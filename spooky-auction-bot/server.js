const express = require('express');
const mineflayer = require('mineflayer');

const PORT = Number(process.env.PORT || 3000);
const MC_HOST = process.env.MC_HOST || 'spookytime.net';
const MC_PORT = Number(process.env.MC_PORT || 25565);
const MC_USERNAME = process.env.MC_USERNAME || 'RNMDPriceBot';
const MC_PASSWORD = process.env.MC_SERVER_PASSWORD || '';
const MC_VERSION = process.env.MC_VERSION || undefined;
const API_KEY = process.env.PRICE_API_KEY || '';

const app = express();
app.use(express.json({ limit: '64kb' }));

let bot = null;
let ready = false;
let reconnectTimer = null;
let reconnectDelayMs = 5000;
let lastConnectionError = '';
let lastAuthSend = 0;
let queue = Promise.resolve();

const allowedAuction = /^\/an(?:10[1-8]|20[1-9]|30[1-9])$/i;

function stripMinecraft(text) {
  return String(text ?? '')
    .replace(/§[0-9A-FK-OR]/gi, '')
    .replace(/[\u00A0]/g, ' ')
    .trim();
}

function normalize(text) {
  return stripMinecraft(text).toLowerCase().replace(/\s+/g, ' ').trim();
}

function collectPrimitiveStrings(value, out = []) {
  if (value == null) return out;
  if (typeof value === 'string' || typeof value === 'number') {
    out.push(stripMinecraft(value));
    return out;
  }
  if (Array.isArray(value)) {
    for (const v of value) collectPrimitiveStrings(v, out);
    return out;
  }
  if (typeof value === 'object') {
    if (Object.prototype.hasOwnProperty.call(value, 'value')) {
      collectPrimitiveStrings(value.value, out);
    } else {
      for (const v of Object.values(value)) collectPrimitiveStrings(v, out);
    }
  }
  return out;
}

function itemTextLines(item) {
  const lines = [];
  if (item?.displayName) lines.push(stripMinecraft(item.displayName));
  if (item?.name) lines.push(stripMinecraft(item.name));
  if (item?.customName) lines.push(stripMinecraft(item.customName));

  try {
    if (item?.nbt) collectPrimitiveStrings(item.nbt, lines);
  } catch (_) {}

  try {
    if (item?.components) collectPrimitiveStrings(item.components, lines);
  } catch (_) {}

  return [...new Set(lines.map(stripMinecraft).filter(Boolean))];
}

function parseNumericToken(raw, suffix = '') {
  let s = String(raw).replace(/\s+/g, '').trim();
  if (!s) return null;

  const commas = (s.match(/,/g) || []).length;
  const dots = (s.match(/\./g) || []).length;

  if (commas + dots > 1 || /[.,]\d{3}(?:[.,]\d{3})*$/.test(s)) {
    s = s.replace(/[.,]/g, '');
  } else {
    s = s.replace(',', '.');
  }

  const num = Number(s);
  if (!Number.isFinite(num)) return null;

  const sf = String(suffix || '').toLowerCase();
  let mult = 1;
  if (['к', 'k', 'тыс'].includes(sf)) mult = 1000;
  if (['м', 'm', 'млн'].includes(sf)) mult = 1000000;

  const result = Math.round(num * mult);
  return result > 0 ? result : null;
}

function extractPrice(lines) {
  const strong = lines.filter(line =>
    /(?:цена|стоим|price|монет|коин|\$|₽)/i.test(line)
  );

  const candidates = strong.length ? strong : [];

  for (const line of candidates) {
    const matches = [...line.matchAll(/(\d[\d\s.,]*)(?:\s*)(к|k|тыс|м|m|млн)?/gi)];
    const nums = matches
      .map(m => parseNumericToken(m[1], m[2]))
      .filter(n => Number.isFinite(n) && n > 0);
    if (nums.length) return Math.max(...nums);
  }

  return null;
}

function wait(ms) {
  return new Promise(resolve => setTimeout(resolve, ms));
}

function waitForWindow(timeoutMs = 7000) {
  return new Promise((resolve, reject) => {
    const timer = setTimeout(() => {
      cleanup();
      reject(new Error('Auction window did not open in time'));
    }, timeoutMs);

    const handler = window => {
      cleanup();
      resolve(window);
    };

    function cleanup() {
      clearTimeout(timer);
      if (bot) bot.removeListener('windowOpen', handler);
    }

    bot.once('windowOpen', handler);
  });
}

function scheduleReconnect() {
  if (reconnectTimer) return;
  ready = false;
  reconnectTimer = setTimeout(() => {
    reconnectTimer = null;
    connect();
  }, reconnectDelayMs);
}

function maybeAuthenticate(message) {
  if (!MC_PASSWORD || !bot) return;
  const now = Date.now();
  if (now - lastAuthSend < 5000) return;

  const text = normalize(message);

  if (/\/(?:reg|register)|зарегистр/.test(text)) {
    lastAuthSend = now;
    bot.chat('/reg ' + MC_PASSWORD + ' ' + MC_PASSWORD);
  } else if (/\/login|авториз|войдите|войти/.test(text)) {
    lastAuthSend = now;
    bot.chat('/login ' + MC_PASSWORD);
  }
}

