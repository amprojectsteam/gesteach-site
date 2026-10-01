"""Write the parts every page of the site shares, from one place.

Each page marks a shared part with two comments, <!-- @name --> and <!-- /@name -->, and this
rewrites what lies between them, leaving the rest of the page as it is:

    head      viewport, canonical, hreflang, Open Graph, icons, fonts, stylesheet
    header    skip link, navigation, language switch, the GesTeach sub-navigation
    footer    contact, project links, the wordmark band, legal links
    orbs      the project spheres around the title of the home
    ring      the projects ring of the home: active projects out of all of them
    projects  the project cards at the bottom of the home

Projects come from projects.json, one per line: adding a project is adding a line there and
running this. Run it as well after changing the shell below or the list of pages. The four legal
pages are written by scripts/legal_to_site.py in the app's repository, which runs this at the end,
so they come out finished and in the same design. It also writes sitemap.xml.

The output is committed: GitHub Pages serves the files as they are and builds nothing.

    python scripts/build.py
"""
import html
import json
import pathlib
import posixpath
import re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SITE = "https://amprojectsteam.github.io/gesteach-site/"
CONTACT = "am.projects.team@gmail.com"

# Italian page -> English page, in sitemap order. A new page is added here.
PAIRS = [
    ("index.html", "en/index.html"),
    ("gesteach.html", "en/gesteach.html"),
    ("privacy.html", "en/privacy.html"),
    ("termini.html", "en/terms.html"),
    ("elimina-account.html", "en/delete-account.html"),
    ("privacy-sito.html", "en/site-privacy.html"),
]
GESTEACH = PAIRS[1:5]  # under the GesTeach sub-navigation, in its order
OTHER = {a: b for pair in PAIRS for a, b in (pair, pair[::-1])}

TEXT = {
    "it": {
        "locale": "it_IT", "skip": "Salta al contenuto", "nav": "Principale",
        "home": "AM Studio, pagina iniziale",
        "links": [("progetti", "Progetti"), ("metodo", "Come lavoriamo"), ("chi-siamo", "Chi siamo")],
        "switch": ("EN", "English", "en"),
        "sub": ["GesTeach", "Privacy", "Termini", "Elimina account"],
        "orbs": "Progetti di AM Studio",
        "talk": "Un'idea, una domanda?<br>Scriviamoci.",
        "write": "Scrivici",
        "github": "AM Studio su GitHub", "footer_nav": "Progetti e studio",
        "about": "Chi siamo", "site_privacy": "Privacy e cookie del sito", "legal": "Note legali",
        "legal_gesteach": ["Privacy di GesTeach", "Termini di GesTeach", "Eliminare l'account GesTeach"],
    },
    "en": {
        "locale": "en_US", "skip": "Skip to content", "nav": "Main",
        "home": "AM Studio, home page",
        "links": [("progetti", "Projects"), ("metodo", "How we work"), ("chi-siamo", "About us")],
        "switch": ("IT", "Italiano", "it"),
        "sub": ["GesTeach", "Privacy", "Terms", "Delete account"],
        "orbs": "AM Studio projects",
        "talk": "An idea, a question?<br>Write to us.",
        "write": "Write to us",
        "github": "AM Studio on GitHub", "footer_nav": "Projects and studio",
        "about": "About us", "site_privacy": "Site privacy and cookies", "legal": "Legal",
        "legal_gesteach": ["GesTeach privacy", "GesTeach terms", "Deleting a GesTeach account"],
    },
}

