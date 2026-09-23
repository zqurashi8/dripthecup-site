"""Match every tool to everyday tasks with Jev, for the "What do you want to do?" finder.

Runs on YOUR computer at build time, so the API key never ships with the website:
    set TYPESAFE_API_KEY in your environment, then
    python resources/jev_tasks.py && python resources/build.py

One Jev request per tool: the tool is the state, and each task is a yes/no (Noul) question.
Jev returns a probability per task; tools at or above THRESHOLD become that task's picks.
Output: resources/tasks.json (safe to commit: it holds only task names, tool ids and scores)."""
import json, os, sys, time, urllib.error, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
API = 'https://api.typesafe.ai/v1/systemone'
THRESHOLD = 0.6
MAX_PER_TASK = 14

TASKS = [
    'Edit a video', 'Make short clips for TikTok or Reels', 'Generate a video from text or a photo',
    'Make a voiceover', 'Make music', 'Transcribe audio or meetings', 'Type faster by talking',
    'Generate images', 'Design a thumbnail, logo or social post', 'Make slides',
    'Build an app or website without coding', 'Write code faster', 'Save tokens and cost in a coding agent',
    'Research a topic with sources', 'Write or improve text', 'Take meeting notes automatically',
    'Clear my inbox faster', 'Plan my day and schedule tasks', 'Manage a team project',
    'Manage customers and sales leads', 'Track business expenses', 'Automate repetitive work between apps',
    'Schedule social media posts', 'Run AI privately on my own computer', 'Put AI inside my own app',
    'Have an AI agent do tasks for me', 'Record a tutorial or demo',
]


def slug(name):
    return 't-' + ''.join(ch if ch.isalnum() else '-' for ch in name.lower()).strip('-')


def ask(key, tool, cat):
    body = {
        'model': 'jev-latest',
        'state': {'tool': tool['name'], 'made_by': tool.get('by', ''), 'what_it_is_best_for': tool['best'],
                  'type': tool.get('kind', ''), 'category': cat['name']},
        'questions': {f'q{i}': {'type': 'noul', 'instructions':
                                f'Would this tool be a strong, directly useful choice for someone who wants to: "{t}"? '
                                'Answer yes only if helping with that is one of the main things this tool does.'}
                      for i, t in enumerate(TASKS)},
    }
    req = urllib.request.Request(API, data=json.dumps(body).encode(), method='POST',
                                 headers={'Authorization': f'Bearer {key}', 'Content-Type': 'application/json'})
    for attempt in range(5):
        try:
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())['answers']
        except urllib.error.HTTPError as e:
            if e.code in (429, 529, 500, 502, 503):
                time.sleep(2 ** attempt); continue
            raise SystemExit(f'Jev error {e.code}: {e.read()[:300]!r}')
    raise SystemExit('Jev kept refusing (rate limit); try again in a minute.')


def main():
    key = os.environ.get('TYPESAFE_API_KEY')
    if not key:
        sys.exit('Set TYPESAFE_API_KEY first (your TypeSafe API key). It is only used on this computer.')
    data = json.load(open(os.path.join(HERE, 'resources.json'), encoding='utf8'))
    picks = {t: [] for t in TASKS}
    tokens = 0
    for cat in data['categories']:
        for tool in cat['items']:
            ans = ask(key, tool, cat)
            for i, t in enumerate(TASKS):
                p = ans[f'q{i}']['noul']
                if p >= THRESHOLD:
                    picks[t].append({'id': slug(tool['name']), 'p': round(p, 3)})
            print(f"  {tool['name']:28s} fits {sum(1 for i in range(len(TASKS)) if ans[f'q{i}']['noul'] >= THRESHOLD)} tasks")
    out = {'model': 'jev-latest', 'threshold': THRESHOLD, 'made': time.strftime('%Y-%m-%d'),
           'tasks': [{'task': t, 'tools': sorted(v, key=lambda x: -x['p'])[:MAX_PER_TASK]} for t, v in picks.items() if v]}
    json.dump(out, open(os.path.join(HERE, 'tasks.json'), 'w', encoding='utf8'), indent=1)
    print(f"tasks.json: {len(out['tasks'])} tasks, {sum(len(t['tools']) for t in out['tasks'])} matches")


if __name__ == '__main__':
    main()
