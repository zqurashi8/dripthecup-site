"""Build the video pages from links/videos.json.

    python links/build.py

Writes links/index.html (a section per video: player, summary, every link) and refreshes two
blocks on the homepage between their markers: the videos carousel (<!-- VIDEOS:START/END -->)
and the AI tools snippet (<!-- TOOLS:START/END -->, counts and picks read from
resources/resources.json). Add a video = add an entry to videos.json and run this.
YouTube thumbnails are downloaded once into links/thumbs/."""
import html, json, os, re, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
V = json.load(open(os.path.join(HERE, 'videos.json'), encoding='utf8'))['videos']
R = json.load(open(os.path.join(ROOT, 'resources', 'resources.json'), encoding='utf8'))
e = html.escape
THUMBS = os.path.join(HERE, 'thumbs')


def thumb(v):
    """Local thumbnail path (relative to links/). Shorts get YouTube's vertical frame."""
    if not v.get('youtube'):
        return v['poster']
    os.makedirs(THUMBS, exist_ok=True)
    path = os.path.join(THUMBS, v['id'] + '.jpg')
    if not os.path.exists(path):
        names = ['oar2', 'oardefault', 'hqdefault'] if v['kind'] == 'Short' else ['maxresdefault', 'hqdefault']
        for n in names:
            try:
                with urllib.request.urlopen(f'https://i.ytimg.com/vi/{v["youtube"]}/{n}.jpg', timeout=20) as r:
                    open(path, 'wb').write(r.read()); break
            except Exception:
                continue
        try:  # keep them light
            from PIL import Image
            im = Image.open(path).convert('RGB'); im.thumbnail((720, 720)); im.save(path, quality=82)
        except Exception:
            pass
    return f'thumbs/{v["id"]}.jpg'


NAV = '''<header class="hdr"><div class="in">
  <a class="brand" href="/">DRIP.</a>
  <nav class="hnav" aria-label="Main">
    <a href="/">Home</a>
    <a href="/links/"{v}>Videos</a>
    <a href="/resources/"{r}>AI tools</a>
    <a href="/#shop">Shop</a>
  </nav>
</div></header>'''


def player(v):
    if v.get('youtube'):
        ratio = 'short' if v['kind'] == 'Short' else 'wide'
        return (f'<div class="player {ratio}"><iframe src="https://www.youtube-nocookie.com/embed/{v["youtube"]}" title="{e(v["title"])}" loading="lazy" '
                'allow="accelerometer; clipboard-write; encrypted-media; gyroscope; picture-in-picture; web-share" '
                'referrerpolicy="strict-origin-when-cross-origin" allowfullscreen></iframe></div>'
                f'<a class="yt" href="https://www.youtube.com/{"shorts/" if v["kind"] == "Short" else "watch?v="}{v["youtube"]}" target="_blank" rel="noopener">Watch on YouTube ↗</a>')
    return f'<div class="player short"><video src="{v["mp4"]}" poster="{v["poster"]}" controls playsinline preload="none"></video></div><p class="yt soon">On YouTube soon</p>'


def link(l):
    stars = f'<span class="stars">★ {e(l["stars"])}</span>' if l.get('stars') else ''
    inst = f'<pre>{e(l["install"])}</pre>' if l.get('install') else ''
    src = f' <a href="{e(l["source"]["url"])}" target="_blank" rel="noopener">{e(l["source"]["label"])}</a>.' if l.get('source') else ''
    return f'''        <li class="tool"><div class="tool-top"><h3><a href="{e(l["url"])}" target="_blank" rel="noopener">{e(l["name"])}</a></h3><span class="kind">{e(l["kind"])}</span>{stars}</div>
          <p>{e(l["what"])}{src}</p>{inst}</li>'''