GITHUB = ('<svg viewBox="0 0 16 16" width="22" height="22" aria-hidden="true" focusable="false"><path fill="currentColor" '
          'd="M8 0c4.42 0 8 3.58 8 8a8.013 8.013 0 0 1-5.45 7.59c-.4.08-.55-.17-.55-.38 0-.27.01-1.13.01-2.2 '
          '0-.75-.25-1.23-.54-1.48 1.78-.2 3.65-.88 3.65-3.95 0-.88-.31-1.59-.82-2.15.08-.2.36-1.02-.08-2.12 '
          '0 0-.67-.22-2.2.82-.64-.18-1.32-.27-2-.27-.68 0-1.36.09-2 .27-1.53-1.03-2.2-.82-2.2-.82-.44 1.1-.16 '
          '1.92-.08 2.12-.51.56-.82 1.28-.82 2.15 0 3.06 1.86 3.75 3.64 3.95-.23.2-.44.55-.51 1.07-.46.21-1.61.55'
          '-2.33-.66-.15-.24-.6-.83-1.23-.82-.67.01-.27.38.01.53.34.19.73.9.82 1.13.16.45.68 1.31 2.69.94 0 .67.01 '
          '1.3.01 1.49 0 .21-.15.45-.55.38A7.995 7.995 0 0 1 0 8c0-4.42 3.58-8 8-8Z"/></svg>')
CURRENT = ' aria-current="page"'


def esc(s):
    return html.escape(s)


def rel(page, target):
    """A link from page to target, both given from the site root."""
    if target.startswith(("http:", "https:", "mailto:")):
        return target
    if page == "404.html":  # served for a missing address at any depth, so it links from the root
        return "/gesteach-site/" + target
    return posixpath.relpath(target, posixpath.dirname(page) or ".")


def url(page):
    return SITE + re.sub(r"(^|/)index\.html$", r"\1", page)


def home_of(lang):
    return "en/index.html" if lang == "en" else "index.html"


def local(page, lang):
    """The same page of the site in the reader's language."""
    return OTHER[page] if lang == "en" and page in OTHER and not page.startswith("en/") else page


def face(page, project):
    if project["icon"]:
        return f'<img src="{rel(page, project["icon"])}" alt="" width="56" height="56">'
    return f'<span class="initials" aria-hidden="true">{esc(project["name"][:1])}</span>'


def head(page, lang, text):
    title = re.search(r"<title>(.*?)</title>", text, re.S).group(1).strip()
    desc = re.search(r'<meta name="description" content="([^"]*)"', text).group(1)
    up = "/gesteach-site/" if page == "404.html" else "../" if page.startswith("en/") else ""
    lines = ['<meta name="viewport" content="width=device-width, initial-scale=1">']
    if page in OTHER:
        it, en = (page, OTHER[page]) if lang == "it" else (OTHER[page], page)
        lines += [
            f'<link rel="canonical" href="{url(page)}">',
            f'<link rel="alternate" hreflang="it" href="{url(it)}">',
            f'<link rel="alternate" hreflang="en" href="{url(en)}">',
            f'<link rel="alternate" hreflang="x-default" href="{url(it)}">',
            '<meta property="og:type" content="website">',
            '<meta property="og:site_name" content="AM Studio">',
            f'<meta property="og:title" content="{title}">',
            f'<meta property="og:description" content="{desc}">',
            f'<meta property="og:url" content="{url(page)}">',
            f'<meta property="og:image" content="{SITE}img/og.jpg">',
            '<meta property="og:image:width" content="1200">',
            '<meta property="og:image:height" content="630">',
            '<meta property="og:image:alt" content="AM Studio">',
            f'<meta property="og:locale" content="{TEXT[lang]["locale"]}">',
            f'<meta property="og:locale:alternate" content="{TEXT["en" if lang == "it" else "it"]["locale"]}">',
            '<meta name="twitter:card" content="summary_large_image">',
        ]
    lines += [
        '<meta name="theme-color" content="#A3B1BA">',
        f'<link rel="icon" href="{up}img/favicon-32.png" type="image/png" sizes="32x32">',
        f'<link rel="apple-touch-icon" href="{up}img/apple-touch-icon.png">',
        f'<link rel="preload" href="{up}fonts/noto-sans-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin>',
        f'<link rel="preload" href="{up}fonts/inter-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin>',
        f'<link rel="stylesheet" href="{up}style.css">',
    ]
    return "\n".join("  " + line for line in lines)


