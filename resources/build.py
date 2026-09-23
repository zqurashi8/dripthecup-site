"""Build resources/index.html from resources.json.

Add or edit a tool in resources.json, then run:  python resources/build.py
Layout (after efficient.app's pattern, denser): a category sidebar, a "starting picks" strip,
and one compact row per tool that expands for details. Plain HTML works without JavaScript;
a small script adds search and the phone category picker."""
import html, json, os, time, urllib.error, urllib.request
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, 'resources.json'), encoding='utf8'))
SEEN = {'claude-code-repos': '4 free repos for Claude Code', 'jev-vs-chatgpt': 'Jev vs ChatGPT'}
e = html.escape


ICONS = os.path.join(HERE, 'icons')


def icon(url):
    """Each tool's favicon (a GitHub repo gets its owner's avatar), downloaded once into
    resources/icons/ so the page never hot-links a third party."""
    u = urlparse(url)
    if u.netloc == 'github.com' and u.path.strip('/').split('/')[0] not in ('features', 'marketplace'):
        key = 'gh-' + u.path.strip('/').split('/')[0].lower()
        src = f'https://github.com/{u.path.strip("/").split("/")[0]}.png?size=64'
    else:
        key = u.netloc.replace('www.', '')
        src = f'https://www.google.com/s2/favicons?domain={u.netloc}&sz=64'
    path = os.path.join(ICONS, key + '.png')
    if not os.path.exists(path):
        os.makedirs(ICONS, exist_ok=True)
        req = urllib.request.Request(src, headers={'User-Agent': 'Mozilla/5.0'})
        data = None
        for attempt in range(3):
            try:
                with urllib.request.urlopen(req, timeout=20) as r:
                    data = r.read()
                break
            except urllib.error.HTTPError as err:  # no icon known: Google still sends its globe
                data = err.read() or None
                break
            except Exception:
                time.sleep(1.5 * (attempt + 1))
        if data:
            open(path, 'wb').write(data)
        else:  # offline or refused: a letter tile in house colours, so the build never fails
            from PIL import Image, ImageDraw, ImageFont
            im = Image.new('RGB', (64, 64), (227, 172, 42)); d = ImageDraw.Draw(im)
            try:
                font = ImageFont.truetype('georgiab.ttf', 38)
            except OSError:
                font = ImageFont.load_default()
            d.text((32, 33), key.replace('gh-', '')[0].upper(), fill=(26, 26, 26), font=font, anchor='mm')
            im.save(path)
    return f'icons/{key}.png'


def slug(name):
    return 't-' + ''.join(ch if ch.isalnum() else '-' for ch in name.lower()).strip('-')


def row(it, cat):
    badges = ''
    if it.get('kind'):
        badges += f'<span class="b">{e(it["kind"])}</span>'
    if it.get('stars'):
        badges += f'<span class="b st">★ {e(it["stars"])}</span>'
    extra = ''
    if it.get('note'):
        extra += f'<p class="warn">{e(it["note"])}</p>'
    if it.get('install'):
        extra += f'<pre>{e(it["install"])}</pre>'
    if it.get('seen'):
        extra += f'<a class="seen" href="/links/#{it["seen"]}">seen in our video: {e(SEEN[it["seen"]])} →</a>'
    q = ' '.join([it['name'], it.get('by', ''), it['best'], it.get('kind', ''), cat['name'],
                  'free' if it.get('kind') in ('free', 'open source') else '']).lower()
    head = f'''<img src="{icon(it["url"])}" alt="" width="28" height="28" loading="lazy">
          <span class="nm"><a href="{e(it["url"])}" target="_blank" rel="noopener">{e(it["name"])}</a><small>{e(it.get("by", ""))}</small></span>
          <span class="bf">{e(it["best"])}</span>
          <span class="bs">{badges}</span>'''
    if extra:
        return f'''      <li class="r" id="{slug(it['name'])}" data-q="{e(q)}"><details><summary>{head}<span class="more" aria-hidden="true">+</span></summary><div class="ex">{extra}</div></details></li>'''
    return f'''      <li class="r" id="{slug(it['name'])}" data-q="{e(q)}"><div class="rw">{head}<a class="go" href="{e(it["url"])}" target="_blank" rel="noopener" aria-label="Open {e(it["name"])}">↗</a></div></li>'''


