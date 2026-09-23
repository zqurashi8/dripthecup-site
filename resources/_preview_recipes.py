"""MOCKUP ONLY (not deployed): injects a Recipes section into a copy of resources/index.html
-> resources/_preview-recipes.html, to review the idea before building it for real."""
import html, json, os
from urllib.parse import urlparse

HERE = os.path.dirname(os.path.abspath(__file__))
D = json.load(open(os.path.join(HERE, 'resources.json'), encoding='utf8'))
TASKS = json.load(open(os.path.join(HERE, 'tasks.json'), encoding='utf8'))['tasks']
e = html.escape
BY = {it['name']: it for c in D['categories'] for it in c['items']}


def icon(name):
    u = urlparse(BY[name]['url'])
    if u.netloc == 'github.com':
        return f'icons/gh-{u.path.strip("/").split("/")[0].lower()}.png'
    return f'icons/{u.netloc.replace("www.", "")}.png'


def slug(name):
    return 't-' + ''.join(ch if ch.isalnum() else '-' for ch in name.lower()).strip('-')


# steps: (tool, what you do there, alternatives)
RECIPES = [
    {'id': 'shorts', 'title': 'Turn one long video into Shorts', 'task': 'Cut a long video into short clips for TikTok or Reels',
     'for': 'podcasts, streams, webinars', 'steps': [
        ('Descript', 'Drop in the video. Get a transcript and cut the ums and dead air by editing text.', ['DaVinci Resolve']),
        ('Opus Clip', 'Upload the cleaned edit. It suggests the 30 to 60 second moments most likely to hold attention.', ['CapCut']),
        ('CapCut', 'Open each clip: auto captions, a hook line on screen, reframe to 9:16.', ['Descript', 'Submagic']),
        ('Blotato', 'Schedule the clips to TikTok, Reels and Shorts from one place.', ['Buffer', 'Metricool']),
     ], 'proof': 'slot', 'prompt': None},
    {'id': 'photo-video', 'title': 'Make an AI video from one photo', 'task': 'Generate a video from text or a photo',
     'for': 'ads, product shots, character clips', 'steps': [
        ('Nano Banana Pro', 'Make or fix the still first. The video can only be as good as the frame it starts from.', ['GPT Image 2', 'Midjourney']),
        ('Kling 3.0', 'Image to video: describe the motion, not the scene (it can already see the scene).', ['Higgsfield', 'Veo']),
        ('ElevenLabs', 'Add a voiceover or sound effects.', ['Murf']),
        ('CapCut', 'Stitch the shots, add music and captions.', ['Descript']),
     ], 'proof': 'slot',
     'prompt': ('Kling 3.0', 'Slow push-in toward the subject. The subject turns their head to camera and smiles. Hair moves in a light breeze. Everything else stays still. Natural lighting, no cuts.')},
    {'id': 'explainer', 'title': 'A faceless explainer with a voice', 'task': 'Make a voiceover',
     'for': 'how we make the Drip the Cup videos', 'ours': True, 'steps': [
        ('Claude', 'Write the script as a conversation: one question, the wrong answer, then the real one.', ['ChatGPT']),
        ('ElevenLabs', 'Give each character their own voice and record the lines.', ['Fish Audio']),
        ('whisper.cpp', 'Get the exact time of every spoken word, free and on your own computer.', []),
        ('Remotion', 'Animate in code, with every caption and card keyed to a spoken word.', ['CapCut']),
     ], 'proof': 'ours', 'prompt': None},
    {'id': 'meetings', 'title': 'Never write meeting notes again', 'task': 'Take meeting notes automatically',
     'for': 'calls, interviews, team meetings', 'steps': [
        ('Granola', 'Runs on your computer during the call, no bot joins. Type a few rough notes if you like.', ['Otter', 'Fathom']),
        ('Claude', 'Paste the notes: ask for decisions, owners and next steps as a list.', ['ChatGPT']),
        ('Notion', 'Keep every meeting in one searchable place.', ['Obsidian']),
     ], 'proof': None, 'prompt': None},
    {'id': 'receipts', 'title': 'Receipts to books without typing', 'task': 'Track business expenses',
     'for': 'small businesses, freelancers', 'steps': [
        ('Expensify', 'Snap each receipt with your phone. It reads the amount and merchant.', ['Ramp']),
        ('QuickBooks', 'Connect it once. Expenses land in your books, sorted.', []),
     ], 'proof': None, 'prompt': None},
    {'id': 'automate', 'title': 'Copy-paste between apps, automated', 'task': 'Automate repetitive work between apps',
     'for': 'forms, leads, reports', 'steps': [
        ('Zapier', 'Pick the trigger (a new form entry, a new email) and the app it should land in.', ['Make', 'n8n']),
        ('Claude', 'Add an AI step in the middle to summarise, sort or draft a reply.', ['ChatGPT']),
     ], 'proof': None, 'prompt': None},
]


