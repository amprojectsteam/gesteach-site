"""Write the parts every page of the site shares, from one place.

Each page marks a shared part with two comments, <!-- @name --> and <!-- /@name -->, and this
rewrites what lies between them, leaving the rest of the page as it is:

    head          viewport, canonical, hreflang, Open Graph, icons, font, stylesheet
    header        skip link, navigation, language switch, the GesTeach sub-navigation
    footer        the "write to us" box, then on the home one thin line (privacy, GitHub) and on
                  every other page the footer columns, the wordmark band and the legal links
    orbs          the project logos orbiting the logo of the home; a project with no page yet is
                  a logo that answers "we're working on it"
    testimonials  the quotes of the GesTeach page; empty, and so absent, while there are none

Projects come from projects.json and quotes from testimonials.json, one per line: adding one is
adding a line there and running this. Run it as well after changing the shell below or the list of
pages. The four legal pages are written by scripts/legal_to_site.py in the app's repository, which
runs this at the end, so they come out finished and in the same design. It also writes sitemap.xml.

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
        "home": "AM Studio, pagina iniziale", "menu": "Apri il menu", "close": "Chiudi il menu",
        # a link is a page of the site, maybe with an anchor, or a bare anchor of the home.
        # No project here: a project opens only from its sphere
        "links": [("#progetti", "Progetti"), ("#chi-siamo", "Chi siamo")],
        "switch": ("EN", "English", "en"),
        "sub": ["GesTeach", "Privacy", "Termini", "Elimina account"],
        "orbs": "Progetti di AM Studio", "soon": "Ci stiamo lavorando.", "privacy": "Privacy",
        "talk": 'Un\'idea, una domanda? <span class="grad">Scriviamoci.</span>',
        "talk_text": "Per GesTeach, per un progetto nuovo o anche solo per un parere: ti rispondiamo noi, Mirko e Alice.",
        "write": "Scrivici",
        "blurb": "Progettiamo e sviluppiamo app. La prima è GesTeach, per chi insegna.",
        "social": "Social", "github": "AM Studio su GitHub",
        "projects": "Progetti", "explore": "Esplora",
        "explore_links": [("gesteach.html#funzioni", "Funzioni"), ("gesteach.html#prezzi", "Prezzi"),
                          ("gesteach.html#novita", "Novità"), ("#chi-siamo", "Chi siamo")],
        "site_privacy": "Privacy e cookie del sito", "legal": "Note legali",
        "legal_gesteach": ["Privacy di GesTeach", "Termini di GesTeach", "Eliminare l'account GesTeach"],
        "quotes": ("Testimonianze", "Chi la usa", "Le parole di chi insegna con GesTeach"),
    },
    "en": {
        "locale": "en_US", "skip": "Skip to content", "nav": "Main",
        "home": "AM Studio, home page", "menu": "Open the menu", "close": "Close the menu",
        "links": [("#progetti", "Projects"), ("#chi-siamo", "About us")],
        "switch": ("IT", "Italiano", "it"),
        "sub": ["GesTeach", "Privacy", "Terms", "Delete account"],
        "orbs": "AM Studio projects", "soon": "We're working on it.", "privacy": "Privacy",
        "talk": 'An idea, a question? <span class="grad">Write to us.</span>',
        "talk_text": "About GesTeach, a new project or just for an opinion: Mirko and Alice will answer you themselves.",
        "write": "Write to us",
        "blurb": "We design and build apps. The first is GesTeach, for teachers.",
        "social": "Social", "github": "AM Studio on GitHub",
        "projects": "Projects", "explore": "Explore",
        "explore_links": [("gesteach.html#funzioni", "Features"), ("gesteach.html#prezzi", "Pricing"),
                          ("gesteach.html#novita", "News"), ("#chi-siamo", "About us")],
        "site_privacy": "Site privacy and cookies", "legal": "Legal",
        "legal_gesteach": ["GesTeach privacy", "GesTeach terms", "Deleting a GesTeach account"],
        "quotes": ("Testimonials", "Who uses it", "In the words of teachers who use GesTeach"),
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


def icon(page, name, cls="ico"):
    return (f'<svg class="{cls}" aria-hidden="true" focusable="false">'
            f'<use href="{rel(page, "img/icons.svg")}#i-{name}"/></svg>')


def link(page, lang, target):
    """A link of the shared navigation: a page of the site, maybe with an anchor; a bare anchor is the home's."""
    path, _, anchor = target.partition("#")
    path = local(path, lang) if path else home_of(lang)
    if anchor and path == page:
        return "#" + anchor
    return rel(page, path) + ("#" + anchor if anchor else "")


