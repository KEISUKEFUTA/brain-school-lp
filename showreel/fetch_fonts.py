# Downloads the exact fonts the reel uses into ./fonts and writes fonts.css (M PLUS 1 is subset to the reel's text).
import re, subprocess, urllib.parse, pathlib
UA = 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36'
html = pathlib.Path('index.html').read_text()
jp_text = ''.join(sorted(set(re.search(r"const JPTEXT = '([^']*)'", html).group(1) + re.sub(r'[\x00-\x7f]', '', html)
                             + 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789 .,:;!?-—·×/@+()')))
def get(url, out=None):
    for _ in range(6):
        r = subprocess.run(['curl', '-sSfL', '-A', UA, '--retry', '4', url] + (['-o', out] if out else []), capture_output=True)
        if r.returncode == 0: return r.stdout.decode() if not out else None
    raise SystemExit('failed: ' + url)
css_out = []
jobs = [('M PLUS 1', 'M+PLUS+1', w, '&text=' + urllib.parse.quote(jp_text)) for w in (500, 700, 800, 900)] + \
       [('Poppins', 'Poppins', w, '') for w in (500, 600, 700, 800)]
for fam, q, w, extra in jobs:
    css = get(f'https://fonts.googleapis.com/css2?family={q}:wght@{w}{extra}&display=block')
    for i, m in enumerate(re.finditer(r'@font-face\s*{([^}]*)}', css)):
        block = m.group(1)
        if fam == 'Poppins' and 'U+0000-00FF' not in block: continue   # latin only
        url = re.search(r'url\(([^)]+)\)', block).group(1)
        name = f"{fam.replace(' ', '')}-{w}-{i}.woff2"; get(url, 'fonts/' + name)
        css_out.append(re.sub(r'url\([^)]+\)', f"url(fonts/{name})", '@font-face{' + block + '}'))
pathlib.Path('fonts.css').write_text('\n'.join(css_out) + '\n')
print(len(css_out), 'faces')