LONG = 8  # a category longer than this scrolls inside its own box
TASKS_PATH = os.path.join(HERE, 'tasks.json')
TASKS = json.load(open(TASKS_PATH, encoding='utf8')) if os.path.exists(TASKS_PATH) else None
cats = D['categories']
total = sum(len(c['items']) for c in cats)
side = '\n'.join(f'      <a href="#{c["id"]}"><span class="ic">{c["icon"]}</span>{e(c["name"])}<span class="n">{len(c["items"])}</span></a>' for c in cats)
opts = '\n'.join(f'      <option value="{c["id"]}">{c["icon"]} {e(c["name"])} ({len(c["items"])})</option>' for c in cats)
tops = [(it, c) for c in cats for it in c['items'] if it.get('top')]
picks = '\n'.join(f'''      <a class="pk" href="{e(it["url"])}" target="_blank" rel="noopener"><img src="{icon(it["url"])}" alt="" width="24" height="24" loading="lazy"><span><b>{e(it["name"])}</b><small>{e(c["name"])}</small></span></a>''' for it, c in tops)
sections = '\n'.join(f'''    <section class="cat" id="{c["id"]}">
      <h2><span class="ic">{c["icon"]}</span>{e(c["name"])} <span class="n">{len(c["items"])}</span></h2>
      <p class="blurb">{e(c["blurb"])}</p>
      <ul class="rows{' long' if len(c['items']) > LONG else ''}">
{chr(10).join(row(it, c) for it in c["items"])}
      </ul>{f'<p class="more-note">Showing {LONG} of {len(c["items"])}. Scroll the list for the rest.</p>' if len(c['items']) > LONG else ''}
    </section>''' for c in cats)

if TASKS:
    btns = '\n'.join(f'    <button type="button" data-task="{i}" aria-pressed="false">{e(t["task"])}</button>' for i, t in enumerate(TASKS['tasks']))
    jev_block = f'''<section class="jev" aria-label="Find a tool by task">
  <h2>What do you want to do?<small>tools matched by Jev</small></h2>
  <div class="tasks">
{btns}
  </div>
  <p class="jev-out" id="jevout" hidden></p>
  <script type="application/json" id="taskdata">{json.dumps(TASKS["tasks"])}</script>
</section>'''
else:
    jev_block = ''

