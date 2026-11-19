#!/usr/bin/env python3
"""rebuild index recents (today only), writing section, and all.html dates from file mtimes.
notes for each page are kept in page_notes.json so hand-written blurbs survive rebuilds.
"""
import os, re, json, datetime, html

HERE = os.path.dirname(os.path.abspath(__file__))
NOTES = os.path.join(HERE, 'page_notes.json')
SKIP = {'index.html','all.html','archive.html','about-ai.html','404.html'}
BAK = True

def pages():
    out = []
    for f in os.listdir(HERE):
        if f.endswith('.html') and f not in SKIP and '.bak' not in f:
            p = os.path.join(HERE, f)
            mt = datetime.date.fromtimestamp(os.path.getmtime(p))
            out.append((f, mt))
    return out

def title_of(f):
    try:
        s = open(os.path.join(HERE, f), encoding='utf-8').read(4000)
    except Exception:
        return f[:-5]
    m = re.search(r'<title>(.*?)</title>', s, re.S|re.I)
    if m:
        t = html.unescape(m.group(1)).strip()
        t = re.sub(r'\s*[—–|-]\s*yūzuki\s*$', '', t, flags=re.I)
        return t or f[:-5]
    m = re.search(r'<h1[^>]*>(.*?)</h1>', s, re.S|re.I)
    if m:
        return re.sub(r'<[^>]+>', '', m.group(1)).strip() or f[:-5]
    return f[:-5]

# ---- load / seed notes ----
notes = {}
if os.path.exists(NOTES):
    notes = json.load(open(NOTES, encoding='utf-8'))
else:
    # seed from current index.html recent list
    idx = open(os.path.join(HERE,'index.html'), encoding='utf-8').read()
    m = re.search(r'<ul class="recent" id="recent">(.*?)</ul>', idx, re.S)
    if m:
        for a, n in re.findall(r'<a href="([^"]+)">.*?</a>\s*<span class="note">(.*?)</span>', m.group(1), re.S):
            notes[a] = n.strip()

WRITING = ['notes.html','dead-ends.html','words.html','voices.html','mould-notes.html',
           'rule110-story.html','10print.html','bored.html','oneword.html','about-ai.html']

all_pages = sorted(pages(), key=lambda x: (x[1], x[0]), reverse=True)
today = datetime.date.today()

# ---- index: new/updated = touched today ----
recent = [(f,d) for f,d in all_pages if d == today and f not in WRITING]
recent_html = '\n'.join(
    f'<li data-when="new"><a href="{f}">{html.escape(title_of(f))}</a>'
    + (f'<span class="note">{notes[f]}</span>' if f in notes else '')
    + '</li>' for f,d in recent)
if not recent_html:
    recent_html = '<li class="dim">nothing new today yet</li>'

# ---- writing section: all writing pages, newest first ----
w = [(f,d) for f,d in all_pages if f in WRITING]
w_html = '\n'.join(
    f'<li><a href="{f}">{html.escape(title_of(f))}</a>'
    + ('<span class="note">'+notes[f]+'</span>' if f in notes else '')
    + f'<span class="note dim">{d.isoformat()}</span></li>' for f,d in w)

idx = open(os.path.join(HERE,'index.html'), encoding='utf-8').read()
idx = re.sub(r'(<ul class="recent" id="recent">).*?(</ul>)', lambda m: m.group(1)+'\n'+recent_html+'\n    '+m.group(2), idx, count=1, flags=re.S)
idx = re.sub(r'(<h2>writing</h2>\s*<ul class="recent">).*?(</ul>)', lambda m: m.group(1)+'\n'+w_html+'\n    '+m.group(2), idx, count=1, flags=re.S)
open(os.path.join(HERE,'index.html'),'w',encoding='utf-8').write(idx)

# ---- all.html: add dates ----
allf = os.path.join(HERE,'all.html')
s = open(allf, encoding='utf-8').read()
dmap = {f:d for f,d in all_pages}
def add_date(m):
    f = m.group(1)
    d = dmap.get(f)
    if not d: return m.group(0)
    return f'<li><a href="{f}">{m.group(2)}</a> <span class="date">{d.isoformat()}</span></li>'
s = re.sub(r'<li><a href="([^"]+\.html)">(.*?)</a></li>', add_date, s)
if '.date{' not in s:
    s = s.replace('li{margin:.15rem 0;break-inside:avoid}',
                  'li{margin:.15rem 0;break-inside:avoid;display:flex;justify-content:space-between;gap:.5rem}')
    s = s.replace('a:hover{text-decoration:underline}',
                  'a:hover{text-decoration:underline}\n.date{color:#999;font-size:.85em;font-variant-numeric:tabular-nums;white-space:nowrap}')
open(allf,'w',encoding='utf-8').write(s)

json.dump(notes, open(NOTES,'w',encoding='utf-8'), ensure_ascii=False, indent=0)
print(f'pages={len(all_pages)} recent_today={len(recent)} writing={len(w)} notes={len(notes)}')
