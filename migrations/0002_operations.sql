-- Additive operational tables. No account or payment activation.
CREATE TABLE IF NOT EXISTS support_requests (
 id TEXT PRIMARY KEY, category TEXT NOT NULL, email TEXT NOT NULL,
 record_reference TEXT NOT NULL DEFAULT '', message TEXT NOT NULL,
 status TEXT NOT NULL DEFAULT 'open' CHECK(status IN ('open','investigating','resolved')),
 created_at INTEGER NOT NULL DEFAULT(unixepoch()), updated_at INTEGER NOT NULL DEFAULT(unixepoch())
);
CREATE INDEX IF NOT EXISTS support_requests_status ON support_requests(status,created_at);
CREATE TABLE IF NOT EXISTS email_events (
 id TEXT PRIMARY KEY, delivery_id TEXT NOT NULL REFERENCES deliveries(id) ON DELETE CASCADE,
 event_type TEXT NOT NULL, created_at INTEGER NOT NULL DEFAULT(unixepoch())
);
CREATE TABLE IF NOT EXISTS email_suppressions (
 email_hash TEXT PRIMARY KEY, reason TEXT NOT NULL, created_at INTEGER NOT NULL DEFAULT(unixepoch())
);
CREATE TABLE IF NOT EXISTS operator_checks (
 id TEXT PRIMARY KEY, state TEXT NOT NULL, detail TEXT NOT NULL, checked_at INTEGER NOT NULL DEFAULT(unixepoch())
);