def face(page, project):
    if project["icon"]:
        return f'<img src="{rel(page, project["icon"])}" alt="" width="56" height="56">'
    return f'<span class="initials" aria-hidden="true">{esc(project.get("mark", project["name"][:1]))}</span>'


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
        '<meta name="theme-color" content="#060610">',
        f'<link rel="icon" href="{up}img/favicon-32.png" type="image/png" sizes="32x32">',
        f'<link rel="apple-touch-icon" href="{up}img/apple-touch-icon.png">',
        f'<link rel="preload" href="{up}fonts/inter-tight-latin-wght-normal.woff2" as="font" type="font/woff2" crossorigin>',
        f'<link rel="stylesheet" href="{up}style.css">',
    ]
    return "\n".join("  " + line for line in lines)


def header(page, lang):
    t = TEXT[lang]
    items = [f'<li><a href="{link(page, lang, target)}"'
             f'{CURRENT if local(target, lang) == page else ""}>{label}</a></li>' for target, label in t["links"]]
    actions = []
    if page in OTHER:
        short, name, code = t["switch"]
        actions.append(f'<a class="nav__lang" href="{rel(page, OTHER[page])}" hreflang="{code}" lang="{code}">'
                       f'<span aria-hidden="true">{short}</span><span class="sr-only">{name}</span></a>')
    actions.append(f'<a class="btn btn--sm" href="mailto:{CONTACT}">{t["write"]}</a>')
    out = [
        f'  <a class="skip" href="#main">{t["skip"]}</a>',
        '  <header class="site-header">',
        f'    <nav class="nav" aria-label="{t["nav"]}">',
        f'      <a class="brand" href="{rel(page, home_of(lang))}" aria-label="{t["home"]}">'
        f'<img class="brand__mark" src="{rel(page, "img/logo-am.png")}" alt="" width="38" height="38"><span>AM Studio</span></a>',
        # popover: a menu that opens and closes without script, so the legal pages can have it too
        f'      <button class="nav__toggle" type="button" popovertarget="menu" aria-label="{t["menu"]}">'
        f'{icon(page, "menu")}</button>',
        '      <div class="nav__menu" id="menu" popover>',
        f'        <button class="nav__close" type="button" popovertarget="menu" popovertargetaction="hide" '
        f'aria-label="{t["close"]}">{icon(page, "close")}</button>',
        '        <ul class="nav__links">',
        *("          " + item for item in items),
        '        </ul>',
        '        <div class="nav__actions">',
        *("          " + action for action in actions),
        '        </div>',
        '      </div>',
        '    </nav>',
    ]
    family = [pair[1 if lang == "en" else 0] for pair in GESTEACH]
    if page in family:
        out += ['    <nav class="subnav" aria-label="GesTeach">', '      <ul>']
        out += [f'        <li><a href="{rel(page, p)}"{CURRENT if p == page else ""}>{label}</a></li>'
                for p, label in zip(family, t["sub"])]
        out += ['      </ul>', '    </nav>']
    out.append('  </header>')
    return "\n".join(out)


def footer(page, lang, projects):
    t = TEXT[lang]
    cta = [
        '    <section class="cta" aria-labelledby="cta-title">',
        '      <div class="cta__box" data-reveal>',
        f'        <h2 class="cta__title" id="cta-title">{t["talk"]}</h2>',
        f'        <p>{t["talk_text"]}</p>',
        f'        <a class="btn" href="mailto:{CONTACT}">{icon(page, "mail")}{t["write"]}</a>',
        f'        <p class="cta__mail">{CONTACT}</p>',
        '      </div>',
        '    </section>',
    ]
    if page == home_of(lang):
        # the home is the projects and who we are: the rest of the site is one line under them
        dot = '<span aria-hidden="true"> · </span>'
        return "\n".join([
            '  <footer class="site-footer site-footer--slim">',
            *cta,
            f'    <p class="footer-bottom">© 2026 AM Studio{dot}<a href="{rel(page, local("privacy-sito.html", lang))}">'
            f'{t["privacy"]}</a>{dot}<a href="https://github.com/amprojectsteam">GitHub</a></p>',
            '  </footer>',
        ])
    projects_links = [f'<li><a href="{rel(page, local(p["href"], lang))}">{esc(p["name"])}</a></li>'
                      for p in projects if p["href"]]
    explore = [f'<li><a href="{link(page, lang, target)}">{label}</a></li>' for target, label in t["explore_links"]]
    legal = [(local("privacy-sito.html", lang), t["site_privacy"])]
    legal += [(local(p, lang), label) for p, label in zip(("privacy.html", "termini.html", "elimina-account.html"),
                                                         t["legal_gesteach"])]
    legal_links = [f'<li><a href="{rel(page, p)}"{CURRENT if p == page else ""}>{label}</a></li>' for p, label in legal]

    def column(key, label, links):
        return [
            f'        <nav class="footer-col" aria-labelledby="f-{key}">',
            f'          <p class="footer-head" id="f-{key}">{label}</p>',
            '          <ul>',
            *("            " + item for item in links),
            '          </ul>',
            '        </nav>',
        ]

    return "\n".join([
        '  <footer class="site-footer">',
        *cta,
        '    <div class="footer-main wrap">',
        '      <div class="footer-about">',
        f'        <a class="footer-brand" href="{rel(page, home_of(lang))}"><img src="{rel(page, "img/logo-am.png")}" '
        'alt="" width="38" height="38">AM Studio</a>',
        f'        <p>{t["blurb"]}</p>',
        f'        <p class="footer-head">{t["social"]}</p>',
        '        <ul class="socials">',
        f'          <li><a href="https://github.com/amprojectsteam" aria-label="{t["github"]}">{GITHUB}</a></li>',
        '        </ul>',
        '      </div>',
        *column("projects", t["projects"], projects_links),
        *column("explore", t["explore"], explore),
        *column("legal", t["legal"], legal_links),
        '    </div>',
        '    <div class="wordmark" aria-hidden="true">',
        '      <div class="wordmark__haze wordmark__haze--far"></div>',
        '      <div class="wordmark__haze"></div>',
        '      <p class="wordmark__text">AM Studio</p>',
        '    </div>',
        '    <p class="footer-bottom">© 2026 AM Studio</p>',
        '  </footer>',
    ])


