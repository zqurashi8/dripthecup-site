/**
 * Our own little email kit.
 *
 * Templates are plain HTML files in /emails on the site (Zain edits those; the
 * <title> is the subject). This file fills in {{placeholders}}, builds the MIME
 * message, and sends it through Gmail as GMAIL_USER with GMAIL_APP_PASSWORD
 * (both Worker secrets). Every send is written to the email_log table.
 *
 * Without the two secrets nothing is sent and nothing breaks: the rows wait, and
 * the cron in index.js welcomes them once the secrets exist.
 */
import { sendSmtp } from './smtp.js';

const SITE = 'https://dripthecup.com';
const FROM_NAME = 'Zain from Drip the Cup';
const DAILY_CAP = 450; // personal Gmail allows 500 a day; keep some room for replies

/** Which welcome each form gets. Keys are the "source" values the forms send. */
const WELCOME = {
  'learn-lab': 'welcome-lab',
  'learn-founding': 'welcome-founding',
  'learn-hero': 'welcome-free',
  'learn-bottom': 'welcome-free',
  learn: 'welcome-free',
};

const esc = s => String(s).replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);

function unentity(s) {
  return s.replace(/&nbsp;/g, ' ').replace(/&middot;/g, '·').replace(/&rarr;/g, '->').replace(/&amp;/g, '&')
    .replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"').replace(/&#39;/g, "'")
    .replace(/&#(\d+);/g, (_, n) => String.fromCharCode(Number(n)));
}

/** A readable plain-text twin of the HTML, for clients that prefer it. */
function toText(html) {
  const body = (html.match(/<body[^>]*>([\s\S]*)<\/body>/i) || [, html])[1];
  return unentity(
    body
      .replace(/<(style|script|head)[\s\S]*?<\/\1>/gi, '')
      .replace(/<div[^>]*class="preheader"[\s\S]*?<\/div>/i, '')
      .replace(/<a [^>]*href="([^"]+)"[^>]*>([\s\S]*?)<\/a>/gi, (_, href, label) => `${label.replace(/<[^>]+>/g, '').trim()} (${href})`)
      .replace(/<br\s*\/?>/gi, '\n')
      .replace(/<\/(p|h1|h2|h3|tr|li|table)>/gi, '\n\n')
      .replace(/<[^>]+>/g, '')
  ).replace(/[ \t]+/g, ' ').replace(/\n[ \t]+/g, '\n').replace(/\n{3,}/g, '\n\n').trim();
}

function b64(str) {
  const bytes = new TextEncoder().encode(str);
  let bin = '';
  for (let i = 0; i < bytes.length; i++) bin += String.fromCharCode(bytes[i]);
  return btoa(bin);
}
const wrap76 = s => s.replace(/.{1,76}/g, '$&\r\n').trimEnd();
const header = s => (/^[\x20-\x7e]*$/.test(s) ? s : `=?UTF-8?B?${b64(s)}?=`);

function message({ from, to, replyTo, subject, html, text, unsubscribe }) {
  const boundary = 'drip-' + crypto.randomUUID().replace(/-/g, '');
  const head = [
    `From: ${header(FROM_NAME)} <${from}>`,
    `To: <${to}>`,
    replyTo && `Reply-To: <${replyTo}>`,
    `Subject: ${header(subject)}`,
    `Date: ${new Date().toUTCString()}`,
    `Message-ID: <${crypto.randomUUID()}@dripthecup.com>`,
    'MIME-Version: 1.0',
    unsubscribe && `List-Unsubscribe: <${unsubscribe}>`,
    unsubscribe && 'List-Unsubscribe-Post: List-Unsubscribe=One-Click',
    `Content-Type: multipart/alternative; boundary="${boundary}"`,
  ].filter(Boolean);
  const part = (type, body) =>
    `--${boundary}\r\nContent-Type: ${type}; charset=UTF-8\r\nContent-Transfer-Encoding: base64\r\n\r\n${wrap76(b64(body))}\r\n`;
  return head.join('\r\n') + '\r\n\r\n' + part('text/plain', text) + part('text/html', html) + `--${boundary}--\r\n`;
}

async function loadTemplate(env, name) {
  // Assets drop ".html" from URLs, so ask for the clean path and follow one redirect if needed.
  let res = await env.ASSETS.fetch(new Request(`${SITE}/emails/${name}`));
  if (res.status >= 300 && res.status < 400 && res.headers.get('location')) {
    res = await env.ASSETS.fetch(new Request(new URL(res.headers.get('location'), SITE)));
  }
  if (!res.ok) throw new Error(`template ${name}: ${res.status}`);
  return res.text();
}