def header(page, lang):
    t = TEXT[lang]
    home = home_of(lang)
    to_home = "" if page == home else rel(page, home)
    items = [f'<li><a href="{to_home}#{anchor}">{label}</a></li>' for anchor, label in t["links"]]
    if page in OTHER:
        short, name, code = t["switch"]
        items.append(f'<li><a class="nav__lang" href="{rel(page, OTHER[page])}" hreflang="{code}" lang="{code}">'
                     f'<span aria-hidden="true">{short}</span><span class="sr-only">{name}</span></a></li>')
    out = [
        f'  <a class="skip" href="#main">{t["skip"]}</a>',
        '  <header class="site-header">',
        f'    <nav class="nav" aria-label="{t["nav"]}">',
        f'      <a class="brand" href="{rel(page, home)}" aria-label="{t["home"]}">'
        f'<img class="brand__mark" src="{rel(page, "img/logo-am.png")}" alt="" width="38" height="38"><span>AM Studio</span></a>',
        '      <ul class="pill nav__links">',
        *("        " + item for item in items),
        '      </ul>',
        '    </nav>',
    ]
    family = [pair[1 if lang == "en" else 0] for pair in GESTEACH]
    if page in family:
        out += ['    <nav class="subnav" aria-label="GesTeach">', '      <ul class="pill">']
        out += [f'        <li><a href="{rel(page, p)}"{CURRENT if p == page else ""}>{label}</a></li>'
                for p, label in zip(family, t["sub"])]
        out += ['      </ul>', '    </nav>']
    out.append('  </header>')
    return "\n".join(out)


def footer(page, lang, projects):
    t = TEXT[lang]
    home = home_of(lang)
    to_home = "" if page == home else rel(page, home)
    links = [f'<li><a href="{rel(page, local(p["href"], lang))}">{esc(p["name"])}</a></li>'
             for p in projects if p["href"]]
    links += [f'<li><a href="{to_home}#{anchor}">{label}</a></li>' for anchor, label in t["links"][1:]]
    legal = [(local("privacy-sito.html", lang), t["site_privacy"])]
    legal += [(local(p, lang), label) for p, label in zip(("privacy.html", "termini.html", "elimina-account.html"),
                                                         t["legal_gesteach"])]
    return "\n".join([
        '  <footer class="site-footer">',
        '    <div class="footer-top">',
        '      <div class="footer-contact">',
        f'        <h2 class="footer-title">{t["talk"]}</h2>',
        f'        <a class="mail-pill" href="mailto:{CONTACT}">',
        f'          <span class="mail-pill__address">{CONTACT}</span>',
        f'          <span class="mail-pill__button">{t["write"]}</span>',
        '        </a>',
        '        <ul class="socials">',
        f'          <li><a href="https://github.com/amprojectsteam" aria-label="{t["github"]}">{GITHUB}</a></li>',
        '        </ul>',
        '      </div>',
        f'      <nav class="footer-links" aria-label="{t["footer_nav"]}">',
        '        <ul>',
        *("          " + link for link in links),
        '        </ul>',
        '      </nav>',
        '    </div>',
        '    <div class="wordmark" aria-hidden="true">',
        '      <div class="wordmark__haze wordmark__haze--far"></div>',
        '      <div class="wordmark__haze"></div>',
        '      <p class="wordmark__text">AM Studio</p>',
        '    </div>',
        '    <div class="footer-legal">',
        f'      <nav aria-label="{t["legal"]}">',
        '        <ul>',
        *(f'          <li><a href="{rel(page, p)}"{CURRENT if p == page else ""}>{label}</a></li>' for p, label in legal),
        '        </ul>',
        '      </nav>',
        '      <p>© 2026 AM Studio</p>',
        '    </div>',
        '  </footer>',
    ])


def orbs(page, lang, projects):
    out = [f'        <ul class="orbs" aria-label="{TEXT[lang]["orbs"]}">']
    for i, p in enumerate(projects):
        angle = (40 + i * 360 / len(projects)) % 360
        inner = (f'<span class="orb__haze" aria-hidden="true"></span>'
                 f'<span class="orb__body">{face(page, p)}<span class="orb__name">{esc(p["name"])}</span></span>'
                 f'<span class="orb__desc">{esc(p["desc_en" if lang == "en" else "desc"])}</span>')
        link = (f'<a class="orb__link" href="{rel(page, local(p["href"], lang))}">{inner}</a>' if p["href"]
                else f'<span class="orb__link">{inner}</span>')
        out.append(f'          <li class="orb" style="--a:{angle:g}deg">{link}</li>')
    out.append('        </ul>')
    return "\n".join(out)