def orbs(page, lang, projects):
    t = TEXT[lang]
    out = [f'        <ul class="orbs" aria-label="{t["orbs"]}">']
    for i, p in enumerate(projects):
        angle = (40 + i * 360 / len(projects)) % 360
        name = p.get("name_en", p["name"]) if lang == "en" else p["name"]
        inner = (f'<span class="orb__haze" aria-hidden="true">{face(page, p)}</span>'
                 f'<span class="orb__body">{face(page, p)}<span class="orb__name">{esc(name)}</span></span>'
                 f'<span class="orb__desc">{esc(p["desc_en" if lang == "en" else "desc"])}</span>')
        # a project with no page yet still goes round: a click has it say so (site.js)
        link_ = (f'<a class="orb__link" href="{rel(page, local(p["href"], lang))}">{inner}</a>' if p["href"]
                 else f'<button class="orb__link" type="button" data-told="{esc(t["soon"])}">{inner}</button>')
        out.append(f'          <li class="orb" style="--a:{angle:g}deg">{link_}</li>')
    out.append('        </ul>')
    out.append('        <p class="sr-only" role="status" data-orb-status></p>')
    return "\n".join(out)


def testimonials(lang, quotes):
    """Only real quotes, given with permission: with none, the section is not there at all."""
    if not quotes:
        return ""
    label, phrase, title = TEXT[lang]["quotes"]
    out = [
        '    <section class="section" id="testimonianze" aria-labelledby="quotes-title">',
        '      <div class="arcs arcs--low" aria-hidden="true"></div>',
        '      <div class="wrap">',
        '        <div class="section-head" data-reveal>',
        f'          <p class="tag"><span class="tag__label">{label}</span> {phrase}</p>',
        f'          <h2 id="quotes-title">{title}</h2>',
        '        </div>',
        '        <ul class="quotes">',
    ]
    for q in quotes:
        role = esc(q["role_en" if lang == "en" else "role"])
        out += [
            '          <li class="card quote" data-reveal>',
            f'            <span class="quote__face" aria-hidden="true">{esc(q["name"][:1])}</span>',
            f'            <blockquote><p>“{esc(q["quote_en" if lang == "en" else "quote"])}”</p></blockquote>',
            f'            <p class="quote__who"><strong>{esc(q["name"])}</strong> – {role}</p>',
            '          </li>',
        ]
    out += ['        </ul>', '      </div>', '    </section>']
    return "\n".join(out)


def fill(text, name, body):
    pattern = re.compile(rf"^([ \t]*)<!-- @{name} -->.*?<!-- /@{name} -->", re.M | re.S)
    inner = f"\n{body}\n" if body else "\n"
    return pattern.sub(lambda m: f"{m.group(1)}<!-- @{name} -->{inner}{m.group(1)}<!-- /@{name} -->", text)


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
    quotes = json.loads((ROOT / "testimonials.json").read_text(encoding="utf-8"))
    for page in [p for pair in PAIRS for p in pair] + ["404.html"]:
        lang = "en" if page.startswith("en/") else "it"
        text = (ROOT / page).read_text(encoding="utf-8")
        for name, body in (("head", lambda: head(page, lang, text)),
                           ("header", lambda: header(page, lang)),
                           ("footer", lambda: footer(page, lang, projects)),
                           ("orbs", lambda: orbs(page, lang, projects)),
                           ("testimonials", lambda: testimonials(lang, quotes))):
            if f"<!-- @{name} -->" in text:
                text = fill(text, name, body())
        write(ROOT / page, text)
    write(ROOT / "sitemap.xml", sitemap())


if __name__ == "__main__":
    main()
