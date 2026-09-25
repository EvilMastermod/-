import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { DatabaseSync } from 'node:sqlite';
import worker from './src/worker.js';

const sqlite = new DatabaseSync(':memory:');
sqlite.exec(readFileSync(new URL('./schema.sql', import.meta.url), 'utf8'));
const DB = {
  prepare(query) {
    return { bind(...params) {
      const stmt = sqlite.prepare(query);
      return {
        first: async () => stmt.get(...params) ?? null,
        all: async () => ({ results: stmt.all(...params) }),
        run: async () => {
          const result = stmt.run(...params);
          return { meta: { changes: Number(result.changes), last_row_id: Number(result.lastInsertRowid) } };
        },
      };
    } };
  },
};

const calls = [];
globalThis.fetch = async (url, init) => {
  const method = url.split('/').at(-1);
  const params = JSON.parse(init.body);
  calls.push({ method, params });
  return Response.json({ ok: true, result: method === 'getChatMember' ? { status: 'administrator' } : true });
};
const env = { DB, BOT_TOKEN: 'test-token', WEBHOOK_SECRET: 'test-secret' };
let id = 1;
const webhook = (update, secret = 'test-secret') => worker.fetch(new Request('https://worker.example/webhook', {
  method: 'POST', headers: { 'X-Telegram-Bot-Api-Secret-Token': secret },
  body: JSON.stringify({ update_id: id++, ...update }),
}), env);

assert.equal((await webhook({}, 'incorrect')).status, 403);
const connection = { id: 'connection-1', user: { id: 11 }, user_chat_id: 11,
  is_enabled: true, date: 1, rights: { can_reply: true, can_delete_all_messages: true } };
assert.equal((await webhook({ business_connection: connection })).status, 200);
const owner = { business_connection_id: connection.id, chat: { id: 22, type: 'private' },
  from: { id: 11, first_name: 'Owner' }, message_id: 4, text: '.mute' };
assert.equal((await webhook({ business_message: owner })).status, 200);
assert.equal(calls.filter(c => c.method === 'editMessageText').length, 1);
const incoming = { ...owner, from: { id: 33, first_name: 'Guest' }, message_id: 5, text: 'Hello' };
assert.equal((await webhook({ business_message: incoming })).status, 200);
assert.equal(calls.filter(c => c.method === 'deleteBusinessMessages').length, 1);
assert.equal(calls.filter(c => c.method === 'editMessageText').length, 1);
assert.ok(sqlite.prepare('SELECT 1 FROM business_message_archive WHERE message_id=5').get());
assert.equal((await webhook({ business_message: { ...owner, message_id: 6, text: '.spam 2 Привет' } })).status, 200);
assert.equal(calls.filter(c => c.method === 'sendMessage' && c.params.chat_id === 22).length, 2);
assert.equal((await webhook({ business_message: { ...owner, message_id: 7, text: '.spam 5000 Привет' } })).status, 200);
assert.equal(calls.filter(c => c.method === 'sendMessage' && c.params.chat_id === 22).length, 3);
const group = { chat: { id: -44, type: 'supergroup', title: 'Test' },
  from: { id: 11, first_name: 'Owner' }, message_id: 8, text: '/setup' };
assert.equal((await webhook({ message: group })).status, 200);
assert.equal(calls.filter(c => c.method === 'sendMessage' && c.params.chat_id === -44).length, 1);
assert.equal((await webhook({ message: { ...group, message_id: 9, text: '/badadd грубо' } })).status, 200);
assert.equal(sqlite.prepare('SELECT word FROM bad_words WHERE chat_id=-44').get().word, 'грубо');
const parts = Object.fromEntries(new Intl.DateTimeFormat('en-GB', {
  timeZone: 'Europe/Kyiv', hour: '2-digit', minute: '2-digit', hourCycle: 'h23',
}).formatToParts(new Date()).map(p => [p.type, p.value]));
assert.equal((await webhook({ message: { ...group, message_id: 10,
  text: `/schedule ${parts.hour}:${parts.minute} | Scheduled` } })).status, 200);
await worker.scheduled({}, env);
await worker.scheduled({}, env);
assert.equal(calls.filter(c => c.method === 'sendMessage' && c.params.text === 'Scheduled').length, 1);
console.log('Business webhook smoke checks passed');
