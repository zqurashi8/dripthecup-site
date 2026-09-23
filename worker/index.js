/**
 * dripthecup.com
 *
 * The site is static files. The only server code is this: the pre-order desk.
 * Someone gives an email and says which thing they want, we write one row, and
 * that is the whole transaction. There is deliberately no payment path here --
 * nobody is charged, so nothing is owed and nothing has to ship by a date.
 *
 * Only /api/* reaches this Worker (see run_worker_first in wrangler.jsonc);
 * every other request is served straight off disk.
 */

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
const EMAIL = /^[^\s@,;:<>"'\]{1,64}@[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?(\.[a-z0-9]([a-z0-9-]{0,61}[a-z0-9])?)+$/i;

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

export default {
  async fetch(request, env) {
    const { pathname } = new URL(request.url);
    if (pathname === '/api/reserve') return reserve(request, env);
    if (pathname.startsWith('/api/')) return json({ error: 'not found' }, 404);
    return env.ASSETS.fetch(request);
  },
};