async function log(env, to, template, status, error = '') {
  await env.DB.prepare('insert into email_log (email, template, status, error) values (?1, ?2, ?3, ?4)')
    .bind(to, template, status, String(error).slice(0, 500)).run();
}

/** Fill a template and send it. Returns true only when Gmail accepted the message. */
export async function sendTemplate(env, { template, to, vars = {}, replyTo, unsubscribe }) {
  if (!env.GMAIL_USER || !env.GMAIL_APP_PASSWORD) return false;
  const sent = await env.DB.prepare("select count(*) as n from email_log where status = 'sent' and created > datetime('now', '-1 day')").first();
  if (sent && sent.n >= DAILY_CAP) { await log(env, to, template, 'held', 'daily cap'); return false; }
  try {
    const all = { site: SITE, unsubscribe: unsubscribe || '', ...vars };
    const html = (await loadTemplate(env, template)).replace(/\{\{(\w+)\}\}/g, (_, k) => (k in all ? esc(all[k]) : ''));
    const subject = unentity(((html.match(/<title>([\s\S]*?)<\/title>/i) || [])[1] || 'Drip the Cup').trim());
    const from = env.GMAIL_USER.trim();
    await sendSmtp({
      user: from,
      pass: env.GMAIL_APP_PASSWORD.replace(/\s+/g, ''),
      from,
      to,
      data: message({ from, to, replyTo, subject, html, text: toText(html), unsubscribe }),
    });
    await log(env, to, template, 'sent');
    return true;
  } catch (e) {
    await log(env, to, template, 'failed', e && e.message);
    return false;
  }
}

/**
 * Welcome one subscriber with the email for the form they used, once per form,
 * then tell Zain. Safe to call twice: the email_log check stops repeats.
 */
export async function welcome(env, email) {
  const row = await env.DB.prepare('select email, source, interest, country, unsub, unsubscribed from subscribers where email = ?1').bind(email).first();
  if (!row || row.unsubscribed) return;
  const template = WELCOME[row.source] || 'welcome-free';
  const already = await env.DB.prepare("select 1 from email_log where email = ?1 and template = ?2 and status = 'sent' limit 1").bind(email, template).first();
  if (!already) {
    const unsubscribe = `${SITE}/api/unsubscribe?e=${encodeURIComponent(email)}&t=${row.unsub}`;
    if (!(await sendTemplate(env, { template, to: email, unsubscribe }))) return;
  }
  await env.DB.prepare('update subscribers set welcomed = ?2 where email = ?1').bind(email, new Date().toISOString()).run();
  const totals = await env.DB.prepare("select count(*) as n from subscribers where unsubscribed = ''").first();
  await sendTemplate(env, {
    template: 'notify-signup',
    to: env.GMAIL_USER.trim(),
    vars: { email, source: row.source, interest: row.interest || '(none)', country: row.country || '?', total: totals ? totals.n : '?' },
  });
}

/** Forward a business request to Zain; replying to it goes straight to the sender. */
export async function notifyInquiry(env, id) {
  const row = await env.DB.prepare('select id, email, company, message, country, notified from inquiries where id = ?1').bind(id).first();
  if (!row || row.notified) return;
  const ok = await sendTemplate(env, {
    template: 'notify-inquiry',
    to: env.GMAIL_USER.trim(),
    replyTo: row.email,
    vars: { email: row.email, company: row.company || 'no company given', message: row.message, country: row.country || '?' },
  });
  if (ok) await env.DB.prepare('update inquiries set notified = ?2 where id = ?1').bind(id, new Date().toISOString()).run();
}

/** The cron: anything that did not go out the first time (no secrets yet, Gmail hiccup). */
export async function catchUp(env) {
  if (!env.GMAIL_USER || !env.GMAIL_APP_PASSWORD) return;
  const waiting = await env.DB.prepare(
    "select email from subscribers where welcomed = '' and unsubscribed = '' and created > ?1 order by created limit 20"
  ).bind(new Date(Date.now() - 7 * 864e5).toISOString()).all();
  for (const r of waiting.results || []) await welcome(env, r.email);
  const open = await env.DB.prepare("select id from inquiries where notified = '' order by id limit 10").all();
  for (const r of open.results || []) await notifyInquiry(env, r.id);
}
