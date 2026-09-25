// Telegram webhook version of the Business features in ../chat-automator-bot/bot.py.
// D1 persists state; Railway continues to serve the existing bot until cutover.
const now = () => Math.floor(Date.now() / 1000);
const one = (db, sql, ...args) => db.prepare(sql).bind(...args).first();
const all = async (db, sql, ...args) => (await db.prepare(sql).bind(...args).all()).results;
const run = (db, sql, ...args) => db.prepare(sql).bind(...args).run();
const keyboard = rows => ({ inline_keyboard: rows });
const button = (label, data) => ({ text: label, callback_data: data });

async function api(env, method, payload = {}) {
  const response = await fetch(`https://api.telegram.org/bot${env.BOT_TOKEN}/${method}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  const result = await response.json();
  if (!result.ok) throw new Error(`Telegram ${method}: ${result.description || response.status}`);
  return result.result;
}

function send(env, chat_id, text, extras = {}) {
  return api(env, 'sendMessage', { chat_id, text, ...extras });
}

async function getConnection(env, id) {
  let row = await one(env.DB, 'SELECT * FROM business_connections WHERE connection_id=?', id);
  if (row) return row;
  const connection = await api(env, 'getBusinessConnection', { business_connection_id: id });
  await saveConnection(env, connection);
  return one(env.DB, 'SELECT * FROM business_connections WHERE connection_id=?', id);
}

async function saveConnection(env, connection) {
  const rights = connection.rights || {};
  await run(env.DB, `INSERT INTO business_connections
    (connection_id,owner_user_id,user_chat_id,is_enabled,can_reply,can_read,
     can_delete_sent,can_delete_all,established_at,updated_at)
    VALUES(?,?,?,?,?,?,?,?,?,?) ON CONFLICT(connection_id) DO UPDATE SET
    owner_user_id=excluded.owner_user_id,user_chat_id=excluded.user_chat_id,
    is_enabled=excluded.is_enabled,can_reply=excluded.can_reply,can_read=excluded.can_read,
    can_delete_sent=excluded.can_delete_sent,can_delete_all=excluded.can_delete_all,
    established_at=excluded.established_at,updated_at=excluded.updated_at`,
    connection.id, connection.user.id, connection.user_chat_id, Number(!!connection.is_enabled),
    Number(!!rights.can_reply), Number(!!rights.can_read_messages),
    Number(!!rights.can_delete_sent_messages), Number(!!rights.can_delete_all_messages),
    connection.date || 0, now());
  await settings(env, connection.user.id);
}

async function settings(env, owner) {
  await run(env.DB, 'INSERT OR IGNORE INTO business_settings(owner_user_id) VALUES(?)', owner);
  return one(env.DB, 'SELECT * FROM business_settings WHERE owner_user_id=?', owner);
}

const ownerConnection = (env, owner) => one(env.DB,
  'SELECT * FROM business_connections WHERE owner_user_id=? AND is_enabled=1 ORDER BY established_at DESC,updated_at DESC LIMIT 1', owner);

async function panel(env, owner) {
  const s = await settings(env, owner);
  const c = await ownerConnection(env, owner);
  const yes = v => v ? '✅' : '❌';
  return keyboard([
    [button(`${yes(c)} Подключение Telegram Business`, 'biz:status')],
    [button(`${yes(s.automation_enabled)} Автоматизация`, 'biz:automation'), button(`${yes(s.fallback_enabled)} Общий автоответ`, 'biz:fallback')],
    [button(`${yes(s.welcome_enabled)} Первое сообщение`, 'biz:welcome'), button(`${yes(s.mark_read)} Читать сообщения`, 'biz:read')],
    [button('🗯 Ответы по словам', 'biz:replies'), button('📝 Тексты автоответов', 'biz:texts')],
  ]);
}

async function handleOwnerCommand(env, msg, connection) {
  const owner = connection.owner_user_id, chat = msg.chat.id, id = msg.business_connection_id;
  const text = (msg.text || msg.caption || '').trim(), low = text.toLowerCase();
  const reply = body => send(env, chat, body, { business_connection_id: id });
  if (low === '.mute') {
    await run(env.DB, `INSERT INTO business_muted_chats(owner_user_id,chat_id,muted_at) VALUES(?,?,?)
      ON CONFLICT(owner_user_id,chat_id) DO UPDATE SET muted_at=excluded.muted_at`, owner, chat, now());
    await run(env.DB, `INSERT INTO business_mute_controls(owner_user_id,chat_id,connection_id,message_id)
      VALUES(?,?,?,?) ON CONFLICT(owner_user_id,chat_id) DO UPDATE SET
      connection_id=excluded.connection_id,message_id=excluded.message_id`, owner, chat, id, msg.message_id);
    try {
      await api(env, 'editMessageText', { chat_id: chat, message_id: msg.message_id,
        business_connection_id: id, text: '🔇 Молчать',
        reply_markup: keyboard([[button('🔊 Говори', `bizchat:unmute:${owner}:${chat}`)]]) });
    } catch (error) { console.warn('Cannot edit mute control:', String(error)); }
    return;
  }
  if (low === '.unmute') {
    await run(env.DB, 'DELETE FROM business_muted_chats WHERE owner_user_id=? AND chat_id=?', owner, chat);
    await run(env.DB, 'DELETE FROM business_mute_controls WHERE owner_user_id=? AND chat_id=?', owner, chat);
    try {
      await api(env, 'editMessageText', { chat_id: chat, message_id: msg.message_id,
        business_connection_id: id, text: '🔊 Говорить',
        reply_markup: keyboard([[button('🔇 Молчать', `bizchat:mute:${owner}:${chat}`)]]) });
    } catch (error) { console.warn('Cannot edit unmute control:', String(error)); }
    return;
  }
  if (low.startsWith('.spam')) {
    const match = /^\.spam\s+(\d+)\s+([\s\S]+)$/i.exec(text);
    if (!match || Number(match[1]) < 1 || Number(match[1]) > 10 || !match[2].trim()) {
      await reply('Формат: .spam 5 Привет (от 1 до 10 раз)');
      return;
    }
    // A D1 lease prevents overlapping batches even across Worker isolates.
    const lease = await run(env.DB, `INSERT OR IGNORE INTO repeat_leases(connection_id,chat_id,expires_at)
      VALUES(?,?,?)`, id, chat, now() + 35);
    if (!lease.meta.changes) {
      const old = await one(env.DB, 'SELECT expires_at FROM repeat_leases WHERE connection_id=? AND chat_id=?', id, chat);
      const claim = old?.expires_at < now() && await run(env.DB,
        'UPDATE repeat_leases SET expires_at=? WHERE connection_id=? AND chat_id=? AND expires_at<?',
        now() + 35, id, chat, now());
      if (!claim?.meta.changes) { await reply('Предыдущая отправка ещё идёт.'); return; }
    }
    try {
      for (let index = 0; index < Number(match[1]); index++) {
        await reply(match[2].trim().slice(0, 4096));
        if (index + 1 < Number(match[1])) await new Promise(r => setTimeout(r, 800));
      }
    } finally {
      await run(env.DB, 'DELETE FROM repeat_leases WHERE connection_id=? AND chat_id=?', id, chat);
    }
  }
}

async function archive(env, msg, connection) {
  const media = ['photo', 'video', 'document', 'voice', 'audio', 'animation', 'sticker', 'video_note']
    .find(key => msg[key]);
  const value = media === 'photo' ? msg.photo.at(-1) : media && msg[media];
  const sender = msg.from || {};
  await run(env.DB, `INSERT OR REPLACE INTO business_message_archive
    (connection_id,owner_user_id,chat_id,message_id,sender_user_id,sender_name,text_content,
     media_type,file_id,created_at) VALUES(?,?,?,?,?,?,?,?,?,?)`,
    connection.connection_id, connection.owner_user_id, msg.chat.id, msg.message_id,
    sender.id ?? null, [sender.first_name, sender.last_name].filter(Boolean).join(' ') || null,
    (msg.text || msg.caption || value?.file_name || value?.emoji || '').trim(),
    media || null, value?.file_id || null, now());
}

async function handleBusinessMessage(env, msg) {
  const connection = await getConnection(env, msg.business_connection_id);
  if (!connection || !connection.is_enabled) return;
  const owner = connection.owner_user_id, chat = msg.chat.id;
  if (msg.from?.id === owner) return handleOwnerCommand(env, msg, connection);
  if (msg.sender_business_bot) return;
  await archive(env, msg, connection);
  if (await one(env.DB, 'SELECT 1 FROM business_muted_chats WHERE owner_user_id=? AND chat_id=?', owner, chat)) {
    await api(env, 'deleteBusinessMessages', { business_connection_id: connection.connection_id, message_ids: [msg.message_id] });
    return;
  }
  const s = await settings(env, owner);
  if (!s.automation_enabled) return;
  if (s.mark_read) {
    try { await api(env, 'readBusinessMessage', { business_connection_id: connection.connection_id, chat_id: chat, message_id: msg.message_id }); }
    catch (error) { console.warn('Business read failed:', String(error)); }
  }
  const text = (msg.text || msg.caption || '').trim(), low = text.toLowerCase();
  const replies = await all(env.DB,
    'SELECT trigger,reply FROM business_replies WHERE owner_user_id=? ORDER BY LENGTH(trigger) DESC,id ASC', owner);
  let chosen = text ? replies.find(row => low.includes(row.trigger.toLowerCase()))?.reply : null;
  const seen = await run(env.DB, `INSERT OR IGNORE INTO business_seen_chats(owner_user_id,chat_id,first_seen_at)
    VALUES(?,?,?)`, owner, chat, now());
  if (!chosen && seen.meta.changes && s.welcome_enabled) chosen = s.welcome_text;
  else if (!chosen && s.fallback_enabled) chosen = s.fallback_text;
  if (chosen) {
    const name = [msg.from?.first_name, msg.from?.last_name].filter(Boolean).join(' ') || 'друг';
    await send(env, chat, chosen.replaceAll('{name}', name).replaceAll('{username}', msg.from?.username ? `@${msg.from.username}` : ''),
      { business_connection_id: connection.connection_id });
  }
}

async function handleDeleted(env, deleted) {
  const connection = await getConnection(env, deleted.business_connection_id);
  if (!connection) return;
  for (const id of deleted.message_ids) {
    const row = await one(env.DB, `SELECT * FROM business_message_archive
      WHERE connection_id=? AND chat_id=? AND message_id=?`, connection.connection_id, deleted.chat.id, id);
    if (!row || row.sender_user_id === connection.owner_user_id) continue;
    const header = `🗑 Удалено сообщение\n👤 ${row.sender_name || `ID ${row.sender_user_id || '?'}`}\n💬 Chat ID: ${row.chat_id}\n🆔 Message ID: ${id}\n`;
    const body = `${header}\n📝 ${row.text_content || '[без текста]'}`;
    const method = { photo: 'sendPhoto', video: 'sendVideo', document: 'sendDocument',
      voice: 'sendVoice', audio: 'sendAudio', animation: 'sendAnimation', video_note: 'sendVideoNote' }[row.media_type];
    if (method && row.file_id) {
      const field = { sendPhoto: 'photo', sendVideo: 'video', sendDocument: 'document',
        sendVoice: 'voice', sendAudio: 'audio', sendAnimation: 'animation', sendVideoNote: 'video_note' }[method];
      if (method === 'sendVideoNote') await send(env, connection.user_chat_id, body.slice(0, 4000));
      await api(env, method, { chat_id: connection.user_chat_id, [field]: row.file_id,
        ...(method === 'sendVideoNote' ? {} : { caption: body.slice(0, 1024) }) });
    } else {
      await send(env, connection.user_chat_id, body.slice(0, 4000));
      if (row.media_type === 'sticker' && row.file_id)
        await api(env, 'sendSticker', { chat_id: connection.user_chat_id, sticker: row.file_id });
    }
    await run(env.DB, 'DELETE FROM business_message_archive WHERE connection_id=? AND chat_id=? AND message_id=?',
      connection.connection_id, deleted.chat.id, id);
  }
}

async function callback(env, q) {
  const data = q.data || '', owner = q.from.id, chat = q.message?.chat?.id;
  const answer = (text, show_alert = false) => api(env, 'answerCallbackQuery', { callback_query_id: q.id, ...(text ? { text, show_alert } : {}) });
  if (data.startsWith('bizchat:')) {
    const [, action, ownerId, chatId] = data.split(':');
    if (Number(ownerId) !== owner || Number(chatId) !== chat || !q.message?.business_connection_id)
      return answer('⛔ Кнопка недоступна.', true);
    const id = q.message.business_connection_id;
    if (action === 'mute') {
      const connection = await getConnection(env, id);
      if (!connection?.can_delete_all) return answer('❌ Нужно право удалять входящие.', true);
      await run(env.DB, `INSERT INTO business_muted_chats(owner_user_id,chat_id,muted_at) VALUES(?,?,?)
        ON CONFLICT(owner_user_id,chat_id) DO UPDATE SET muted_at=excluded.muted_at`, owner, chat, now());
    } else if (action === 'unmute') {
      await run(env.DB, 'DELETE FROM business_muted_chats WHERE owner_user_id=? AND chat_id=?', owner, chat);
      await run(env.DB, 'DELETE FROM business_mute_controls WHERE owner_user_id=? AND chat_id=?', owner, chat);
    } else return answer();
    await answer(action === 'mute' ? '🔇 Молчать' : '🔊 Говорить');
    return api(env, 'editMessageText', { chat_id: chat, message_id: q.message.message_id,
      business_connection_id: id, text: action === 'mute' ? '🔇 Молчать' : '🔊 Говорить',
      reply_markup: keyboard([[button(action === 'mute' ? '🔊 Говори' : '🔇 Молчать',
        `bizchat:${action === 'mute' ? 'unmute' : 'mute'}:${owner}:${chat}`)]]) });
  }
  if (!data.startsWith('biz:') || chat !== owner) return answer();
  const action = data.slice(4), s = await settings(env, owner);
  const fields = { automation: 'automation_enabled', fallback: 'fallback_enabled',
    welcome: 'welcome_enabled', read: 'mark_read' };
  if (fields[action]) {
    const field = fields[action];
    await run(env.DB, `UPDATE business_settings SET ${field}=? WHERE owner_user_id=?`, Number(!s[field]), owner);
    await answer('Настройка изменена.');
    return api(env, 'editMessageReplyMarkup', { chat_id: chat, message_id: q.message.message_id,
      reply_markup: await panel(env, owner) });
  }
  await answer();
  if (action === 'status') {
    const c = await ownerConnection(env, owner);
    const text = c ? `✅ Telegram Business подключён.\n\n💬 Ответы/редактирование: ${c.can_reply ? '✅' : '❌'}\n🗑 Удаление входящих: ${c.can_delete_all ? '✅' : '❌'}\n🧹 Удаление исходящих бота: ${c.can_delete_sent ? '✅' : '❌'}\n\nПоследнее обновление прав от Telegram: ${now() - c.updated_at} сек. назад.`
      : '❌ Бот пока не получил Business-подключение.';
    return send(env, owner, text);
  }
  if (action === 'replies') {
    const rows = await all(env.DB,
      'SELECT id,trigger,reply FROM business_replies WHERE owner_user_id=? ORDER BY id DESC LIMIT 30', owner);
    return send(env, owner, `🗯 Ответы по словам\n\n${rows.map(r => `#${r.id} «${r.trigger}» → ${r.reply}`).join('\n') || 'Пока нет.'}\n\nДобавить: /bizreplyadd привет | Привет!\nУдалить: /bizreplydel ID`);
  }
  if (action === 'texts')
    return send(env, owner, `📝 Тексты Business-автоответов\n\nПервое сообщение:\n${s.welcome_text}\n\nОбщий автоответ:\n${s.fallback_text}\n\nИзменить: /bizwelcome текст или /bizfallback текст`);
}

async function privateCommand(env, msg) {
  if (msg.chat.type !== 'private' || msg.from?.id !== msg.chat.id) return;
  const text = msg.text || '', [name] = text.split(/\s+/, 1), raw = text.slice(name.length).trim();
  const command = name.split('@')[0].toLowerCase(), owner = msg.from.id;
  if (command === '/start') return send(env, owner, '🤖 Я RNMD Chat Automator.\n\nНастройки Business: /business');
  if (command === '/business') {
    const c = await ownerConnection(env, owner);
    return send(env, owner, `💼 Автоматизация личных чатов\n\nTelegram Business: ${c ? '✅ подключён' : '❌ ещё не подключён'}\n\n.mute — удалять новые входящие\n.unmute — снять мут\n.spam 5 Привет — повторить до 10 раз`,
      { reply_markup: await panel(env, owner) });
  }
  if (command === '/bizwelcome' || command === '/bizfallback') {
    if (!raw) return send(env, owner, `Пример: ${command} Привет, {name}!`);
    const field = command === '/bizwelcome' ? 'welcome_text' : 'fallback_text';
    await settings(env, owner);
    await run(env.DB, `UPDATE business_settings SET ${field}=? WHERE owner_user_id=?`, raw.slice(0, 2000), owner);
    return send(env, owner, '✅ Текст сохранён.');
  }
  if (command === '/bizreplyadd') {
    const i = raw.indexOf('|');
    if (i < 1 || !raw.slice(i + 1).trim()) return send(env, owner, 'Пример: /bizreplyadd привет | Привет!');
    await run(env.DB, 'INSERT INTO business_replies(owner_user_id,trigger,reply) VALUES(?,?,?)',
      owner, raw.slice(0, i).trim().toLowerCase().slice(0, 150), raw.slice(i + 1).trim().slice(0, 2000));
    return send(env, owner, '✅ Business-автоответ добавлен.');
  }
  if (command === '/bizreplydel') {
    if (!/^\d+$/.test(raw)) return send(env, owner, 'Пример: /bizreplydel 3');
    await run(env.DB, 'DELETE FROM business_replies WHERE owner_user_id=? AND id=?', owner, Number(raw));
    return send(env, owner, '✅ Business-автоответ удалён.');
  }
}

async function dispatch(env, update) {
  if (update.business_connection) {
    const c = update.business_connection;
    await saveConnection(env, c);
    return send(env, c.user_chat_id, c.is_enabled
      ? '✅ Telegram Business подключён к RNMD Chat Automator.'
      : '⚠️ Telegram Business отключён от RNMD Chat Automator.');
  }
  if (update.business_message) return handleBusinessMessage(env, update.business_message);
  if (update.deleted_business_messages) return handleDeleted(env, update.deleted_business_messages);
  if (update.callback_query) return callback(env, update.callback_query);
  if (update.message) return privateCommand(env, update.message);
}

export default {
  async fetch(request, env) {
    if (new URL(request.url).pathname !== '/webhook') return new Response('RNMD bot', { status: 200 });
    if (request.method !== 'POST') return new Response('Method not allowed', { status: 405 });
    if (!env.BOT_TOKEN || !env.WEBHOOK_SECRET || !env.DB) return new Response('Not configured', { status: 503 });
    if (request.headers.get('X-Telegram-Bot-Api-Secret-Token') !== env.WEBHOOK_SECRET)
      return new Response('Forbidden', { status: 403 });
    let update;
    try { update = await request.json(); } catch { return new Response('Bad JSON', { status: 400 }); }
    if (!Number.isInteger(update.update_id)) return new Response('Bad update', { status: 400 });
    // Telegram may retry a webhook update. Never repeat sends/deletes on a retry.
    const claim = await run(env.DB, 'INSERT OR IGNORE INTO processed_updates(update_id,received_at) VALUES(?,?)',
      update.update_id, now());
    if (!claim.meta.changes) return new Response('OK');
    try {
      await dispatch(env, update);
      return new Response('OK');
    } catch (error) {
      await run(env.DB, 'DELETE FROM processed_updates WHERE update_id=?', update.update_id);
      console.error('Telegram webhook failed:', String(error));
      return new Response('Retry', { status: 500 });
    }
  },
};
