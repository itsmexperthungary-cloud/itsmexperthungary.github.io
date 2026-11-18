"""Build the static GitHub Pages site from the Design canvas artboards.

Usage: python3 build_site.py <artboard_dir> <out_dir> <base_url>
"""
import os, re, shutil, sys, json
from PIL import Image, ImageDraw, ImageFont

SRC, OUT, BASE = sys.argv[1], sys.argv[2], sys.argv[3].rstrip('/') + '/'
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = '/home/claude/landing/assets'
CV = '/home/claude/cv/public/A_Krisztina_Juhasz_CV.pdf'
ACCENT = '#8E2F3C'

PAGES = {
    'Main.dc.html': ('index.html',
        'ITSM process consultant and ITIL trainer. I build and redesign IT service management practices and lead the organisational change that makes them stick.'),
    'HealthCheck.dc.html': ('health-check.html',
        'A five-day, fixed-scope ITSM health check: interviews, a maturity snapshot based on ITIL 4 and three priorities you can act on right away.'),
    'Privacy.dc.html': ('privacy.html',
        'Privacy notice and legal notice for the website of A. Krisztina Juhász.'),
}
PAGES.update({
    'Main-HU.dc.html': ('hu/index.html',
        'ITSM folyamattanácsadó és ITIL-tréner. IT service management folyamatokat építek fel és alakítok át, és vezetem a szervezeti változást, amitől tartósak maradnak.'),
    'HealthCheck-HU.dc.html': ('hu/health-check.html',
        'Ötnapos, fix scope-ú ITSM health check: interjúk, ITIL 4 alapú maturity snapshot és három azonnal megvalósítható prioritás.'),
    'Privacy-HU.dc.html': ('hu/privacy.html',
        'A. Krisztina Juhász weboldalának adatkezelési tájékoztatója és impresszuma.'),
})
SITE_PATH = {src: out for src, (out, _) in PAGES.items()}

def rel_link(from_out, to_out):
    """Relative href from one output page to another (both relative to the site root)."""
    import posixpath
    target = to_out[:-len('index.html')] if to_out.endswith('index.html') else to_out
    rel = posixpath.relpath(target or '.', posixpath.dirname(from_out) or '.')
    if rel == '.':
        return './'
    return rel + '/' if target.endswith('/') or not target else rel

def twin(src):
    return src.replace('-HU.dc.html', '.dc.html') if '-HU' in src else src.replace('.dc.html', '-HU.dc.html')
BLOBS = {
    '335d4c1bc800bbaa0758325b5cc2dd52': ('icons/linkedin.png', 'assets/img/linkedin.png'),
    '6c8e5759d1e7a3b64f05a6070c655941': ('krisztina-juhasz-portrait.jpg', 'assets/img/portrait.jpg'),
    '33f33fc8aa091cdfde8ae78a6dbffbb7': ('krisztina-juhasz-at-work.jpg', 'assets/img/at-work.jpg'),
    '92b02e9d56b2268a377ae2434e75f973': ('krisztina-juhasz-books.jpg', 'assets/img/books.jpg'),
    '4aa089631036ff62b45338bb80f6aa7c': ('krisztina-juhasz-health-check-crop.jpg', 'assets/img/health-check.jpg'),
    '257e101c1156cd96bd268366c643cb98': (None, 'assets/A_Krisztina_Juhasz_CV.pdf'),
    'a397690d0bb930f1b60abb7ead28d4f5': ('badges/az-900.png', 'assets/img/badges/az-900.png'),
    '7b0a708930439e6dbda676366460a64c': ('badges/ab-730.png', 'assets/img/badges/ab-730.png'),
    '4bef5be650a643d98f39d5bc9dfa9bfa': ('badges/itil4-strategic-leader-hd.png', 'assets/img/badges/itil4-strategic-leader.png'),
    '0aeef7efdb0b6c8dfec9c53ef7a519f0': ('badges/itil4-hvit-hd.png', 'assets/img/badges/itil4-hvit.png'),
    '84ba9e585ca4ab924db2d6b1226542a1': ('badges/itil4-dsv-hd.png', 'assets/img/badges/itil4-dsv.png'),
    'b4179e62ac858efeb883407223aa1a74': ('badges/itil4-foundation-hd.png', 'assets/img/badges/itil4-foundation.png'),
}