function connect() {
  try {
    const opts = {
      host: MC_HOST,
      port: MC_PORT,
      username: MC_USERNAME,
      auth: 'offline'
    };
    if (MC_VERSION) opts.version = MC_VERSION;

    bot = mineflayer.createBot(opts);

    bot.on('spawn', () => {
      ready = true;
      reconnectDelayMs = 5000;
      lastConnectionError = '';
      console.log('[MC] Spawned as', MC_USERNAME, 'on', MC_HOST + ':' + MC_PORT);
      if (MC_PASSWORD) {
        setTimeout(() => {
          try { bot.chat('/login ' + MC_PASSWORD); } catch (_) {}
        }, 1500);
      }
    });

    bot.on('messagestr', maybeAuthenticate);
    bot.on('message', msg => maybeAuthenticate(msg?.toString?.() || msg));

    bot.on('kicked', reason => {
      const rawReason = String(reason);
      console.error('[MC] Kicked:', rawReason);
      ready = false;

      let readable = stripMinecraft(rawReason);
      try {
        const parsed = JSON.parse(rawReason);
        if (parsed && parsed.text) readable = stripMinecraft(parsed.text);
      } catch (_) {}

      if (/возможно вы бот|провалили проверку/i.test(readable)) {
        lastConnectionError = 'Spooky Time отклонил автоматический вход: вы провалили антибот-проверку.';
        reconnectDelayMs = 5 * 60 * 1000;
      } else {
        lastConnectionError = readable || 'Spooky Time разорвал соединение.';
        reconnectDelayMs = 30000;
      }
    });

    bot.on('error', err => {
      const message = err?.message || String(err);
      console.error('[MC] Error:', message);
      ready = false;
      lastConnectionError = message;
    });

    bot.on('end', () => {
      console.log('[MC] Disconnected');
      ready = false;
      scheduleReconnect();
    });
  } catch (err) {
    const message = err?.message || String(err);
    console.error('[MC] Connect failed:', message);
    lastConnectionError = message;
    scheduleReconnect();
  }
}

async function inspectAuction(itemQuery, auctionCommand) {
  if (!ready || !bot) {
    throw new Error(
      lastConnectionError || 'Minecraft-бот сейчас не подключён к Spooky Time.'
    );
  }

  if (!allowedAuction.test(auctionCommand)) {
    throw new Error('Unsupported auction command');
  }

  const queryNorm = normalize(itemQuery);
  if (!queryNorm) throw new Error('Item name is empty');

  try {
    if (bot.currentWindow) bot.closeWindow(bot.currentWindow);
  } catch (_) {}

  // Сначала переходим на нужную анку (/an101 ... /an309).
  bot.chat(auctionCommand);
  await wait(4000);

  // После перехода открываем аукцион и читаем видимые лоты.
  try {
    if (bot.currentWindow) bot.closeWindow(bot.currentWindow);
  } catch (_) {}

  await wait(300);
  const windowPromise = waitForWindow(8000);
  bot.chat('/ah');
  const window = await windowPromise;
  await wait(900);

  const prices = [];
  const matches = [];

  for (const item of window.slots || []) {
    if (!item) continue;

    const lines = itemTextLines(item);
    const haystack = normalize(lines.join(' '));

    if (!haystack.includes(queryNorm)) continue;

    const price = extractPrice(lines);
    if (!price) continue;

    prices.push(price);
    matches.push({
      name: stripMinecraft(item.displayName || item.name || 'item'),
      price
    });
  }

  try {
    if (bot.currentWindow) bot.closeWindow(bot.currentWindow);
  } catch (_) {}

  if (!prices.length) {
    return {
      ok: true,
      item: itemQuery,
      auction: auctionCommand,
      count: 0,
      prices: [],
      average: null,
      min: null,
      max: null
    };
  }

  const total = prices.reduce((a, b) => a + b, 0);
  const average = Math.round(total / prices.length);

  return {
    ok: true,
    item: itemQuery,
    auction: auctionCommand,
    count: prices.length,
    prices,
    average,
    min: Math.min(...prices),
    max: Math.max(...prices),
    matches
  };
}

function enqueue(task) {
  const result = queue.then(task, task);
  queue = result.catch(() => {});
  return result;
}

function requireKey(req, res, next) {
  if (!API_KEY) return next();
  if (req.get('x-api-key') !== API_KEY) {
    return res.status(401).json({ ok: false, error: 'unauthorized' });
  }
  next();
}

app.get('/health', (_req, res) => {
  res.json({
    ok: true,
    minecraftConnected: ready,
    host: MC_HOST,
    username: MC_USERNAME,
    error: ready ? null : (lastConnectionError || null)
  });
});

app.post('/price', requireKey, async (req, res) => {
  const item = String(req.body?.item || '').trim();
  const auction = String(req.body?.auction || '').trim().toLowerCase();

  if (!item || !auction) {
    return res.status(400).json({ ok: false, error: 'item and auction are required' });
  }

  if (!allowedAuction.test(auction)) {
    return res.status(400).json({
      ok: false,
      error: 'allowed auctions: /an101-/an108, /an201-/an209, /an301-/an309'
    });
  }

  try {
    const data = await enqueue(() => inspectAuction(item, auction));
    res.json(data);
  } catch (err) {
    console.error('[PRICE]', err?.stack || err);
    res.status(503).json({ ok: false, error: err?.message || 'price lookup failed' });
  }
});

app.listen(PORT, '0.0.0.0', () => {
  console.log('[HTTP] listening on', PORT);
  connect();
});
