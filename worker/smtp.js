/**
 * Just enough SMTP to hand one message to Gmail from a Worker.
 *
 * Workers can open TCP sockets (cloudflare:sockets), but not on port 25, so this
 * speaks implicit TLS on 465, which Gmail accepts with an App Password. One
 * connection per message keeps it simple; the volume here is a few a day.
 */
import { connect } from 'cloudflare:sockets';

export async function sendSmtp({ host = 'smtp.gmail.com', port = 465, user, pass, from, to, data }) {
  const socket = connect({ hostname: host, port }, { secureTransport: 'on' });
  const writer = socket.writable.getWriter();
  const reader = socket.readable.getReader();
  const enc = new TextEncoder();
  const dec = new TextDecoder();
  let buf = '';

  // A reply can span several lines ("250-..."); the last one has a space after the code.
  async function reply() {
    for (;;) {
      const lines = buf.split('\r\n');
      for (let i = 0; i < lines.length - 1; i++) {
        if (/^\d{3} /.test(lines[i])) {
          const out = { code: Number(lines[i].slice(0, 3)), text: lines.slice(0, i + 1).join(' | ') };
          buf = lines.slice(i + 1).join('\r\n');
          return out;
        }
      }
      const { value, done } = await reader.read();
      if (done) throw new Error('smtp: the server closed the connection');
      buf += dec.decode(value, { stream: true });
    }
  }

  async function say(line, ok, label = line.split(' ')[0]) {
    await writer.write(enc.encode(line + '\r\n'));
    const r = await reply();
    if (!ok.includes(r.code)) throw new Error(`smtp ${label}: ${r.text}`);
    return r;
  }

  try {
    const hello = await reply();
    if (hello.code !== 220) throw new Error('smtp greeting: ' + hello.text);
    await say('EHLO dripthecup.com', [250]);
    await say('AUTH PLAIN ' + btoa('\0' + user + '\0' + pass), [235], 'AUTH');
    await say(`MAIL FROM:<${from}>`, [250]);
    for (const rcpt of [].concat(to)) await say(`RCPT TO:<${rcpt}>`, [250, 251]);
    await say('DATA', [354]);
    // Lines that start with a dot get a second one (SMTP's escape), then the lone dot ends the message.
    const body = data.replace(/\r?\n/g, '\r\n').replace(/^\./gm, '..');
    await writer.write(enc.encode(body + '\r\n.\r\n'));
    const accepted = await reply();
    if (accepted.code !== 250) throw new Error('smtp DATA: ' + accepted.text);
    await writer.write(enc.encode('QUIT\r\n')).catch(() => {});
  } finally {
    try { await socket.close(); } catch { /* already closed */ }
  }
}