HU = json.load(open(os.path.join(HERE, 'hu.json'), encoding='utf-8'))
KEEP = re.compile(r'(?s)^(A\. Krisztina Juhász|\d+|[.;]|ITSM Health Check|itsmexperthungary@gmail\.com|ugyfelszolgalat@naih\.hu|www\.naih\.hu|ITIL 4 .*|Microsoft AI Business Professional \(AB-730\)|Azure Fundamentals \(AZ-900\)|ServiceNow Certified System Administrator|GitHub, Inc\., 88 Colin.*|width=device-width.*|English|Magyar|document\..*|PeopleCert|Microsoft|Microsoft · A[BZ]-\d+|Microsoft Certified: .*|.* badge|ITSM Health Check – A\. Krisztina Juhász)$')
MISSING = set()

def nav_switch(html, href, label, lang):
    link = f'<a href="{href}" lang="{lang}" hreflang="{lang}" style="color: #444650; text-decoration: none; font-weight: 600">{label}</a>\n'
    return re.sub(r'(<nav aria-label="Main"[^>]*>\n)', lambda m: m.group(1) + link, html, count=1)

def alternates(html, en_url, hu_url):
    alt = (f'<link rel="alternate" hreflang="en" href="{en_url}">\n'
           f'<link rel="alternate" hreflang="hu" href="{hu_url}">\n')
    return html.replace('<link rel="icon"', alt + '<link rel="icon"', 1)

def tr_segment(m):
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
    if ' ' in t and not KEEP.match(t) and not t.startswith('http'):
        MISSING.add(t)
    return m.group(0)

def make_hu(out_name, html):
    h = html.replace('<html lang="en">', '<html lang="hu">', 1)
    head, body = h.split('<body>', 1)
    head = re.sub(r'(content)="([^"]+)"', tr_attr, head)
    head = re.sub(r'>([^<]+)<', tr_segment, head)
    body = re.sub(r'(alt|aria-label)="([^"]+)"', tr_attr, body)
    body = re.sub(r'>([^<]+)<', tr_segment, body)
    h = head + '<body>' + body
    for a in ('href="assets/', 'src="assets/', 'href="favicon', 'href="apple-touch'):
        h = h.replace(a, a.replace('="', '="../'))
    page_path = '' if out_name == 'index.html' else out_name
    h = h.replace(f'<link rel="canonical" href="{BASE}{page_path}">', f'<link rel="canonical" href="{BASE}hu/{page_path}">')
    h = h.replace(f'<meta property="og:url" content="{BASE}{page_path}">', f'<meta property="og:url" content="{BASE}hu/{page_path}">')
    h = nav_switch(h, '../' + page_path, 'English', 'en')
    return h

def fonts_css():
    out = []
    for fam, weights in (('inter', (400, 500, 600)), ('plus-jakarta-sans', (600, 700, 800))):
        for w in weights:
            css = open(f'{HERE}/node_modules/@fontsource/{fam}/{w}.css', encoding='utf-8').read()
            for block in re.findall(r'/\* [^*]+ \*/\s*@font-face \{.*?\}', css, re.S):
                name = re.search(r'/\* ([^*]+) \*/', block).group(1)
                if not re.search(r'-latin(-ext)?-\d+-normal$', name):
                    continue
                fn = re.search(r'url\(\./files/([^)]+\.woff2)\)', block).group(1)
                shutil.copy(f'{HERE}/node_modules/@fontsource/{fam}/files/{fn}', f'{OUT}/assets/fonts/{fn}')
                block = re.sub(r'src: [^;]+;', f"src: url(../fonts/{fn}) format('woff2');", block)
                out.append(block)
    return '\n\n'.join(out)

