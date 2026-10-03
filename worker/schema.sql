-- Pre-order reservations for dripthecup.com.
--
-- Nothing here is a sale: no card, no charge, no order. A row means one person
-- said they want one of something, so we can tell what is worth making.
--
-- Apply with:  npx wrangler d1 execute dripthecup --remote --file worker/schema.sql

create table if not exists reservations (
  id           integer primary key autoincrement,
  created      text not null,          -- ISO 8601, UTC
  email        text not null,
  product      text not null,          -- slug, matches PRODUCTS in worker/index.js
  product_name text not null,          -- copied in so old rows stay readable if a name changes
  size         text not null default '',
  country      text not null default ''
);

-- One reservation per person per product; reserving again just updates the size.
create unique index if not exists reservations_person on reservations (email, product);
create index if not exists reservations_product on reservations (product);

-- Abuse throttle only. Holds a salted hash of the caller's IP, never the address
-- itself, and rows older than a day are deleted on the next write.
create table if not exists throttle (
  who text not null,
  ts  text not null
);
create index if not exists throttle_who on throttle (who, ts);

-- The /learn email list (added 2026-09-30). One row per address. A row means one
-- person asked to hear when the Lab opens. No double opt-in yet: the first mail
-- they get should say how to leave. "source" is the form on the site that sent
-- it; "interest" is the one thing they said they want to build (optional).
create table if not exists subscribers (
  id       integer primary key autoincrement,
  created  text not null,          -- ISO 8601, UTC
  email    text not null,
  source   text not null default '',
  interest text not null default '',
  country  text not null default ''
);
create unique index if not exists subscribers_email on subscribers (email);

-- "Work with me" requests from businesses on /learn (added 2026-10-02). Every
-- message is its own row; kept apart from the learner list on purpose.
create table if not exists inquiries (
  id       integer primary key autoincrement,
  created  text not null,          -- ISO 8601, UTC
  email    text not null,
  company  text not null default '',
  message  text not null default '',
  country  text not null default ''
);
create index if not exists inquiries_created on inquiries (created);

-- Emails (added 2026-10-03). The welcome goes out at sign-up through Gmail (see
-- worker/mail.js); "welcomed" is when it went, "unsub" the random token in the
-- unsubscribe link, "unsubscribed" when they used it. email_log keeps every send.
alter table subscribers add column welcomed text not null default '';
alter table subscribers add column unsub text not null default '';
alter table subscribers add column unsubscribed text not null default '';
alter table inquiries add column notified text not null default '';
create table if not exists email_log (
  id       integer primary key autoincrement,
  created  text not null default (datetime('now')),
  email    text not null,
  template text not null,
  status   text not null,               -- sent | failed | held
  error    text not null default ''
);
create index if not exists email_log_email on email_log (email, template, status);
create index if not exists email_log_created on email_log (created);
