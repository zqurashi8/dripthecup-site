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