def page_html(src_name):
    out_name, desc = PAGES[src_name]
    s = open(os.path.join(SRC, src_name), encoding='utf-8').read()
    title = re.search(r'<title>(.*?)</title>', s, re.S).group(1).strip()
    body = re.search(r'<x-dc>(.*)</x-dc>', s, re.S).group(1)
    body = re.sub(r'<helmet>.*?</helmet>', '', body, flags=re.S).strip()
    body = body.replace('{{accent}}', ACCENT)
    body = body.replace('onClick="{{prev}}"', 'data-slide="-1"').replace('onClick="{{next}}"', 'data-slide="1"')
    # badge tiles without a verification link yet: not clickable, no "Verify" label
    body = re.sub(r'<a href="#verify" (style="[^"]*")>(.*?)<span style="margin-top: auto;[^"]*">(?:Verify|Ellenőrzés) ↗</span></a>',
                  lambda m: f'<div {m.group(1)}>{m.group(2)}</div>', body, flags=re.S)
    if 'cert-track' in body:
        body += '''
<script>
document.querySelectorAll('[data-slide]').forEach(function (b) {
  b.addEventListener('click', function () {
    var t = document.getElementById('cert-track');
    if (t) t.scrollBy({ left: Number(b.dataset.slide) * 184, behavior: 'smooth' });
  });
});
</script>'''
    if '{{' in body:
        raise SystemExit(f'Unresolved template hole in {src_name}')
    for bid, (_, path) in BLOBS.items():
        body = body.replace(f'/_blob/{bid}', path)
    if '/_blob/' in body:
        raise SystemExit(f'Unknown asset in {src_name}: ' + re.search(r'/_blob/\w+', body).group(0))
    for k, v in SITE_PATH.items():
        body = body.replace(f'href="{k}', f'href="{rel_link(out_name, v)}')
    lang = 'hu' if '-HU' in src_name else 'en'
    up = '../' * out_name.count('/')
    url = BASE + (out_name[:-len('index.html')] if out_name.endswith('index.html') else out_name)
    for bid, (_, path) in BLOBS.items():
        body = body.replace(f'"{path}', f'"{up}{path}')
    head = f'''<!doctype html>
<html lang="{lang}">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{desc}">
<link rel="canonical" href="{url}">
<meta property="og:type" content="website">
<meta property="og:title" content="{title}">
<meta property="og:description" content="{desc}">
<meta property="og:url" content="{url}">
<meta property="og:image" content="{BASE}assets/img/og-image.jpg">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="{up}favicon.svg" type="image/svg+xml">
<link rel="icon" href="{up}favicon-32.png" sizes="32x32" type="image/png">
<link rel="apple-touch-icon" href="{up}apple-touch-icon.png">
<link rel="preload" href="{up}assets/fonts/inter-latin-400-normal.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="{up}assets/css/site.css">
</head>
<body>
'''
    return out_name, head + body + '\n</body>\n</html>\n'

def og_image():
    G = '/usr/share/fonts/truetype/google-fonts/'
    im = Image.new('RGB', (1200, 630), '#CEC2BC')
    p = Image.open(f'{ASSETS}/krisztina-juhasz-portrait.jpg').convert('RGB')
    w = 504; h = round(p.height * w / p.width)
    p = p.resize((w, h), Image.LANCZOS).crop((0, 0, w, 630))
    im.paste(p, (0, 0))
    d = ImageDraw.Draw(im)
    navy = '#1B2A47'
    d.text((560, 170), 'A. Krisztina Juhász', font=ImageFont.truetype(G + 'Poppins-Bold.ttf', 52), fill=navy)
    d.text((562, 250), 'ITSM PROCESS CONSULTANT · ITIL TRAINER', font=ImageFont.truetype(G + 'Poppins-Medium.ttf', 22), fill=ACCENT)
    f = ImageFont.truetype(G + 'Poppins-Regular.ttf', 30)
    for i, line in enumerate(['Service management that', 'people actually use.']):
        d.text((560, 320 + i * 44), line, font=f, fill='#2F3340')
    d.rectangle((560, 450, 640, 454), fill=ACCENT)
    im.save(f'{OUT}/assets/img/og-image.jpg', quality=88, optimize=True)

def icons():
    svg = ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64">'
           '<rect width="64" height="64" rx="14" fill="#1B2A47"/>'
           '<text x="32" y="42" text-anchor="middle" font-family="Arial, Helvetica, sans-serif" '
           'font-size="28" font-weight="700" fill="#FFFFFF">KJ</text></svg>')
    open(f'{OUT}/favicon.svg', 'w').write(svg)
    G = '/usr/share/fonts/truetype/google-fonts/'
    for size, name in ((32, 'favicon-32.png'), (180, 'apple-touch-icon.png')):
        big = 512
        im = Image.new('RGBA', (big, big), (0, 0, 0, 0))
        d = ImageDraw.Draw(im)
        d.rounded_rectangle((0, 0, big, big), radius=110, fill='#1B2A47')
        f = ImageFont.truetype(G + 'Poppins-Bold.ttf', 230)
        bb = d.textbbox((0, 0), 'KJ', font=f)
        d.text(((big - (bb[2] - bb[0])) / 2 - bb[0], (big - (bb[3] - bb[1])) / 2 - bb[1]), 'KJ', font=f, fill='white')
        im.resize((size, size), Image.LANCZOS).save(f'{OUT}/{name}')

