/**
 * dripthecup.com
 *
 * The site is static files. The only server code is this: the pre-order desk,
 * the /learn sign-up forms and their emails (mail.js), and the business request
 * form. There is deliberately no payment path here: nobody is charged, so
 * nothing is owed and nothing has to ship by a date.
 *
 * Only /api/* reaches this Worker (see run_worker_first in wrangler.jsonc);
 * every other request is served straight off disk. A cron (also in
 * wrangler.jsonc) sends any welcome email that did not go out the first time.
 */
import { welcome, notifyInquiry, catchUp } from './mail.js';

/**
 * The catalogue, server side, so a forged request cannot invent a product or a
 * name. Slugs must match the data-p attributes on the shop buttons in index.html.
 */
const PRODUCTS = {
  mug:      { name: 'Bean There diner mug',       sizes: [] },
  tee:      { name: 'Slow Drip boxy tee',         sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'] },
  hoodie:   { name: 'Brewed, Not Rushed hoodie',  sizes: ['S', 'M', 'L', 'XL', '2XL', '3XL'] },
  beans:    { name: 'Slow Roast whole bean',      sizes: [] },
  tote:     { name: 'A Latte to Carry tote',      sizes: [] },
  cap:      { name: 'Boot Brown dad cap',         sizes: [] },
  socks:    { name: 'All-over Drip socks',        sizes: ['S/M', 'L/XL'] },
  pin:      { name: 'Bean There enamel pin',      sizes: [] },
  stickers: { name: 'Late Reaction sticker pack', sizes: [] },
};

/** Deliberately loose. The only real test of an address is mail arriving at it. */
const EMAIL = /^[^\s@]{1,64}@[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)+$/i;

const json = (body, status = 200) =>
  new Response(JSON.stringify(body), {
    status,
    headers: { 'content-type': 'application/json; charset=utf-8', 'cache-control': 'no-store' },
  });

/**
 * A salted hash of the caller's address, for throttling only. We never store the
 * address, and the hash is useless for anything except spotting the same caller
 * hammering the endpoint within the hour.
 */
async function caller(request) {
  const ip = request.headers.get('CF-Connecting-IP') || '';
  const digest = await crypto.subtle.digest('SHA-256', new TextEncoder().encode('drip:' + ip));
  return Array.from(new Uint8Array(digest), b => b.toString(16).padStart(2, '0')).join('');
}

async function reserve(request, env) {
  if (request.method !== 'POST') return json({ error: 'post only' }, 405);

  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: 'bad request' }, 400);
  }

  // "cream" is a field no human can see or tab into, so anything in it is a bot.
  // Answer as if it worked; a bot told it failed just tries again.
  if (body.cream) return json({ ok: true });

  const slug = String(body.product || '');
  const product = PRODUCTS[slug];
  if (!product) return json({ error: 'unknown product' }, 400);

  const email = String(body.email || '').trim().toLowerCase();
  if (email.length > 254 || !EMAIL.test(email)) {
    return json({ error: "that email doesn't look right" }, 400);
  }

  const size = String(body.size || '');
  if (product.sizes.length && !product.sizes.includes(size)) {
    return json({ error: 'pick a size' }, 400);
  }
  if (!product.sizes.length && size) return json({ error: 'unknown size' }, 400);

  // Reserving all nine is nine requests, which is fine. Hundreds is a script.
  const who = await caller(request);
  const recent = await env.DB
    .prepare("select count(*) as n from throttle where who = ?1 and ts > datetime('now', '-1 hour')")
    .bind(who)
    .first();
  if (recent && recent.n >= 40) return json({ error: 'too many for one hour' }, 429);

  await env.DB.batch([
    env.DB.prepare("delete from throttle where ts < datetime('now', '-1 day')"),
    env.DB.prepare("insert into throttle (who, ts) values (?1, datetime('now'))").bind(who),
    env.DB.prepare(
      'insert into reservations (created, email, product, product_name, size, country) ' +
      'values (?1, ?2, ?3, ?4, ?5, ?6) ' +
      'on conflict (email, product) do update set size = excluded.size, created = excluded.created'
    ).bind(new Date().toISOString(), email, slug, product.name, size, (request.cf && request.cf.country) || ''),
  ]);

  return json({ ok: true });
}

/**
 * The /learn list. One row per address: someone asked to hear when the Lab opens
 * (or wants the first build by email). Signing up twice just refreshes the row.
 * "source" is which form on the site (learn-hero, learn-bottom, ...), "interest"
 * is the one thing they said they want to build, both optional and short.
 */
const SOURCES = new Set(['learn-hero', 'learn-founding', 'learn-bottom', 'learn-lab', 'learn']);

