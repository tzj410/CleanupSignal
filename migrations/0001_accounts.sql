PRAGMA foreign_keys=ON;
CREATE TABLE IF NOT EXISTS companies (
 id TEXT PRIMARY KEY, name TEXT NOT NULL CHECK(length(name) BETWEEN 2 AND 160),
 owner_id TEXT NOT NULL UNIQUE, plan TEXT NOT NULL DEFAULT 'free' CHECK(plan IN ('free','starter','team','business')),
 subscription_status TEXT NOT NULL DEFAULT 'inactive', stripe_customer TEXT UNIQUE, stripe_subscription TEXT UNIQUE,
 period_end INTEGER NOT NULL DEFAULT 0, billing_event_created INTEGER NOT NULL DEFAULT 0,
 created_at INTEGER NOT NULL DEFAULT (unixepoch())
);
CREATE TABLE IF NOT EXISTS members (
 user_id TEXT PRIMARY KEY, company_id TEXT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
 email TEXT NOT NULL COLLATE NOCASE, role TEXT NOT NULL CHECK(role IN ('owner','member')),
 created_at INTEGER NOT NULL DEFAULT (unixepoch()), UNIQUE(company_id,email)
);
CREATE INDEX IF NOT EXISTS members_company ON members(company_id);
CREATE TABLE IF NOT EXISTS invitations (
 token_hash TEXT PRIMARY KEY, company_id TEXT NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
 email TEXT NOT NULL COLLATE NOCASE, expires_at INTEGER NOT NULL, created_at INTEGER NOT NULL DEFAULT(unixepoch()),
 UNIQUE(company_id,email)
);
CREATE TRIGGER IF NOT EXISTS member_seats BEFORE INSERT ON members
WHEN (SELECT count(*) FROM members WHERE company_id=NEW.company_id) >=
 (SELECT CASE WHEN subscription_status IN ('active','trialing') AND period_end>unixepoch() THEN
 CASE plan WHEN 'business' THEN 8 WHEN 'team' THEN 3 ELSE 1 END ELSE 1 END FROM companies WHERE id=NEW.company_id)
BEGIN SELECT RAISE(ABORT,'seat_limit'); END;
CREATE TRIGGER IF NOT EXISTS invitation_seats BEFORE INSERT ON invitations
WHEN (SELECT count(*) FROM members WHERE company_id=NEW.company_id) +
 (SELECT count(*) FROM invitations WHERE company_id=NEW.company_id AND expires_at>unixepoch()) >=
 (SELECT CASE WHEN subscription_status IN ('active','trialing') AND period_end>unixepoch() THEN
 CASE plan WHEN 'business' THEN 8 WHEN 'team' THEN 3 ELSE 1 END ELSE 1 END FROM companies WHERE id=NEW.company_id)
BEGIN SELECT RAISE(ABORT,'seat_limit'); END;
CREATE TABLE IF NOT EXISTS preferences (
 company_id TEXT PRIMARY KEY REFERENCES companies(id) ON DELETE CASCADE,
 regions TEXT NOT NULL DEFAULT '[]', services TEXT NOT NULL DEFAULT '[]', updated_at INTEGER NOT NULL DEFAULT(unixepoch())
);
CREATE TABLE IF NOT EXISTS watchlist (
 company_id TEXT NOT NULL REFERENCES companies(id) ON DELETE CASCADE, signal_id TEXT NOT NULL,
 note TEXT NOT NULL DEFAULT '', reminder_date TEXT, created_at INTEGER NOT NULL DEFAULT(unixepoch()),
 PRIMARY KEY(company_id,signal_id)
);
CREATE TABLE IF NOT EXISTS alert_settings (
 user_id TEXT PRIMARY KEY REFERENCES members(user_id) ON DELETE CASCADE,
 frequency TEXT NOT NULL DEFAULT 'off' CHECK(frequency IN ('off','daily','weekly')),
 deadlines INTEGER NOT NULL DEFAULT 0 CHECK(deadlines IN (0,1)),
 unsubscribe_hash TEXT UNIQUE, updated_at INTEGER NOT NULL DEFAULT(unixepoch())
);
CREATE TABLE IF NOT EXISTS deliveries (
 id TEXT PRIMARY KEY, user_id TEXT NOT NULL REFERENCES members(user_id) ON DELETE CASCADE,
 kind TEXT NOT NULL, payload TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','sending','sent','failed','cancelled')),
 attempts INTEGER NOT NULL DEFAULT 0, lease_until INTEGER NOT NULL DEFAULT 0,
 provider_id TEXT, last_error TEXT, created_at INTEGER NOT NULL DEFAULT(unixepoch()), sent_at INTEGER
);
CREATE INDEX IF NOT EXISTS deliveries_pending ON deliveries(status,lease_until);
CREATE TABLE IF NOT EXISTS webhook_events (id TEXT PRIMARY KEY, created_at INTEGER NOT NULL DEFAULT(unixepoch()));
CREATE TABLE IF NOT EXISTS rate_limits (key TEXT PRIMARY KEY, window INTEGER NOT NULL, count INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS job_runs (id TEXT PRIMARY KEY, kind TEXT NOT NULL, status TEXT NOT NULL, detail TEXT, created_at INTEGER NOT NULL DEFAULT(unixepoch()));
CREATE TABLE IF NOT EXISTS unsubscribe_tokens(token_hash TEXT PRIMARY KEY,user_id TEXT NOT NULL REFERENCES members(user_id) ON DELETE CASCADE,expires_at INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS delivered_items(user_id TEXT NOT NULL REFERENCES members(user_id) ON DELETE CASCADE,fingerprint TEXT NOT NULL,created_at INTEGER NOT NULL DEFAULT(unixepoch()),PRIMARY KEY(user_id,fingerprint));
CREATE TABLE IF NOT EXISTS checkout_sessions(company_id TEXT PRIMARY KEY REFERENCES companies(id) ON DELETE CASCADE,request_id TEXT NOT NULL,session_id TEXT,url TEXT,plan_key TEXT NOT NULL,expires_at INTEGER NOT NULL);
