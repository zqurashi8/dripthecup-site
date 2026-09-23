"""Build resources/index.html from resources.json.

Add or edit a tool in resources.json, then run:  python resources/build.py
The page is plain static HTML (works without JavaScript); a small script adds search."""
import html, json, os

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, 'resources.json'), encoding='utf8'))
SEEN = {'claude-code-repos': '4 free repos for Claude Code', 'jev-vs-chatgpt': 'Jev vs ChatGPT'}
e = html.escape


def card(it):
    tags = ''
    if it.get('kind'):
        tags += f'<span class="kind">{e(it["kind"])}</span>'
    if it.get('use'):
        tags += '<span class="we">we use this</span>'
    stars = f'<span class="stars">★ {e(it["stars"])}</span>' if it.get('stars') else ''
    install = f'<pre>{e(it["install"])}</pre>' if it.get('install') else ''
    seen = (f'<a class="seen" href="/links/#{it["seen"]}">seen in: {e(SEEN[it["seen"]])}</a>'
            if it.get('seen') else '')
    words = ' '.join([it['name'], it.get('by', ''), it['what'], it.get('good', ''), it.get('kind', '')]).lower()
    return f'''      <li class="card" data-q="{e(words)}">
        <div class="top"><h3><a href="{e(it["url"])}" target="_blank" rel="noopener">{e(it["name"])}</a></h3>{stars}</div>
        <p class="by">{e(it.get("by", ""))}</p>
        <div class="tags">{tags}</div>
        <p>{e(it["what"])}</p>
        <p class="good"><b>Good for:</b> {e(it.get("good", ""))}</p>{install}{seen}
      </li>'''


cats = D['categories']
total = sum(len(c['items']) for c in cats)
index = '\n'.join(f'    <a href="#{c["id"]}">{e(c["name"])} <span>{len(c["items"])}</span></a>' for c in cats)
sections = '\n'.join(f'''  <section class="cat" id="{c["id"]}">
    <div class="cat-head"><h2>{e(c["name"])}</h2><p>{e(c["blurb"])}</p></div>
    <ul class="grid">
{chr(10).join(card(it) for it in c["items"])}
    </ul>
  </section>''' for c in cats)