async function subscribe(request, env, ctx) {
  if (request.method !== 'POST') return json({ error: 'post only' }, 405);

  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: 'bad request' }, 400);
  }
  if (body.cream) return json({ ok: true }); // honeypot, same trick as reserve()

  const email = String(body.email || '').trim().toLowerCase();
  if (email.length > 254 || !EMAIL.test(email)) {
    return json({ error: "that email doesn't look right" }, 400);
  }
  const source = SOURCES.has(body.source) ? body.source : 'learn';
  const interest = String(body.interest || '').replace(/\s+/g, ' ').trim().slice(0, 200);

  const who = await caller(request);
  const recent = await env.DB
    .prepare("select count(*) as n from throttle where who = ?1 and ts > datetime('now', '-1 hour')")
    .bind(who)
    .first();
  if (recent && recent.n >= 40) return json({ error: 'too many for one hour' }, 429);

  await env.DB.batch([
    env.DB.prepare("delete from throttle where ts < datetime('now', '-1 day')"),
    env.DB.prepare("insert into throttle (who, ts) values (?1, datetime('now'))").bind(who),
    env.DB.prepare(
      // "unsub" is a random token for this address's unsubscribe link. Signing up
      // again from a different form re-arms the welcome for that form, and signing
      // up again at all undoes an earlier unsubscribe (they asked, twice).
      'insert into subscribers (created, email, source, interest, country, unsub) values (?1, ?2, ?3, ?4, ?5, ?6) ' +
      'on conflict (email) do update set source = excluded.source, ' +
      "interest = case when excluded.interest = '' then subscribers.interest else excluded.interest end, " +
      "welcomed = case when excluded.source = subscribers.source then subscribers.welcomed else '' end, " +
      "unsubscribed = ''"
    ).bind(new Date().toISOString(), email, source, interest, (request.cf && request.cf.country) || '', crypto.randomUUID()),
  ]);

  ctx.waitUntil(welcome(env, email).catch(() => {})); // the cron retries anything that fails here
  return json({ ok: true });
}

/**
 * "Work with me" on /learn: a business asking for a call. Kept apart from the
 * learner list so a consulting request never lands in the course emails, and
 * every request is its own row (a second message from the same address is a
 * new message, not an update).
 */
async function inquire(request, env, ctx) {
  if (request.method !== 'POST') return json({ error: 'post only' }, 405);

  let body;
  try {
    body = await request.json();
  } catch {
    return json({ error: 'bad request' }, 400);
  }
  if (body.cream) return json({ ok: true });

  const email = String(body.email || '').trim().toLowerCase();
  if (email.length > 254 || !EMAIL.test(email)) {
    return json({ error: "that email doesn't look right" }, 400);
  }
  const company = String(body.company || '').replace(/\s+/g, ' ').trim().slice(0, 120);
  const message = String(body.message || '').trim().slice(0, 1500);
  if (message.length < 10) return json({ error: 'tell me a little about what you want automated' }, 400);

  const who = await caller(request);
  const recent = await env.DB
    .prepare("select count(*) as n from throttle where who = ?1 and ts > datetime('now', '-1 hour')")
    .bind(who)
    .first();
  if (recent && recent.n >= 40) return json({ error: 'too many for one hour' }, 429);

  const [, saved] = await env.DB.batch([
    env.DB.prepare("insert into throttle (who, ts) values (?1, datetime('now'))").bind(who),
    env.DB.prepare(
      'insert into inquiries (created, email, company, message, country) values (?1, ?2, ?3, ?4, ?5)'
    ).bind(new Date().toISOString(), email, company, message, (request.cf && request.cf.country) || ''),
  ]);

  const id = saved && saved.meta && saved.meta.last_row_id;
  if (id) ctx.waitUntil(notifyInquiry(env, id).catch(() => {}));
  return json({ ok: true });
}

/**
 * The link at the bottom of every welcome email. GET shows a page a person can
 * read; POST is the one-click unsubscribe that mail apps send on their own.
 */
async function unsubscribe(request, env) {
  const url = new URL(request.url);
  const email = String(url.searchParams.get('e') || '').trim().toLowerCase();
  const token = String(url.searchParams.get('t') || '');
  let done = false;
  if (email && token) {
    const r = await env.DB.prepare("update subscribers set unsubscribed = ?3 where email = ?1 and unsub = ?2 and unsub <> ''")
      .bind(email, token, new Date().toISOString()).run();
    done = !!(r.meta && r.meta.changes);
  }
  if (request.method === 'POST') return json({ ok: done });
  const msg = done
    ? "You're unsubscribed. No more emails from Drip the Cup. If that was a mistake, sign up again on the site any time."
    : "That link didn't match an address on the list, so there's nothing to unsubscribe. If you keep getting emails, reply to one and I'll take you off by hand.";
  return new Response(
    '<!doctype html><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>Unsubscribe · Drip the Cup</title>' +
    '<body style="margin:0;background:#F6EFE0;color:#1A1A1A;font:17px/1.6 Georgia,serif"><div style="max-width:520px;margin:12vh auto;padding:0 20px">' +
    '<p style="font:11px/1 ui-monospace,monospace;letter-spacing:.18em;text-transform:uppercase;color:#6B6155">Drip the Cup</p>' +
    `<h1 style="font-size:30px;line-height:1.1;margin:10px 0 14px">${done ? 'Done.' : 'Hmm.'}</h1><p>${msg}</p>` +
    '<p><a href="/" style="color:#1A1A1A">Back to dripthecup.com</a></p></div></body>',
    { headers: { 'content-type': 'text/html; charset=utf-8', 'cache-control': 'no-store' } }
  );
}

export default {
  async fetch(request, env, ctx) {
    const { pathname } = new URL(request.url);
    if (pathname === '/api/reserve') return reserve(request, env);
    if (pathname === '/api/subscribe') return subscribe(request, env, ctx);
    if (pathname === '/api/inquire') return inquire(request, env, ctx);
    if (pathname === '/api/unsubscribe') return unsubscribe(request, env);
    if (pathname.startsWith('/api/')) return json({ error: 'not found' }, 404);
    return env.ASSETS.fetch(request);
  },
  async scheduled(event, env, ctx) {
    ctx.waitUntil(catchUp(env));
  },
};
