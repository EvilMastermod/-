CREATE TABLE IF NOT EXISTS business_connections (
  connection_id TEXT PRIMARY KEY,
  owner_user_id INTEGER NOT NULL,
  user_chat_id INTEGER NOT NULL,
  is_enabled INTEGER NOT NULL DEFAULT 1,
  can_reply INTEGER NOT NULL DEFAULT 0,
  can_read INTEGER NOT NULL DEFAULT 0,
  can_delete_sent INTEGER NOT NULL DEFAULT 0,
  can_delete_all INTEGER NOT NULL DEFAULT 0,
  established_at INTEGER NOT NULL DEFAULT 0,
  updated_at INTEGER NOT NULL
);
CREATE INDEX IF NOT EXISTS business_owner ON business_connections(owner_user_id, established_at DESC);

CREATE TABLE IF NOT EXISTS business_settings (
  owner_user_id INTEGER PRIMARY KEY,
  automation_enabled INTEGER NOT NULL DEFAULT 1,
  fallback_enabled INTEGER NOT NULL DEFAULT 0,
  fallback_text TEXT NOT NULL DEFAULT '👋 Спасибо за сообщение! Я скоро отвечу.',
  welcome_enabled INTEGER NOT NULL DEFAULT 1,
  welcome_text TEXT NOT NULL DEFAULT '👋 Привет, {name}! Спасибо за сообщение.',
  mark_read INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS business_replies (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  owner_user_id INTEGER NOT NULL,
  trigger TEXT NOT NULL,
  reply TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS business_seen_chats (
  owner_user_id INTEGER NOT NULL,
  chat_id INTEGER NOT NULL,
  first_seen_at INTEGER NOT NULL,
  PRIMARY KEY(owner_user_id, chat_id)
);
CREATE TABLE IF NOT EXISTS business_muted_chats (
  owner_user_id INTEGER NOT NULL,
  chat_id INTEGER NOT NULL,
  muted_at INTEGER NOT NULL,
  PRIMARY KEY(owner_user_id, chat_id)
);
CREATE TABLE IF NOT EXISTS business_mute_controls (
  owner_user_id INTEGER NOT NULL,
  chat_id INTEGER NOT NULL,
  connection_id TEXT NOT NULL,
  message_id INTEGER NOT NULL,
  PRIMARY KEY(owner_user_id, chat_id)
);
CREATE TABLE IF NOT EXISTS business_message_archive (
  connection_id TEXT NOT NULL,
  owner_user_id INTEGER NOT NULL,
  chat_id INTEGER NOT NULL,
  message_id INTEGER NOT NULL,
  sender_user_id INTEGER,
  sender_name TEXT,
  text_content TEXT,
  media_type TEXT,
  file_id TEXT,
  created_at INTEGER NOT NULL,
  PRIMARY KEY(connection_id, chat_id, message_id)
);
CREATE TABLE IF NOT EXISTS processed_updates (
  update_id INTEGER PRIMARY KEY,
  received_at INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS repeat_leases (
  connection_id TEXT NOT NULL,
  chat_id INTEGER NOT NULL,
  expires_at INTEGER NOT NULL,
  PRIMARY KEY(connection_id, chat_id)
);
CREATE TABLE IF NOT EXISTS chats (
  chat_id INTEGER PRIMARY KEY,
  welcome_enabled INTEGER NOT NULL DEFAULT 1,
  welcome_text TEXT NOT NULL DEFAULT '👋 Добро пожаловать, {name}!',
  anti_spam INTEGER NOT NULL DEFAULT 1,
  anti_links INTEGER NOT NULL DEFAULT 0,
  bad_words_enabled INTEGER NOT NULL DEFAULT 1,
  warn_limit INTEGER NOT NULL DEFAULT 3,
  clean_service INTEGER NOT NULL DEFAULT 0,
  rules TEXT NOT NULL DEFAULT 'Правила пока не настроены.',
  flood_count INTEGER NOT NULL DEFAULT 6,
  flood_window INTEGER NOT NULL DEFAULT 10,
  flood_mute INTEGER NOT NULL DEFAULT 60
);
CREATE TABLE IF NOT EXISTS bad_words (
  chat_id INTEGER NOT NULL,
  word TEXT NOT NULL,
  PRIMARY KEY(chat_id, word)
);
CREATE TABLE IF NOT EXISTS auto_replies (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  chat_id INTEGER NOT NULL,
  trigger TEXT NOT NULL,
  reply TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS warnings (
  chat_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  count INTEGER NOT NULL DEFAULT 0,
  PRIMARY KEY(chat_id, user_id)
);
CREATE TABLE IF NOT EXISTS schedules (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  chat_id INTEGER NOT NULL,
  hh INTEGER NOT NULL,
  mm INTEGER NOT NULL,
  text TEXT NOT NULL,
  enabled INTEGER NOT NULL DEFAULT 1
);
CREATE TABLE IF NOT EXISTS sent_schedules (
  schedule_id INTEGER NOT NULL,
  date TEXT NOT NULL,
  PRIMARY KEY(schedule_id, date)
);
CREATE TABLE IF NOT EXISTS flood_events (
  chat_id INTEGER NOT NULL,
  user_id INTEGER NOT NULL,
  update_id INTEGER NOT NULL,
  at INTEGER NOT NULL,
  PRIMARY KEY(chat_id, user_id, update_id)
);
CREATE INDEX IF NOT EXISTS flood_window_idx ON flood_events(chat_id, user_id, at);