page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>AI tools directory · Drip the Cup</title>
<meta name="description" content="{total} AI tools sorted by what you want to do: chat, agents, coding, dictation, note takers, email, CRM, finance, video, voice and more.">
<link rel="canonical" href="https://dripthecup.com/resources/">
<meta property="og:type" content="website">
<meta property="og:url" content="https://dripthecup.com/resources/">
<meta property="og:title" content="AI tools directory · Drip the Cup">
<meta property="og:description" content="{total} AI tools in {len(cats)} categories. One line each on what they're best for.">
<meta property="og:image" content="https://dripthecup.com/assets/og.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#E3AC2A">
<link rel="icon" href="../assets/favicon-32.png" sizes="32x32">
<link rel="apple-touch-icon" href="../assets/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,900&display=swap">
<style>
  :root{{
    --mustard:#E3AC2A; --paper:#F6EFE0; --cup:#F5F1E8; --ink:#1A1A1A; --muted:#6B6155;
    --red:#D63F2A; --dark:#100D09; --line:#D9CFBC; --hover:#EFE6D2;
    --display:'Fraunces', Georgia, 'Times New Roman', serif;
    --body:Georgia, 'Times New Roman', serif;
    --mono:ui-monospace, 'Cascadia Mono', 'Courier New', monospace;
  }}
  *{{box-sizing:border-box;}}
  html{{scroll-padding-top:70px;}}
  body{{margin:0;background:var(--paper);color:var(--ink);font-family:var(--body);font-size:15px;line-height:1.45;-webkit-font-smoothing:antialiased;}}
  a{{color:inherit;}}
  :focus-visible{{outline:3px solid var(--red);outline-offset:2px;}}
  h1,h2{{text-wrap:balance;margin:0;}}
  .hdr{{background:var(--paper);border-bottom:1px solid var(--line);position:sticky;top:env(safe-area-inset-top, 0px);z-index:20;}}
  .hdr .in{{max-width:1240px;margin:0 auto;padding:12px 20px;display:flex;align-items:center;justify-content:space-between;gap:12px;}}
  .brand{{font-family:var(--display);font-weight:900;font-size:22px;letter-spacing:-.02em;text-decoration:none;line-height:1;}}
  .hnav{{display:flex;gap:2px;flex-wrap:wrap;}}
  .hnav a{{font-family:var(--mono);font-size:11.5px;letter-spacing:.12em;text-transform:uppercase;text-decoration:none;padding:7px 10px;}}
  .hnav a:hover,.hnav a[aria-current]{{background:var(--mustard);}}

  /* compact intro: title, search, Drip small on mustard */
  .intro{{max-width:1240px;margin:0 auto;padding:30px 20px 18px;display:flex;align-items:flex-end;gap:24px;}}
  .intro .t{{flex:1;min-width:0;}}
  .eyebrow{{font-family:var(--mono);font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:var(--muted);margin:0;}}
  .intro h1{{font-family:var(--display);font-weight:900;font-size:clamp(30px,4vw,48px);line-height:1.02;letter-spacing:-.025em;margin-top:8px;}}
  .intro p{{margin:10px 0 0;color:var(--muted);max-width:60ch;}}
  .search{{margin-top:16px;display:flex;align-items:center;max-width:520px;border:2px solid var(--ink);background:var(--cup);}}
  .search span{{padding-left:12px;font-family:var(--mono);color:var(--muted);}}
  .search input{{flex:1;min-width:0;border:0;background:transparent;font:15px var(--mono);padding:11px 12px;color:var(--ink);}}
  .search input:focus{{outline:none;}}
  .search:focus-within{{box-shadow:4px 4px 0 var(--ink);}}
  .drip{{background:var(--mustard);border:2px solid var(--ink);width:150px;height:150px;flex:none;display:flex;align-items:flex-end;justify-content:center;overflow:hidden;box-shadow:5px 5px 0 var(--ink);}}
  .drip img{{width:88px;display:block;}}
  @media (max-width:700px){{.drip{{display:none;}}}}

  /* starting picks strip */
  .picks{{max-width:1240px;margin:0 auto;padding:6px 20px 18px;}}
  .picks h2{{font-family:var(--mono);font-size:11px;letter-spacing:.18em;text-transform:uppercase;color:var(--muted);font-weight:400;margin-bottom:8px;}}
  .pks{{display:flex;gap:8px;overflow-x:auto;padding-bottom:6px;scrollbar-width:thin;}}
  .pk{{flex:none;display:flex;align-items:center;gap:9px;text-decoration:none;border:1.5px solid var(--ink);background:var(--cup);padding:7px 12px 7px 9px;}}
  .pk:hover{{background:var(--mustard);}}
  .pk img{{border-radius:5px;}}
  .pk b{{display:block;font-family:var(--display);font-size:15px;line-height:1.1;}}
  .pk small{{display:block;font-family:var(--mono);font-size:10.5px;color:var(--muted);}}

  /* layout: sidebar + list */
  .layout{{max-width:1240px;margin:0 auto;padding:0 20px 40px;display:grid;grid-template-columns:250px minmax(0,1fr);gap:32px;border-top:1px solid var(--line);}}
  .side{{position:sticky;top:64px;align-self:start;max-height:calc(100vh - 80px);overflow:auto;padding:18px 4px 18px 0;}}
  .side a{{display:flex;align-items:center;gap:8px;text-decoration:none;font-size:14px;padding:6px 8px;border-radius:0;}}
  .side a:hover{{background:var(--hover);}}
  .side a.on{{background:var(--mustard);}}
  .side .n{{margin-left:auto;font-family:var(--mono);font-size:11px;color:var(--muted);}}
  .ic{{width:20px;text-align:center;flex:none;}}
  .pick{{display:none;}}
  @media (max-width:900px){{
    .layout{{grid-template-columns:minmax(0,1fr);gap:0;}}
    .side{{display:none;}}
    .pick{{display:block;position:sticky;top:56px;z-index:10;background:var(--paper);padding:10px 0;border-bottom:1px solid var(--line);}}
    .pick select{{width:100%;font:14px var(--mono);padding:10px;border:2px solid var(--ink);background:var(--cup);color:var(--ink);}}
  }}

  .cat{{padding-top:24px;}}
  .cat h2{{font-family:var(--display);font-weight:900;font-size:24px;letter-spacing:-.015em;display:flex;align-items:center;gap:8px;}}
  .cat h2 .n{{font-family:var(--mono);font-size:12px;font-weight:400;color:var(--muted);}}
  .blurb{{margin:4px 0 10px;color:var(--muted);font-size:14px;max-width:80ch;}}
  .rows{{list-style:none;margin:0;padding:0;border-top:1.5px solid var(--ink);}}
  .r{{border-bottom:1px solid var(--line);}}
  .rw, .r summary{{display:grid;grid-template-columns:28px minmax(120px,190px) minmax(0,1fr) auto 22px;align-items:center;gap:12px;padding:9px 6px;}}
  .r summary{{cursor:pointer;list-style:none;}}
  .r summary::-webkit-details-marker{{display:none;}}
  .rw:hover, .r summary:hover{{background:var(--hover);}}
  .r img{{border-radius:6px;background:#fff;}}
  .nm{{min-width:0;}}
  .nm a{{font-family:var(--display);font-weight:600;font-size:16px;text-decoration:none;}}
  .nm a:hover{{background:var(--mustard);}}
  .nm small{{display:block;font-family:var(--mono);font-size:10.5px;color:var(--muted);white-space:nowrap;overflow:hidden;text-overflow:ellipsis;}}
  .bf{{font-size:14.5px;}}
  .bs{{display:flex;gap:5px;flex-wrap:wrap;justify-content:flex-end;}}
  .b{{font-family:var(--mono);font-size:10px;letter-spacing:.1em;text-transform:uppercase;border:1px solid var(--ink);padding:2px 6px;white-space:nowrap;}}
  .b.we{{background:var(--mustard);}}
  .b.st{{background:var(--ink);color:var(--paper);}}
  .go, .more{{font-family:var(--mono);text-decoration:none;text-align:center;color:var(--muted);}}
  .go:hover{{color:var(--ink);}}
  details[open] .more{{transform:rotate(45deg);}}
  .ex{{padding:0 6px 12px 46px;}}
  .ex pre{{margin:6px 0 0;background:var(--dark);color:#EDE6D8;padding:9px 12px;overflow-x:auto;font:12.5px/1.5 var(--mono);white-space:pre;}}
  .warn{{margin:6px 0 0;font-size:13.5px;border-left:3px solid var(--red);padding-left:10px;}}
  .seen{{display:inline-block;margin-top:8px;font-family:var(--mono);font-size:11px;letter-spacing:.06em;text-transform:uppercase;}}
  @media (max-width:640px){{
    .rw, .r summary{{grid-template-columns:28px minmax(0,1fr) 22px;grid-template-areas:"i n g" "i f f" "i b b";row-gap:3px;}}
    .r img{{grid-area:i;align-self:start;margin-top:3px;}} .nm{{grid-area:n;}} .bf{{grid-area:f;font-size:14px;color:var(--muted);}}
    .bs{{grid-area:b;justify-content:flex-start;}} .bs:empty{{display:none;}} .go,.more{{grid-area:g;}}
    .ex{{padding-left:6px;}}
  }}
  .rows.long{{max-height:470px;overflow-y:auto;overscroll-behavior:contain;border-bottom:1.5px solid var(--ink);}}
  @media (max-width:640px){{.rows.long{{max-height:640px;}}}}
  body.searching .rows.long, body.tasking .rows.long{{max-height:none;border-bottom:0;}}
  body.searching .more-note, body.tasking .more-note{{display:none;}}
  .more-note{{font-family:var(--mono);font-size:11px;color:var(--muted);margin:6px 0 0;}}
  /* Jev task finder */
  .jev{{max-width:1240px;margin:0 auto;padding:4px 20px 20px;}}
  .jev h2{{font-family:var(--display);font-weight:900;font-size:22px;letter-spacing:-.01em;}}
  .jev h2 small{{font-family:var(--mono);font-size:11px;font-weight:400;color:var(--muted);letter-spacing:.08em;margin-left:8px;}}
  .tasks{{display:flex;flex-wrap:wrap;gap:7px;margin-top:10px;}}
  .tasks button{{font:13px var(--body);border:1.5px solid var(--ink);background:var(--cup);padding:7px 11px;cursor:pointer;color:var(--ink);}}
  .tasks button:hover{{background:var(--hover);}}
  .tasks button[aria-pressed="true"]{{background:var(--ink);color:var(--paper);}}
  .jev-out{{font-family:var(--mono);font-size:12px;margin-top:10px;color:var(--muted);}}
  .jev-out button{{font:inherit;border:0;background:none;text-decoration:underline;cursor:pointer;color:var(--ink);}}
  .r .fit{{font-family:var(--mono);font-size:10px;background:#2F6B4F;color:#fff;padding:2px 6px;letter-spacing:.06em;}}
  .empty{{font-family:var(--mono);color:var(--muted);padding:40px 0;}}
  .fine{{font-family:var(--mono);font-size:11.5px;color:var(--muted);padding-top:28px;margin-top:28px;border-top:1px solid var(--line);max-width:80ch;}}
  .foot{{background:var(--dark);color:#CFC4B0;padding:26px 20px;font-family:var(--mono);font-size:12px;text-align:center;}}
  .foot a{{color:var(--mustard);}}
</style>
</head>
<body>

<header class="hdr"><div class="in">
  <a class="brand" href="/">DRIP.</a>
  <nav class="hnav" aria-label="Main">
    <a href="/">Home</a>
    <a href="/resources/" aria-current="page">AI tools</a>
    <a href="/links/">From the videos</a>
  </nav>
</div></header>

<div class="intro">
  <div class="t">
    <p class="eyebrow">AI tools directory · {total} tools · {len(cats)} categories</p>
    <h1>Find the right AI tool, fast.</h1>
    <p>One line each on what it's best for. Click a row with a <b>+</b> for install commands and notes.</p>
    <label class="search" for="q"><span>⌕</span><input id="q" type="search" placeholder="Try: dictation, email, free, video, agent..." autocomplete="off" aria-label="Search {total} AI tools"></label>
  </div>
  <div class="drip" aria-hidden="true"><img src="../assets/drip2-idle.png" alt=""></div>
</div>

<section class="picks" aria-label="Starting picks">
  <h2>Where we'd start</h2>
  <div class="pks">
{picks}
  </div>
</section>

{jev_block}
<div class="layout">
  <nav class="side" aria-label="Categories">
{side}
  </nav>
  <main>
    <div class="pick"><select id="jump" aria-label="Jump to a category">
      <option value="">Jump to a category...</option>
{opts}
    </select></div>
{sections}
    <p class="empty" id="empty" hidden>Nothing matches that yet. Drip is still learning.</p>
    <p class="fine">Last checked {e(D["updated"])}. Star counts are GitHub's on that day. We're not paid by any of these companies; if that ever changes, it will say so here. Tools change fast, so check each site for current pricing and features. Icons are each site's own favicon.</p>
  </main>
</div>

<footer class="foot">drip the cup · <a href="/">dripthecup.com</a> · a cup of coffee learning about a.i.</footer>

<script>
  const q = document.getElementById('q'), empty = document.getElementById('empty');
  q.addEventListener('input', () => {{
    document.body.classList.toggle('searching', q.value.trim() !== '');
    clearTask();
    const terms = q.value.toLowerCase().trim().split(/\\s+/).filter(Boolean);
    let shown = 0;
    document.querySelectorAll('.cat').forEach(cat => {{
      let n = 0;
      cat.querySelectorAll('.r').forEach(r => {{ const hit = terms.every(t => r.dataset.q.includes(t)); r.hidden = !hit; if (hit) n++; }});
      cat.hidden = n === 0; shown += n;
    }});
    empty.hidden = shown > 0;
  }});
  // Jev task finder: each task lists the tools Jev judged a strong fit (probability kept per tool)
  const td = document.getElementById('taskdata');
  const TASKS = td ? JSON.parse(td.textContent) : [];
  const out = document.getElementById('jevout');
  function clearTask() {{
    document.body.classList.remove('tasking');
    document.querySelectorAll('.tasks button').forEach(b => b.setAttribute('aria-pressed', 'false'));
    document.querySelectorAll('.r .fit').forEach(x => x.remove());
    if (out) out.hidden = true;
  }}
  document.querySelectorAll('.tasks button').forEach(btn => btn.addEventListener('click', () => {{
    const on = btn.getAttribute('aria-pressed') === 'true';
    q.value = ''; document.body.classList.remove('searching');
    clearTask();
    document.querySelectorAll('.r').forEach(r => r.hidden = false);
    document.querySelectorAll('.cat').forEach(c => c.hidden = false);
    empty.hidden = true;
    if (on) return;
    const t = TASKS[+btn.dataset.task], pick = new Map(t.tools.map(x => [x.id, x.p]));
    btn.setAttribute('aria-pressed', 'true'); document.body.classList.add('tasking');
    document.querySelectorAll('.cat').forEach(cat => {{
      let n = 0;
      cat.querySelectorAll('.r').forEach(r => {{
        const p = pick.get(r.id); r.hidden = p === undefined;
        if (p !== undefined) {{ n++; const s = document.createElement('span'); s.className = 'fit'; s.textContent = Math.round(p * 100) + '% fit'; r.querySelector('.bs').prepend(s); }}
      }});
      cat.hidden = n === 0;
    }});
    out.hidden = false;
    out.innerHTML = `Jev picked ${{t.tools.length}} tools for “${{t.task}}”. <button type="button">show everything</button>`;
    out.querySelector('button').onclick = () => btn.click();
    document.querySelector('.layout').scrollIntoView({{behavior: 'smooth'}});
  }}));
  document.getElementById('jump').addEventListener('change', ev => {{ if (ev.target.value) location.hash = ev.target.value; }});
  // highlight the category you're reading in the sidebar
  const links = [...document.querySelectorAll('.side a')];
  const io = new IntersectionObserver(es => es.forEach(en => {{
    if (en.isIntersecting) links.forEach(a => a.classList.toggle('on', a.hash === '#' + en.target.id));
  }}), {{rootMargin: '-70px 0px -70% 0px'}});
  document.querySelectorAll('.cat').forEach(c => io.observe(c));
</script>
</body>
</html>
'''
open(os.path.join(HERE, 'index.html'), 'w', encoding='utf8').write(page)
print(f'resources/index.html: {len(cats)} categories, {total} tools, {len(tops)} starting picks')