def chain(r):
    return '<span class="arr">→</span>'.join(f'<img src="{icon(t)}" alt="{e(t)}" title="{e(t)}" width="26" height="26">' for t, _, _ in r['steps'])


def card(r, open_=False):
    steps = ''
    for i, (t, what, alts) in enumerate(r['steps'], 1):
        alt = (' <span class="alt">or ' + ', '.join(f'<a href="#{slug(a)}">{e(a)}</a>' for a in alts if a in BY) + '</span>') if alts else ''
        steps += f'''<li><span class="sn">{i}</span><img src="{icon(t)}" alt="" width="30" height="30"><div><a class="st" href="{e(BY[t]['url'])}" target="_blank" rel="noopener">{e(t)} ↗</a>{alt}<p>{e(what)}</p></div></li>'''
    proof = ''
    if r['proof'] == 'slot':
        proof = '''<div class="proof"><b>SEE IT IN ACTION</b><div class="pslot"><div class="pthumb">▶</div><div><span>a real post showing the result, linked, with the creator's handle</span><small>@creator on X · opens on x.com</small></div></div><p class="mocknote">mockup: this slot gets 1 or 2 real, credited posts per recipe</p></div>'''
    elif r['proof'] == 'ours':
        proof = '''<div class="proof"><b>MADE WITH THIS RECIPE</b><a class="pslot" href="/links/#ai-tools-directory"><img src="../links/videos/ai-tools-directory.jpg" alt="" class="pimg"><div><span>191 AI tools, and Jev picks the right one for you</span><small>Drip the Cup · 56s short</small></div></a></div>'''
    prompt = ''
    if r.get('prompt'):
        t, p = r['prompt']
        prompt = f'''<div class="prompt"><b>FIRST PROMPT FOR {e(t.upper())}</b><pre>{e(p)}</pre><button type="button" class="copy">Copy</button></div>'''
    ours = '<span class="ours">how we make our videos</span>' if r.get('ours') else ''
    return f'''<details class="rc" id="r-{r['id']}" data-task="{e(r['task'])}"{' open' if open_ else ''}><summary>
      <span class="rt">{e(r['title'])}{ours}</span><span class="rf">for {e(r['for'])} · {len(r['steps'])} steps</span><span class="chain">{chain(r)}</span></summary>
      <div class="rb"><ol>{steps}</ol>{proof}{prompt}</div></details>'''