page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>AI resources · Drip the Cup</title>
<meta name="description" content="The AI tools Drip the Cup talks about and uses: chat assistants, coding agents, Claude Code skills, voice, image and video generation, editing and more. {total} tools, sorted and linked.">
<link rel="canonical" href="https://dripthecup.com/resources/">
<meta property="og:type" content="website">
<meta property="og:url" content="https://dripthecup.com/resources/">
<meta property="og:title" content="AI resources · Drip the Cup">
<meta property="og:description" content="{total} AI tools, sorted by what you're trying to do. The ones we actually use are marked.">
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
    --red:#D63F2A; --dark:#100D09; --line:#D9CFBC;
    --display:'Fraunces', Georgia, 'Times New Roman', serif;
    --body:Georgia, 'Times New Roman', serif;
    --mono:ui-monospace, 'Cascadia Mono', 'Courier New', monospace;
  }}
  *{{box-sizing:border-box;}}
  body{{margin:0;background:var(--paper);color:var(--ink);font-family:var(--body);font-size:16px;line-height:1.55;-webkit-font-smoothing:antialiased;}}
  .wrap{{max-width:1200px;margin:0 auto;padding-inline:20px;}}
  a{{color:inherit;}}
  :focus-visible{{outline:3px solid var(--red);outline-offset:2px;}}
  h1,h2,h3{{text-wrap:balance;margin:0;}}
  .eyebrow{{font-family:var(--mono);font-size:11.5px;letter-spacing:.18em;text-transform:uppercase;color:var(--muted);margin:0;}}
  .hdr{{background:var(--paper);border-bottom:1px solid var(--line);position:sticky;top:env(safe-area-inset-top, 0px);z-index:20;}}
  .hdr .wrap{{display:flex;align-items:center;justify-content:space-between;gap:14px;padding-block:14px;}}
  .brand{{font-family:var(--display);font-weight:900;font-size:24px;letter-spacing:-.02em;text-decoration:none;line-height:1;}}
  .hnav{{display:flex;gap:2px;flex-wrap:wrap;}}
  .hnav a{{font-family:var(--mono);font-size:12px;letter-spacing:.14em;text-transform:uppercase;text-decoration:none;padding:8px 11px;}}
  .hnav a:hover,.hnav a[aria-current]{{background:var(--mustard);}}

  .intro{{display:grid;grid-template-columns:1.4fr 1fr;border-bottom:1px solid var(--line);}}
  .intro-copy{{padding:56px 40px 48px max(20px, calc((100vw - 1200px)/2 + 20px));display:flex;flex-direction:column;justify-content:center;}}
  .intro h1{{font-family:var(--display);font-weight:900;font-size:clamp(34px,4.8vw,62px);line-height:1.02;letter-spacing:-.025em;margin-top:12px;}}
  .intro p.sub{{max-width:48ch;margin:16px 0 0;font-size:17px;color:var(--muted);}}
  .search{{margin-top:24px;display:flex;max-width:460px;border:2px solid var(--ink);background:var(--cup);}}
  .search input{{flex:1;min-width:0;border:0;background:transparent;font:16px var(--mono);padding:13px 14px;color:var(--ink);}}
  .search input:focus{{outline:none;}}
  .search:focus-within{{box-shadow:4px 4px 0 var(--ink);}}
  .stage{{background:var(--mustard);display:flex;align-items:flex-end;justify-content:center;min-height:300px;padding:30px 20px 0;overflow:hidden;}}
  .stage img{{width:min(190px,44vw);height:auto;display:block;}}
  @media (max-width:820px){{.intro{{grid-template-columns:minmax(0,1fr);}} .stage{{order:-1;min-height:0;padding-top:26px;}} .stage img{{width:min(150px,38vw);}} .intro-copy{{padding:28px 20px 34px;}}}}

  .index{{display:flex;flex-wrap:wrap;gap:8px;padding-block:20px;border-bottom:1px solid var(--line);}}
  .index a{{font-family:var(--mono);font-size:12px;letter-spacing:.06em;text-decoration:none;border:1.5px solid var(--ink);padding:8px 12px;background:var(--paper);}}
  .index a span{{color:var(--muted);margin-left:4px;}}
  .index a:hover{{background:var(--ink);color:var(--paper);}}
  .index a:hover span{{color:var(--mustard);}}

  .cat{{padding-block:44px 8px;scroll-margin-top:72px;}}
  .cat-head{{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 20px;margin-bottom:20px;}}
  .cat-head h2{{font-family:var(--display);font-weight:900;font-size:clamp(26px,3vw,36px);letter-spacing:-.02em;}}
  .cat-head p{{margin:0;color:var(--muted);max-width:70ch;}}
  .grid{{list-style:none;margin:0;padding:0;display:grid;grid-template-columns:repeat(auto-fill,minmax(min(100%,270px),1fr));gap:14px;}}
  .card{{background:var(--cup);border:1.5px solid var(--ink);padding:18px 18px 16px;display:flex;flex-direction:column;min-width:0;}}
  .card:hover{{box-shadow:5px 5px 0 var(--ink);}}
  .top{{display:flex;align-items:baseline;gap:10px;}}
  .card h3{{font-family:var(--display);font-weight:900;font-size:23px;letter-spacing:-.01em;}}
  .card h3 a{{text-decoration:none;border-bottom:2px solid var(--mustard);}}
  .card h3 a:hover{{background:var(--mustard);}}
  .stars{{font-family:var(--mono);font-size:12.5px;margin-left:auto;white-space:nowrap;}}
  .by{{font-family:var(--mono);font-size:11.5px;color:var(--muted);margin:2px 0 0;letter-spacing:.04em;}}
  .tags{{display:flex;flex-wrap:wrap;gap:6px;margin-top:8px;}}
  .tags:empty{{display:none;}}
  .kind{{font-family:var(--mono);font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;background:var(--ink);color:var(--paper);padding:3px 7px;}}
  .we{{font-family:var(--mono);font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;background:var(--mustard);padding:3px 7px;border:1px solid var(--ink);}}
  .card p{{margin:10px 0 0;}}
  .card .good{{font-size:14.5px;color:var(--muted);margin-top:auto;padding-top:10px;}}
  .card .good b{{color:var(--ink);font-weight:600;}}
  .card pre{{margin:12px 0 0;background:var(--dark);color:#EDE6D8;padding:10px 12px;overflow-x:auto;font:12.5px/1.5 var(--mono);white-space:pre;}}
  .seen{{display:inline-block;margin-top:12px;font-family:var(--mono);font-size:11.5px;letter-spacing:.06em;text-transform:uppercase;text-decoration:none;border-bottom:1.5px solid var(--ink);align-self:flex-start;}}
  .seen:hover{{background:var(--mustard);}}
  .empty{{font-family:var(--mono);color:var(--muted);padding:40px 0;}}
  .fine{{font-family:var(--mono);font-size:12px;color:var(--muted);padding-block:34px 44px;border-top:1px solid var(--line);margin-top:30px;max-width:80ch;}}
  .foot{{background:var(--dark);color:#CFC4B0;padding-block:30px;font-family:var(--mono);font-size:12px;}}
  .foot a{{color:var(--mustard);}}
</style>
</head>
<body>

<header class="hdr">
  <div class="wrap">
    <a class="brand" href="/">DRIP.</a>
    <nav class="hnav" aria-label="Main">
      <a href="/">Home</a>
      <a href="/resources/" aria-current="page">Resources</a>
      <a href="/links/">From the videos</a>
    </nav>
  </div>
</header>

<section class="intro">
  <div class="intro-copy">
    <p class="eyebrow">Resources · {total} tools</p>
    <h1>The AI tools we talk about, sorted.</h1>
    <p class="sub">Pick what you're trying to do and start there. The ones we actually use to make Drip are marked <b>we use this</b>.</p>
    <label class="search" for="q"><input id="q" type="search" placeholder="Search: voice, video, free, Claude..." autocomplete="off" aria-label="Search the resources"></label>
  </div>
  <div class="stage"><img src="../assets/drip2-curious-a.png" width="420" height="720" alt="Drip, a white paper cup of black coffee, looking curious on the mustard stage."></div>
</section>

<div class="wrap">
  <nav class="index" aria-label="Categories">
{index}
  </nav>

{sections}

  <p class="empty" id="empty" hidden>Nothing matches that yet. Drip is still learning.</p>

  <p class="fine">Last checked {e(D["updated"])}. Star counts are GitHub's on that day. We're not paid by any of these companies; if that ever changes, it'll say so right here. Tools change fast, so check each site for current pricing.</p>
</div>

<footer class="foot">
  <div class="wrap">drip the cup · <a href="/">dripthecup.com</a> · a cup of coffee learning about a.i.</div>
</footer>

<script>
  // search: hide cards that don't match, and categories with nothing left
  const q = document.getElementById('q'), empty = document.getElementById('empty');
  q.addEventListener('input', () => {{
    const terms = q.value.toLowerCase().trim().split(/\\s+/).filter(Boolean);
    let shown = 0;
    document.querySelectorAll('.cat').forEach(cat => {{
      let n = 0;
      cat.querySelectorAll('.card').forEach(c => {{
        const hit = terms.every(t => c.dataset.q.includes(t) || cat.id.includes(t) || cat.querySelector('h2').textContent.toLowerCase().includes(t));
        c.hidden = !hit; if (hit) n++;
      }});
      cat.hidden = n === 0; shown += n;
    }});
    empty.hidden = shown > 0;
  }});
</script>
</body>
</html>
'''
open(os.path.join(HERE, 'index.html'), 'w', encoding='utf8').write(page)
print(f'resources/index.html: {len(cats)} categories, {total} tools')