WJ = '\u2060'  # word joiner: invisible, forbids a line break on both sides
COMPOUND = re.compile(r'(?<=\w)(-|\))(?=[\w(])')
PHRASES = ['Service management', 'service management', 'Jira Service Management', 'Microsoft 365', 'ITIL 4',
           'Change Enablement', 'Azure DevOps', 'Jira Assets', 'A. Krisztina Juhász', '9+ years', '9+ év',
           'IT service', 'IT-szolgáltatás', 'IT service management', 'Change Enablement', 'Knowledge Management', 'customer journey', 'stakeholder map', 'operating model', 'continual improvement', 'maturity snapshot', 'Maturity snapshot', 'maturity assessment', 'improvement roadmap', 'service review', 'service owner', 'service desk', 'process onboarding', 'Quality Gate', 'health check']
def keep_compounds(html):
    """Never split hyphenated words (IT-szervezet, third-party) or fixed phrases across lines."""
    head, sep, body = html.partition('<body')
    parts = re.split(r'(<script.*?</script>|<style.*?</style>|<[^>]+>)', body, flags=re.S)
    for i in range(0, len(parts), 2):
        t = COMPOUND.sub(lambda m: m.group(1) + WJ, parts[i])
        for ph in PHRASES:
            t = t.replace(ph, ph.replace(' ', '\u00a0'))
        parts[i] = t
    return head + sep + ''.join(parts)

def main():
    for sub in ('assets/css', 'assets/fonts', 'assets/img', 'assets/img/badges'):
        os.makedirs(f'{OUT}/{sub}', exist_ok=True)
    css = fonts_css() + '''

html{-webkit-text-size-adjust:100%;scroll-behavior:smooth;scroll-padding-top:96px}
body{margin:0;background:#FFFFFF}
img{max-width:100%}
a{color:#8E2F3C}a:hover{color:#6E2430}
@media (max-width:1023px){[style*="position: sticky; top: 112px"]{position:static!important}}
@media (max-width:1199px){[style*="text-align: justify"]{text-align:left!important}}
@media (max-width:640px){p,li span,h1,h2,h3{text-align:left!important}}
h1{text-wrap:balance}
h1,h2,h3{overflow-wrap:break-word;max-width:100%!important;height:auto!important}
a[style*="min-height: 52px"]{padding-top:10px!important;padding-bottom:10px!important;box-sizing:border-box}
@media (max-width:640px){div[style*="flex-direction: column; align-items: flex-end"]{align-items:flex-start!important}div[style*="justify-content: flex-end"]{justify-content:flex-start!important}}
@media (max-width:640px){
header>div{padding:10px 16px!important;gap:8px!important;flex-wrap:nowrap!important}
header>div>a:first-child{font-size:18px!important;white-space:nowrap}
header nav{gap:6px!important;flex-wrap:nowrap!important}
header nav a[style*="background"]{padding:0 14px!important;min-height:40px!important;white-space:nowrap}
header nav a[hreflang]{min-width:40px!important}
header nav a[href^="#"]:not([style*="background"]),header nav a[href="./"],header nav a[href="../"]{display:none!important}
}
@media (max-width:400px){h1{font-size:min(30px,8.4vw)!important}}
'''
    open(f'{OUT}/assets/css/site.css', 'w', encoding='utf-8').write(css)
    for bid, (local, path) in BLOBS.items():
        shutil.copy(f'{ASSETS}/{local}' if local else CV, f'{OUT}/{path}')
    os.makedirs(f'{OUT}/hu', exist_ok=True)
    for src in PAGES:
        name, html = page_html(src)
        en_src = src if '-HU' not in src else twin(src)
        en_out, hu_out = SITE_PATH[en_src], SITE_PATH[twin(en_src)]
        strip = lambda p: p[:-len('index.html')] if p.endswith('index.html') else p
        html = alternates(html, BASE + strip(en_out), BASE + strip(hu_out))
        open(f'{OUT}/{name}', 'w', encoding='utf-8').write(keep_compounds(html))
    og_image()
    icons()
    print('built', sorted(os.listdir(OUT)))

main()
