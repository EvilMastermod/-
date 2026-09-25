const now = () => Math.floor(Date.now() / 1000);
const one = (db, sql, ...args) => db.prepare(sql).bind(...args).first();
const all = async (db, sql, ...args) => (await db.prepare(sql).bind(...args).all()).results;
const run = (db, sql, ...args) => db.prepare(sql).bind(...args).run();
const key = (text, data) => ({ text, callback_data: data });
const URL_RE = /(https?:\/\/|t\.me\/|www\.|discord\.gg\/)/i;
const fields = new Set(['welcome_enabled', 'welcome_text', 'anti_spam', 'anti_links',
  'bad_words_enabled', 'warn_limit', 'clean_service', 'rules', 'flood_count',
  'flood_window', 'flood_mute']);

async function chatSettings(env, chat) {
  await run(env.DB, 'INSERT OR IGNORE INTO chats(chat_id) VALUES(?)', chat);
  return one(env.DB, 'SELECT * FROM chats WHERE chat_id=?', chat);
}

async function updateField(env, chat, field, value) {
  if (!fields.has(field)) throw new Error('Invalid chat setting');
  await chatSettings(env, chat);
  await run(env.DB, `UPDATE chats SET ${field}=? WHERE chat_id=?`, value, chat);
}

async function isAdmin(env, api, chat, user) {
  if (!user) return false;
  try {
    const member = await api(env, 'getChatMember', { chat_id: chat, user_id: user });
    return ['administrator', 'creator'].includes(member.status);
  } catch { return false; }
}

async function panel(env, chat) {
  const s = await chatSettings(env, chat);
  const yes = field => s[field] ? '✅' : '❌';
  return { inline_keyboard: [
    [key(`${yes('welcome_enabled')} Приветствие`, 'cfg:welcome'), key(`${yes('anti_spam')} Антиспам`, 'cfg:spam')],
    [key(`${yes('anti_links')} Антиссылки`, 'cfg:links'), key(`${yes('bad_words_enabled')} Фильтр слов`, 'cfg:words')],
    [key('🗯 Автоответы', 'cfg:replies'), key('⏰ Расписание', 'cfg:schedules')],
    [key(`${yes('clean_service')} Чистить сервис`, 'cfg:clean'), key('📋 Правила', 'cfg:rules')],
    [key('⚠️ Лимит предупреждений', 'cfg:warnlimit')],
  ] };
}

async function reply(send, env, msg, text, extras = {}) {
  return send(env, msg.chat.id, text, { reply_parameters: { message_id: msg.message_id }, ...extras });
}

function duration(raw) {
  const m = /^(\d+)([smhd]?)$/i.exec(raw || '10m');
  return m ? Number(m[1]) * ({ '': 60, s: 1, m: 60, h: 3600, d: 86400 }[m[2].toLowerCase()]) : 600;
}

const locked = { can_send_messages: false };
const unlocked = {
  can_send_messages: true, can_send_audios: true, can_send_documents: true,
  can_send_photos: true, can_send_videos: true, can_send_video_notes: true,
  can_send_voice_notes: true, can_send_polls: true, can_send_other_messages: true,
  can_add_web_page_previews: true,
};