CSS = '''
  /* ── MOCKUP: recipes ── */
  .recipes{max-width:1240px;margin:0 auto;padding:8px 20px 22px;}
  .recipes h2{font-family:var(--display);font-weight:900;font-size:22px;}
  .recipes h2 small{font-family:var(--mono);font-size:11px;font-weight:400;color:var(--muted);letter-spacing:.08em;margin-left:8px;}
  .rgrid{display:grid;grid-template-columns:repeat(auto-fill,minmax(340px,1fr));gap:12px;margin-top:10px;align-items:start;}
  .rc{border:2px solid var(--ink);background:var(--cup);box-shadow:4px 4px 0 var(--ink);}
  .rc[open]{grid-column:1/-1;}
  .rc summary{list-style:none;cursor:pointer;padding:14px 16px;display:grid;gap:6px;}
  .rc summary::-webkit-details-marker{display:none;}
  .rc summary:hover{background:var(--hover);}
  .rc[open] summary{background:var(--mustard);border-bottom:2px solid var(--ink);}
  .rt{font-family:var(--display);font-weight:900;font-size:19px;line-height:1.15;}
  .ours{display:inline-block;margin-left:8px;vertical-align:middle;font:10px var(--mono);letter-spacing:.08em;text-transform:uppercase;background:var(--ink);color:var(--paper);padding:2px 6px;}
  .rf{font-family:var(--mono);font-size:11px;color:var(--muted);}
  .rc[open] .rf{color:var(--ink);}
  .chain{display:flex;align-items:center;gap:6px;flex-wrap:wrap;}
  .chain img{border-radius:6px;background:#fff;border:1px solid var(--line);}
  .arr{font-family:var(--mono);color:var(--muted);}
  .rb{padding:6px 16px 16px;display:grid;grid-template-columns:minmax(0,1.4fr) minmax(0,1fr);gap:18px;}
  .rb ol{list-style:none;margin:0;padding:0;grid-row:span 2;}
  .rb li{display:grid;grid-template-columns:26px 30px minmax(0,1fr);gap:10px;align-items:start;padding:10px 0;border-bottom:1px solid var(--line);}
  .rb li img{border-radius:6px;background:#fff;}
  .sn{font:700 13px var(--mono);width:24px;height:24px;border:2px solid var(--ink);display:flex;align-items:center;justify-content:center;background:var(--paper);}
  .st{font-family:var(--display);font-weight:600;font-size:16px;text-decoration:none;}
  .st:hover{background:var(--mustard);}
  .alt{font-family:var(--mono);font-size:11px;color:var(--muted);margin-left:6px;}
  .alt a{color:var(--muted);}
  .rb li p{margin:3px 0 0;font-size:14px;}
  .proof, .prompt{border:1.5px solid var(--ink);background:var(--paper);padding:12px;align-self:start;}
  .proof b, .prompt b{font:11px var(--mono);letter-spacing:.14em;}
  .pslot{display:flex;gap:10px;align-items:center;margin-top:8px;text-decoration:none;}
  .pthumb{width:64px;height:84px;flex:none;background:var(--dark);color:var(--mustard);display:flex;align-items:center;justify-content:center;font-size:22px;}
  .pimg{width:64px;height:112px;object-fit:cover;flex:none;border:1.5px solid var(--ink);}
  .pslot span{display:block;font-size:14px;}
  .pslot small{display:block;font:11px var(--mono);color:var(--muted);margin-top:3px;}
  .mocknote{font:10.5px var(--mono);color:var(--red);margin:8px 0 0;}
  .prompt pre{white-space:pre-wrap;background:var(--dark);color:#EDE6D8;font:12.5px/1.5 var(--mono);padding:10px;margin:8px 0;}
  .copy{font:600 11px var(--mono);letter-spacing:.08em;text-transform:uppercase;border:2px solid var(--ink);background:var(--mustard);padding:6px 12px;cursor:pointer;}
  .jev-out .recipe-hint{display:flex;align-items:center;gap:8px;border:2px solid var(--ink);background:var(--mustard);color:var(--ink);padding:8px 12px;font:600 12.5px var(--mono);text-decoration:none;box-shadow:3px 3px 0 var(--ink);}
  .mockbar{background:var(--red);color:#fff;font:12px var(--mono);text-align:center;padding:8px;letter-spacing:.08em;}
  @media (max-width:640px){
    .rgrid{grid-template-columns:minmax(0,1fr);}
    .rb{grid-template-columns:minmax(0,1fr);}
    .rb ol{grid-row:auto;}
  }
'''

cards = '\n'.join(card(r, open_=(r['id'] == 'shorts')) for r in RECIPES)
section = f'''<section class="recipes" id="recipes" aria-label="Recipes">
  <h2>Recipes<small>the tools in order, for one goal</small></h2>
  <div class="rgrid">
{cards}
  </div>
</section>
'''
JS = '''
<script>
  // MOCKUP: a task that has a recipe shows it first, above Jev's ranked tools
  const RECIPE_BY_TASK = {}; document.querySelectorAll('.rc').forEach(r => RECIPE_BY_TASK[r.dataset.task] = r);
  new MutationObserver(() => {
    const o = document.getElementById('jevout'); if (o.hidden || o.querySelector('.recipe-hint')) return;
    const b = document.querySelector('.tasks button[aria-pressed="true"]'); if (!b) return;
    const r = RECIPE_BY_TASK[b.textContent]; if (!r) return;
    const a = document.createElement('a'); a.className = 'recipe-hint'; a.href = '#' + r.id;
    a.textContent = 'Start with a recipe: ' + r.querySelector('.rt').firstChild.textContent + ' →';
    a.onclick = () => { r.open = true; }; o.prepend(a);
  }).observe(document.getElementById('jevout'), {attributes: true, childList: true});
  document.querySelectorAll('.copy').forEach(b => b.onclick = () => { navigator.clipboard?.writeText(b.previousElementSibling.textContent); b.textContent = 'Copied'; });
</script>
'''
page = open(os.path.join(HERE, 'index.html'), encoding='utf8').read()
page = page.replace('</style>', CSS + '</style>', 1)
page = page.replace('<body>', '<body>\n<div class="mockbar">MOCKUP · RECIPES PREVIEW · NOT LIVE</div>', 1)
page = page.replace('<div class="layout">', section + '<div class="layout">', 1)
page = page.replace('</body>', JS + '</body>', 1)
open(os.path.join(HERE, '_preview-recipes.html'), 'w', encoding='utf8').write(page)
print('wrote resources/_preview-recipes.html')
