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