export async function handleGroup(env, api, send, msg, updateId) {
  const chat = msg.chat.id, user = msg.from;
  const raw = (msg.text || '').trim();
  const command = /^\/([^\s@]+)(?:@\S+)?(?:\s|$)/.exec(raw)?.[1]?.toLowerCase();
  const arg = command ? raw.slice(raw.indexOf(command) + command.length).replace(/^@\S+/, '').trim() : '';
  if (msg.new_chat_members?.length) {
    const s = await chatSettings(env, chat);
    if (s.welcome_enabled)
      for (const member of msg.new_chat_members.filter(u => !u.is_bot)) {
        const name = [member.first_name, member.last_name].filter(Boolean).join(' ');
        await reply(send, env, msg, s.welcome_text.replaceAll('{name}', name)
          .replaceAll('{chat}', msg.chat.title || 'чат'));
      }
    if (s.clean_service)
      try { await api(env, 'deleteMessage', { chat_id: chat, message_id: msg.message_id }); } catch {}
    return;
  }
  if (command === 'start') return reply(send, env, msg, '🤖 Готов. Админ-панель: /setup');
  if (command === 'rules') {
    const s = await chatSettings(env, chat);
    return reply(send, env, msg, '📋 Правила чата:\n\n' + s.rules);
  }
  const admin = await isAdmin(env, api, chat, user?.id);
  if (command && admin) {
    const s = await chatSettings(env, chat);
    if (command === 'setup')
      return reply(send, env, msg, '🛠 Автоматизация чата\n\nВыберите настройку:',
        { reply_markup: await panel(env, chat) });
    const textField = { setwelcome: ['welcome_text', 1000], setrules: ['rules', 3000] }[command];
    if (textField) {
      if (!arg) return reply(send, env, msg, `Пример: /${command} текст`);
      await updateField(env, chat, textField[0], arg.slice(0, textField[1]));
      return reply(send, env, msg, '✅ Текст сохранён.');
    }
    if (command === 'badadd' || command === 'baddel') {
      if (!arg) return reply(send, env, msg, `Пример: /${command} слово`);
      if (command === 'badadd') await run(env.DB, 'INSERT OR IGNORE INTO bad_words(chat_id,word) VALUES(?,?)', chat, arg.toLowerCase().slice(0, 100));
      else await run(env.DB, 'DELETE FROM bad_words WHERE chat_id=? AND word=?', chat, arg.toLowerCase());
      return reply(send, env, msg, '✅ Фильтр обновлён.');
    }
    if (command === 'badlist') {
      const words = await all(env.DB, 'SELECT word FROM bad_words WHERE chat_id=? ORDER BY word', chat);
      return reply(send, env, msg, `🚫 Запрещённые слова:\n${words.map(r => r.word).join(', ') || 'список пуст'}`);
    }
    if (command === 'replyadd') {
      const [trigger, ...parts] = arg.split('|'), response = parts.join('|').trim();
      if (!trigger?.trim() || !response) return reply(send, env, msg, 'Пример: /replyadd привет | Привет 👋');
      await run(env.DB, 'INSERT INTO auto_replies(chat_id,trigger,reply) VALUES(?,?,?)',
        chat, trigger.trim().toLowerCase().slice(0, 150), response.slice(0, 1000));
      return reply(send, env, msg, '✅ Автоответ добавлен.');
    }
    if (command === 'replydel') {
      if (!/^\d+$/.test(arg)) return reply(send, env, msg, 'Пример: /replydel 4');
      await run(env.DB, 'DELETE FROM auto_replies WHERE chat_id=? AND id=?', chat, Number(arg));
      return reply(send, env, msg, '✅ Автоответ удалён.');
    }
    if (command === 'schedule') {
      const m = /^(\d{1,2}):(\d{2})\s*\|\s*(.+)$/s.exec(arg);
      if (!m || Number(m[1]) > 23 || Number(m[2]) > 59)
        return reply(send, env, msg, 'Пример: /schedule 18:30 | Добрый вечер!');
      const result = await run(env.DB, 'INSERT INTO schedules(chat_id,hh,mm,text) VALUES(?,?,?,?)',
        chat, Number(m[1]), Number(m[2]), m[3].trim().slice(0, 2000));
      return reply(send, env, msg, `✅ Добавлено каждый день в ${m[1].padStart(2, '0')}:${m[2]} (Europe/Kyiv). ID #${result.meta.last_row_id}`);
    }
    if (command === 'scheduledel') {
      if (!/^\d+$/.test(arg)) return reply(send, env, msg, 'Пример: /scheduledel 2');
      await run(env.DB, 'DELETE FROM schedules WHERE chat_id=? AND id=?', chat, Number(arg));
      return reply(send, env, msg, '✅ Расписание удалено.');
    }
    if (command === 'warnlimit') {
      if (!/^\d+$/.test(arg) || Number(arg) < 1 || Number(arg) > 20)
        return reply(send, env, msg, 'Пример: /warnlimit 3');
      await updateField(env, chat, 'warn_limit', Number(arg));
      return reply(send, env, msg, `✅ Лимит предупреждений: ${arg}`);
    }
    const target = msg.reply_to_message?.from;
    if (['warn', 'unwarn', 'mute', 'unmute', 'ban'].includes(command)) {
      if (!target) return reply(send, env, msg, `Ответь /${command} на сообщение пользователя.`);
      if (target.is_bot) return;
      if (['warn', 'mute', 'ban'].includes(command) && await isAdmin(env, api, chat, target.id))
        return reply(send, env, msg, '❌ Нельзя применять к админу.');
      if (command === 'warn') {
        await run(env.DB, `INSERT INTO warnings(chat_id,user_id,count) VALUES(?,?,1)
          ON CONFLICT(chat_id,user_id) DO UPDATE SET count=count+1`, chat, target.id);
        const count = (await one(env.DB, 'SELECT count FROM warnings WHERE chat_id=? AND user_id=?', chat, target.id)).count;
        if (count >= s.warn_limit) {
          try {
            await api(env, 'restrictChatMember', { chat_id: chat, user_id: target.id, permissions: locked });
            await run(env.DB, 'UPDATE warnings SET count=0 WHERE chat_id=? AND user_id=?', chat, target.id);
            return reply(send, env, msg, `🔇 Пользователь получил ${count} предупреждений и был замьючен.`);
          } catch { return reply(send, env, msg, `⚠️ ${count}/${s.warn_limit}. Не смог замьютить — проверь права.`); }
        }
        return reply(send, env, msg, `⚠️ ${count}/${s.warn_limit}`);
      }
      if (command === 'unwarn') {
        await run(env.DB, 'UPDATE warnings SET count=MAX(0,count-1) WHERE chat_id=? AND user_id=?', chat, target.id);
        return reply(send, env, msg, '✅ Одно предупреждение снято.');
      }
      const method = command === 'ban' ? 'banChatMember' : 'restrictChatMember';
      try {
        await api(env, method, { chat_id: chat, user_id: target.id, ...(command === 'ban' ? {}
          : { permissions: command === 'unmute' ? unlocked : locked,
            ...(command === 'mute' ? { until_date: now() + duration(arg.split(/\s+/)[0]) } : {}) }) });
        return reply(send, env, msg, command === 'ban' ? '🚫 Пользователь заблокирован.'
          : command === 'mute' ? '🔇 Мут включён.' : '🔊 Мут снят.');
      } catch { return reply(send, env, msg, '❌ Не получилось. Проверь права бота.'); }
    }
    return;
  }
  if (command && !admin) {
    if (new Set(['setup', 'setwelcome', 'setrules', 'badadd', 'baddel', 'badlist',
      'replyadd', 'replydel', 'schedule', 'scheduledel', 'warnlimit', 'warn', 'unwarn',
      'mute', 'unmute', 'ban']).has(command))
      return reply(send, env, msg, '⛔ Эта команда только для админов чата.');
  }
  if (!user || user.is_bot || admin || command) return;
  const text = (msg.text || msg.caption || '').trim();
  if (!text) return;
  const s = await chatSettings(env, chat);
  let reason = '';
  if (s.anti_spam) {
    await run(env.DB, 'INSERT OR IGNORE INTO flood_events(chat_id,user_id,update_id,at) VALUES(?,?,?,?)',
      chat, user.id, updateId, now());
    await run(env.DB, 'DELETE FROM flood_events WHERE chat_id=? AND user_id=? AND at<?',
      chat, user.id, now() - s.flood_window);
    const count = await one(env.DB, 'SELECT COUNT(*) AS n FROM flood_events WHERE chat_id=? AND user_id=?', chat, user.id);
    if (count.n >= s.flood_count) {
      reason = 'слишком много сообщений подряд';
      await run(env.DB, 'DELETE FROM flood_events WHERE chat_id=? AND user_id=?', chat, user.id);
      try { await api(env, 'restrictChatMember', { chat_id: chat, user_id: user.id,
        permissions: locked, until_date: now() + s.flood_mute }); } catch {}
    }
  }
  if (!reason && s.anti_links && URL_RE.test(text)) reason = 'ссылки запрещены';
  if (!reason && s.bad_words_enabled) {
    const words = await all(env.DB, 'SELECT word FROM bad_words WHERE chat_id=?', chat);
    if (words.some(r => text.toLowerCase().includes(r.word))) reason = 'запрещённое слово';
  }
  if (reason) {
    try { await api(env, 'deleteMessage', { chat_id: chat, message_id: msg.message_id }); } catch {}
    return send(env, chat, `🚫 ${user.first_name || 'Пользователь'}: ${reason}.`);
  }
  const replies = await all(env.DB, 'SELECT trigger,reply FROM auto_replies WHERE chat_id=?', chat);
  const chosen = replies.find(row => text.toLowerCase().includes(row.trigger));
  if (chosen) return reply(send, env, msg, chosen.reply);
}