def ring(lang, projects):
    total = len(projects)
    active = sum(1 for p in projects if p.get("active"))
    share = active / total if total else 0
    unit = f"{'attivo' if active == 1 else 'attivi'} su {total}" if lang == "it" else f"active of {total}"
    return "\n".join([
        '            <svg class="ring" viewBox="0 0 220 220" aria-hidden="true" focusable="false">',
        '              <circle class="ring__track" cx="110" cy="110" r="96"/>',
        f'              <circle class="ring__arc" cx="110" cy="110" r="101.5" pathLength="1" data-ring="{share:g}" style="--p:{share:g}"/>',
        '            </svg>',
        f'            <p class="stat__label">{"Progetti" if lang == "it" else "Projects"}</p>',
        f'            <p class="stat__value"><span data-count="{active}" aria-hidden="true">{active}</span>'
        f'<span class="sr-only">{active}</span></p>',
        f'            <p class="stat__unit">{unit}</p>',
    ])


def project_cards(page, lang, projects):
    out = ['      <ul class="projects__list">']
    for p in projects:
        name = esc(p["name"])
        if p["href"]:
            name = f'<a href="{rel(page, local(p["href"], lang))}">{name}</a>'
        out += [
            '        <li class="project">',
            f'          <span class="project__orb">{face(page, p)}</span>',
            f'          <h3 class="project__name">{name}</h3>',
            f'          <p class="project__status">{esc(p["status_en" if lang == "en" else "status"])}</p>',
            f'          <p class="project__desc">{esc(p["desc_en" if lang == "en" else "desc"])}</p>',
            '        </li>',
        ]
    out.append('      </ul>')
    return "\n".join(out)


def fill(text, name, body):
    pattern = re.compile(rf"^([ \t]*)<!-- @{name} -->.*?<!-- /@{name} -->", re.M | re.S)
    return pattern.sub(lambda m: f"{m.group(1)}<!-- @{name} -->\n{body}\n{m.group(1)}<!-- /@{name} -->", text)


def sitemap():
    rows = []
    for it, en in PAIRS:
        alternates = "".join(f'\n    <xhtml:link rel="alternate" hreflang="{code}" href="{url(p)}"/>'
                             for code, p in (("it", it), ("en", en), ("x-default", it)))
        rows += [f"  <url>\n    <loc>{url(p)}</loc>{alternates}\n  </url>" for p in (it, en)]
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9" xmlns:xhtml="http://www.w3.org/1999/xhtml">\n'
            + "\n".join(rows) + "\n</urlset>\n")


def write(path, content):
    if not path.exists() or path.read_text(encoding="utf-8") != content:
        path.write_text(content, encoding="utf-8", newline="\n")
        print(f"{path.relative_to(ROOT).as_posix()}: written")


def main():
    projects = json.loads((ROOT / "projects.json").read_text(encoding="utf-8"))
    for page in [p for pair in PAIRS for p in pair] + ["404.html"]:
        lang = "en" if page.startswith("en/") else "it"
        text = (ROOT / page).read_text(encoding="utf-8")
        for name, body in (("head", lambda: head(page, lang, text)),
                           ("header", lambda: header(page, lang)),
                           ("footer", lambda: footer(page, lang, projects)),
                           ("orbs", lambda: orbs(page, lang, projects)),
                           ("ring", lambda: ring(lang, projects)),
                           ("projects", lambda: project_cards(page, lang, projects))):
            if f"<!-- @{name} -->" in text:
                text = fill(text, name, body())
        write(ROOT / page, text)
    write(ROOT / "sitemap.xml", sitemap())


if __name__ == "__main__":
    main()
