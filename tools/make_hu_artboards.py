"""Create the Hungarian artboards (X-HU.dc.html) from the English ones, using hu.json.

Also adds the language switch link to the navigation of both versions.
Usage: python3 make_hu_artboards.py <artboard_dir>
"""
import json, os, re, sys

SRC = sys.argv[1]
HERE = os.path.dirname(os.path.abspath(__file__))
HU = json.load(open(os.path.join(HERE, 'hu.json'), encoding='utf-8'))
PAGES = ['Main.dc.html', 'HealthCheck.dc.html', 'Privacy.dc.html']
KEEP = re.compile(r'(?s)^(A\. Krisztina Juhász|\d+|[.;]|ITSM Health Check|itsmexperthungary@gmail\.com|ugyfelszolgalat@naih\.hu|www\.naih\.hu|ITIL 4 .*|GitHub, Inc\., 88 Colin.*|English|Magyar|PeopleCert|Microsoft|Microsoft · A[BZ]-\d+|Microsoft Certified: .*|.* badge|ITSM Health Check – A\. Krisztina Juhász|←|→)$')
NAV = re.compile(r'(<nav aria-label="Main"[^>]*>\n)')
MISSING = set()

def hu_name(name):
    return name.replace('.dc.html', '-HU.dc.html')

def switch(href, label, lang):
    return (f'<a href="{href}" lang="{lang}" hreflang="{lang}" '
            f'style="color: #444650; text-decoration: none; font-weight: 600">{label}</a>\n')

def tr_text(m):
    raw = m.group(1)
    t = raw.strip()
    if not t:
        return m.group(0)
    if t in HU:
        return '>' + raw.replace(t, HU[t]) + '<'
    if not KEEP.match(t):
        MISSING.add(t)
    return m.group(0)

def tr_attr(m):
    t = m.group(2)
    if t in HU:
        return f'{m.group(1)}="{HU[t]}"'
    if not KEEP.match(t):
        MISSING.add(t)
    return m.group(0)

for name in PAGES:
    path = os.path.join(SRC, name)
    en = open(path, encoding='utf-8').read()
    # English artboard: make sure it links to its Hungarian twin
    if 'hreflang="hu"' not in en:
        en = NAV.sub(lambda m: m.group(1) + switch(hu_name(name), 'Magyar', 'hu'), en, count=1)
        open(path, 'w', encoding='utf-8').write(en)
    head, rest = en.split('<x-dc>', 1)
    body, tail = rest.split('</x-dc>', 1)
    head = head.replace('<html lang="en">', '<html lang="hu">', 1)
    head = re.sub(r'<title>(.*?)</title>', lambda m: f'<title>{HU.get(m.group(1).strip(), m.group(1))}</title>', head)
    helmet = re.search(r'<helmet>.*?</helmet>', body, re.S).group(0)
    content = body.replace(helmet, '\x00')
    content = content.replace(switch(hu_name(name), 'Magyar', 'hu'), switch(name, 'English', 'en'))
    content = re.sub(r'(alt|aria-label)="([^"]+)"', tr_attr, content)
    content = re.sub(r'>([^<]+)<', tr_text, content)
    for p in PAGES:
        content = content.replace(f'href="{p}"', f'href="{hu_name(p)}"')
    # the language switch must still point back to the English page
    content = content.replace(f'href="{hu_name(name)}" lang="en"', f'href="{name}" lang="en"')
    body = content.replace('\x00', helmet)
    out = head + '<x-dc>' + body + '</x-dc>' + tail
    open(os.path.join(SRC, hu_name(name)), 'w', encoding='utf-8').write(out)

if MISSING:
    raise SystemExit('Untranslated: ' + json.dumps(sorted(MISSING), ensure_ascii=False, indent=1))
print('ok')