export async function groupCallback(env, api, send, q) {
  const chat = q.message?.chat?.id;
  const answer = (text, show_alert = false) => api(env, 'answerCallbackQuery',
    { callback_query_id: q.id, ...(text ? { text, show_alert } : {}) });
  if (!chat || !await isAdmin(env, api, chat, q.from?.id)) return answer('⛔ Только для админов.', true);
  const s = await chatSettings(env, chat), action = q.data.slice(4);
  const toggles = { welcome: 'welcome_enabled', spam: 'anti_spam', links: 'anti_links',
    words: 'bad_words_enabled', clean: 'clean_service' };
  if (toggles[action]) {
    await updateField(env, chat, toggles[action], Number(!s[toggles[action]]));
    await answer('Настройка изменена.');
    return api(env, 'editMessageReplyMarkup', { chat_id: chat, message_id: q.message.message_id,
      reply_markup: await panel(env, chat) });
  }
  await answer();
  if (action === 'replies') {
    const rows = await all(env.DB, 'SELECT id,trigger,reply FROM auto_replies WHERE chat_id=? ORDER BY id DESC LIMIT 20', chat);
    return send(env, chat, `🗯 Автоответы\n\n${rows.map(r => `#${r.id} «${r.trigger}» → ${r.reply}`).join('\n') || 'Пока нет.'}\n\n/replyadd слово | ответ\n/replydel ID`);
  }
  if (action === 'schedules') {
    const rows = await all(env.DB, 'SELECT id,hh,mm,text FROM schedules WHERE chat_id=? AND enabled=1 ORDER BY hh,mm', chat);
    return send(env, chat, `⏰ Ежедневные сообщения\n\n${rows.map(r => `#${r.id} ${String(r.hh).padStart(2, '0')}:${String(r.mm).padStart(2, '0')} — ${r.text}`).join('\n') || 'Пока нет.'}\n\nEurope/Kyiv\n/schedule 18:30 | Текст\n/scheduledel ID`);
  }
  if (action === 'rules') return send(env, chat, `📋 Правила чата:\n\n${s.rules}\n\n/setrules текст`);
  if (action === 'warnlimit') return send(env, chat, `⚠️ Сейчас лимит: ${s.warn_limit}\n/warnlimit 3`);
}

export async function scheduled(env, send) {
  const parts = Object.fromEntries(new Intl.DateTimeFormat('en-GB', {
    timeZone: 'Europe/Kyiv', year: 'numeric', month: '2-digit', day: '2-digit',
    hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
  }).formatToParts(new Date()).map(p => [p.type, p.value]));
  const date = `${parts.year}-${parts.month}-${parts.day}`;
  const rows = await all(env.DB, 'SELECT * FROM schedules WHERE enabled=1 AND hh=? AND mm=?',
    Number(parts.hour), Number(parts.minute));
  for (const row of rows) {
    const claim = await run(env.DB, 'INSERT OR IGNORE INTO sent_schedules(schedule_id,date) VALUES(?,?)', row.id, date);
    if (!claim.meta.changes) continue;
    try { await send(env, row.chat_id, row.text); }
    catch (error) {
      await run(env.DB, 'DELETE FROM sent_schedules WHERE schedule_id=? AND date=?', row.id, date);
      console.error('Scheduled send failed:', String(error));
    }
  }
  await run(env.DB, 'DELETE FROM sent_schedules WHERE date<?', date);
  await run(env.DB, 'DELETE FROM processed_updates WHERE received_at<?', now() - 2 * 86400);
  await run(env.DB, 'DELETE FROM flood_events WHERE at<?', now() - 300);
}