sections = '\n'.join(f'''  <article class="ep" id="{v["id"]}">
    <div class="clip">{player(v)}<p class="date">{e(v["kind"])} · {e(v["date"])} · {e(v["length"])}</p></div>
    <div class="body">
      <p class="eyebrow">{e(v["topic"])}</p>
      <h2>{e(v["title"])}</h2>
      <h3 class="sumh">What it covers</h3>
      <p class="lede">{e(v["summary"])}</p>
      <h3 class="sumh">Everything we mentioned</h3>
      <ul class="tools">
{chr(10).join(link(l) for l in v["links"])}
      </ul>{f'<a class="more" href="{e(v["more"]["url"])}">{e(v["more"]["label"])} →</a>' if v.get("more") else ''}
    </div>
  </article>''' for v in V)
jump = '\n'.join(f'    <a href="#{v["id"]}"><img src="{thumb(v)}" alt="" loading="lazy"><span>{e(v["title"])}</span></a>' for v in V)

page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>Videos · Drip the Cup</title>
<meta name="description" content="Every Drip the Cup video with a short summary and every tool, repo and source we mentioned, linked.">
<link rel="canonical" href="https://dripthecup.com/links/">
<meta property="og:type" content="website">
<meta property="og:url" content="https://dripthecup.com/links/">
<meta property="og:title" content="Videos · Drip the Cup">
<meta property="og:description" content="Every video, summarized, with everything we mentioned linked.">
<meta property="og:image" content="https://dripthecup.com/assets/og.jpg">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#E3AC2A">
<link rel="icon" href="../assets/favicon-32.png" sizes="32x32">
<link rel="apple-touch-icon" href="../assets/apple-touch-icon.png">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Fraunces:opsz,wght@9..144,400;9..144,600;9..144,900&display=swap">
<style>
  :root{{--mustard:#E3AC2A;--paper:#F6EFE0;--cup:#F5F1E8;--ink:#1A1A1A;--muted:#6B6155;--red:#D63F2A;--dark:#100D09;--line:#D9CFBC;
    --display:'Fraunces',Georgia,'Times New Roman',serif;--body:Georgia,'Times New Roman',serif;--mono:ui-monospace,'Cascadia Mono','Courier New',monospace;}}
  *{{box-sizing:border-box;}}
  html{{scroll-padding-top:70px;}}
  body{{margin:0;background:var(--paper);color:var(--ink);font-family:var(--body);font-size:16px;line-height:1.6;-webkit-font-smoothing:antialiased;}}
  a{{color:inherit;}}
  :focus-visible{{outline:3px solid var(--red);outline-offset:2px;}}
  h1,h2,h3{{text-wrap:balance;margin:0;}}
  .wrap{{max-width:1120px;margin:0 auto;padding-inline:20px;}}
  .eyebrow{{font-family:var(--mono);font-size:11.5px;letter-spacing:.18em;text-transform:uppercase;color:var(--muted);margin:0;}}
  .hdr{{background:var(--paper);border-bottom:1px solid var(--line);position:sticky;top:env(safe-area-inset-top,0px);z-index:20;}}
  @media (max-width:900px){{.hdr{{position:static;}} html{{scroll-padding-top:12px;}}}} /* phones: header scrolls away */
  .hdr .in{{max-width:1120px;margin:0 auto;padding:12px 20px;display:flex;align-items:center;justify-content:space-between;gap:12px;}}
  .brand{{font-family:var(--display);font-weight:900;font-size:22px;letter-spacing:-.02em;text-decoration:none;line-height:1;}}
  .hnav{{display:flex;gap:2px;flex-wrap:wrap;}}
  .hnav a{{font-family:var(--mono);font-size:11.5px;letter-spacing:.12em;text-transform:uppercase;text-decoration:none;padding:7px 10px;}}
  .hnav a:hover,.hnav a[aria-current]{{background:var(--mustard);}}
  .intro{{padding-block:40px 20px;}}
  .intro h1{{font-family:var(--display);font-weight:900;font-size:clamp(32px,4.4vw,54px);line-height:1.02;letter-spacing:-.025em;margin-top:10px;}}
  .intro p{{color:var(--muted);max-width:60ch;margin:12px 0 0;}}
  .jump{{display:flex;gap:12px;overflow-x:auto;padding-block:18px 22px;border-bottom:1px solid var(--line);scroll-snap-type:x mandatory;}}
  .jump a{{flex:none;width:150px;text-decoration:none;scroll-snap-align:start;}}
  .jump img{{width:150px;height:200px;object-fit:cover;display:block;border:2px solid var(--ink);background:var(--dark);}}
  .jump a:hover img{{box-shadow:4px 4px 0 var(--ink);}}
  .jump span{{display:block;font-size:13.5px;line-height:1.3;margin-top:8px;}}
  .ep{{display:grid;grid-template-columns:300px minmax(0,1fr);gap:40px;padding-block:48px;border-bottom:1px solid var(--line);}}
  @media (max-width:820px){{.ep{{grid-template-columns:minmax(0,1fr);gap:22px;padding-block:34px;}}}}
  .ep > *{{min-width:0;}}
  .player{{border:3px solid var(--ink);box-shadow:6px 6px 0 var(--ink);background:var(--dark);}}
  .player.short{{aspect-ratio:9/16;max-width:300px;}}
  .player.wide{{aspect-ratio:16/9;}}
  .player iframe,.player video{{width:100%;height:100%;border:0;display:block;}}
  @media (max-width:820px){{.player.short{{max-width:260px;margin-inline:auto;}}}}
  .yt{{display:inline-block;margin-top:14px;font-family:var(--mono);font-size:12px;letter-spacing:.08em;text-transform:uppercase;}}
  .yt.soon{{color:var(--muted);}}
  .date{{font-family:var(--mono);font-size:12px;color:var(--muted);margin:6px 0 0;}}
  .ep h2{{font-family:var(--display);font-weight:900;font-size:clamp(26px,3vw,36px);line-height:1.05;letter-spacing:-.02em;margin-top:8px;}}
  .sumh{{font-family:var(--mono);font-size:11px;letter-spacing:.16em;text-transform:uppercase;color:var(--muted);font-weight:400;margin-top:22px;}}
  .lede{{margin:8px 0 0;max-width:65ch;}}
  .tools{{list-style:none;margin:10px 0 0;padding:0;display:grid;grid-template-columns:minmax(0,1fr);gap:10px;}}
  .tool{{background:var(--cup);border:1.5px solid var(--ink);padding:14px 16px;}}
  .tool-top{{display:flex;flex-wrap:wrap;align-items:baseline;gap:6px 12px;}}
  .tool h3{{font-family:var(--display);font-weight:900;font-size:20px;}}
  .tool h3 a{{text-decoration:none;border-bottom:2px solid var(--mustard);}}
  .tool h3 a:hover{{background:var(--mustard);}}
  .kind{{font-family:var(--mono);font-size:10.5px;letter-spacing:.12em;text-transform:uppercase;background:var(--ink);color:var(--paper);padding:2px 7px;}}
  .stars{{font-family:var(--mono);font-size:12.5px;margin-left:auto;}}
  .tool p{{margin:6px 0 0;font-size:15px;}}
  .tool pre{{margin:10px 0 0;background:var(--dark);color:#EDE6D8;padding:10px 12px;overflow-x:auto;font:12.5px/1.5 var(--mono);white-space:pre;}}
  .more{{display:inline-block;margin-top:16px;font-family:var(--mono);font-size:12px;letter-spacing:.08em;text-transform:uppercase;border-bottom:1.5px solid var(--ink);text-decoration:none;}}
  .more:hover{{background:var(--mustard);}}
  .foot{{background:var(--dark);color:#CFC4B0;padding:28px 20px;font-family:var(--mono);font-size:12px;text-align:center;}}
  .foot a{{color:var(--mustard);margin:0 8px;}}
</style>
</head>
<body>

{NAV.format(v=' aria-current="page"', r='')}

<div class="wrap">
  <section class="intro">
    <p class="eyebrow">Videos · {len(V)} so far</p>
    <h1>Every video, and everything we mentioned in it.</h1>
    <p>A short summary of each one, the video itself, and a link to every tool, repo and source. Newest first.</p>
  </section>
  <nav class="jump" aria-label="Jump to a video">
{jump}
  </nav>
{sections}
</div>

<footer class="foot"><a href="/">Home</a>·<a href="/resources/">AI tools</a>·<a href="/#shop">Shop</a>·<a href="https://www.youtube.com/@dripthecup" target="_blank" rel="noopener">YouTube</a>·<a href="https://www.tiktok.com/@dripthecup" target="_blank" rel="noopener">TikTok</a>·<a href="https://www.instagram.com/dripthecup/" target="_blank" rel="noopener">Instagram</a></footer>

</body>
</html>
'''
open(os.path.join(HERE, 'index.html'), 'w', encoding='utf8').write(page)

# ---------- homepage blocks ----------
cards = '\n'.join(f'''        <a class="vcard {'wide' if v['kind'] != 'Short' else ''}" href="/links/#{v["id"]}">
          <img src="links/{thumb(v)}" alt="" loading="lazy">
          <span class="vmeta"><span class="vtag">{e(v["kind"])} · {e(v["topic"])}</span><b>{e(v["title"])}</b><small>Summary + links →</small></span>
        </a>''' for v in V)
videos_block = f'''<!-- VIDEOS:START (generated by links/build.py) -->
<section class="sec" id="watch">
  <div class="wrap">
    <div class="sec-head">
      <div>
        <p class="eyebrow">Freshly brewed</p>
        <h2>Every video, with the links</h2>
      </div>
      <div class="vnav"><button type="button" class="vbtn" data-dir="-1" aria-label="Previous videos">←</button><button type="button" class="vbtn" data-dir="1" aria-label="More videos">→</button><a class="btn btn-outline" href="/links/">All videos</a></div>
    </div>
    <div class="vrow" id="vrow">
{cards}
    </div>
  </div>
  <script>document.querySelectorAll('.vbtn').forEach(b=>b.addEventListener('click',()=>{{const r=document.getElementById('vrow');r.scrollBy({{left:+b.dataset.dir*r.clientWidth*0.8,behavior:'smooth'}});}}));</script>
</section>
<!-- VIDEOS:END -->'''
cats = R['categories']
total = sum(len(c['items']) for c in cats)
chips = '\n'.join(f'        <a href="/resources/#{c["id"]}">{c["icon"]} {e(c["name"])}</a>' for c in cats)
tops = [it for c in cats for it in c['items'] if it.get('top')][:8]
tools_block = f'''<!-- TOOLS:START (generated by links/build.py) -->
<section class="sec tools-snip" id="tools">
  <div class="wrap">
    <div class="sec-head">
      <div>
        <p class="eyebrow">Free directory · {total} tools · {len(cats)} categories</p>
        <h2>Find the right AI tool, fast</h2>
      </div>
      <a class="btn btn-primary" href="/resources/">Open the AI tools directory</a>
    </div>
    <p class="snip-sub">Everything we talk about in the videos and more, sorted by what you're trying to do. Tell it the job and Jev picks the tools.</p>
    <div class="snip-picks">
{chr(10).join(f'      <a href="/resources/#t-{"".join(ch if ch.isalnum() else "-" for ch in it["name"].lower()).strip("-")}"><b>{e(it["name"])}</b><span>{e(it["best"])}</span></a>' for it in tops)}
    </div>
    <div class="snip-cats">
{chips}
    </div>
  </div>
</section>
<!-- TOOLS:END -->'''
hp = os.path.join(ROOT, 'index.html')
h = open(hp, encoding='utf8').read()
h = re.sub(r'<!-- VIDEOS:START.*?<!-- VIDEOS:END -->', lambda m: videos_block, h, flags=re.S)
h = re.sub(r'<!-- TOOLS:START.*?<!-- TOOLS:END -->', lambda m: tools_block, h, flags=re.S)
open(hp, 'w', encoding='utf8').write(h)
print(f'links/index.html: {len(V)} videos; homepage: carousel + tools snippet ({total} tools) refreshed')
