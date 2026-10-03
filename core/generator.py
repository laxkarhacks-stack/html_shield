"""Step 07 (App Generator) + 08 (Shared UI themes) + 09 (Manifest)."""
import re, json, pathlib, datetime
from bs4 import BeautifulSoup
from jinja2 import Environment, FileSystemLoader
from .analyzer import extract_with_helpers, KNOWN_LIBS

ROOT = pathlib.Path(__file__).parent.parent
env = Environment(loader=FileSystemLoader(ROOT / "templates"), autoescape=False)

def list_themes(): return sorted(p.stem for p in (ROOT / "shared/themes").glob("*.css"))

def _rewrite_js(analysis, matches):
    js, funcs = analysis["js"], analysis["functions"]
    by_name = {f["name"]: f for f in funcs}
    moved = {m["name"]: m for m in matches["functions"] if m["status"] == "auto"}
    remove = set(moved)
    # helpers jo sirf moved functions use karte the, wo bhi hat jayein
    for name in moved:
        for h in extract_with_helpers(name, funcs)[1:]:
            users = [f["name"] for f in funcs if h["name"] in f["calls"]]
            if all(u in remove for u in users): remove.add(h["name"])
    for f in sorted(funcs, key=lambda x: -x["start"]):
        if f["name"] in remove:
            if f["name"] in moved:
                stub = f'async function {f["name"]}(...a){{return shield.call("{moved[f["name"]]["id"]}",a)}}'
            else: stub = ""
            js = js[:f["start"]] + stub + js[f["end"]:]
    return re.sub(r"\n{3,}", "\n\n", js).strip(), sorted(remove)

def generate_app(stripped_html, analysis, matches, reg, theme="clean", api=""):
    soup = BeautifulSoup(stripped_html, "html.parser")
    title = soup.title.get_text() if soup.title else "App"
    for s in soup.find_all("script"): s.decompose()
    body = "".join(str(c) for c in (soup.body.contents if soup.body else soup.contents)).strip()
    js, removed = _rewrite_js(analysis, matches)
    lib_scripts = []
    for lib in matches["libraries"]:
        if not re.search(KNOWN_LIBS[lib["lib"]][1], js): continue   # ab zarurat nahi
        if lib["shared"] and api: lib_scripts.append(api + reg["libraries"][lib["lib"]]["src"])
        else: lib_scripts += lib["urls"]
    theme_css = (ROOT / f"shared/themes/{theme}.css").read_text()
    shield_js = (ROOT / "shared/shield.js").read_text()
    html = env.get_template("app.html.j2").render(title=title, api=api, theme=theme, theme_css=theme_css,
        shield_js=shield_js, lib_scripts=lib_scripts, body=body, js=js)
    return html, removed

def build_manifest(name, matches, theme, api, removed, orig_size, new_size):
    return {"app": name, "created": datetime.datetime.now().isoformat(timespec="seconds"),
            "theme": theme, "api": api or None,
            "shared_functions": sorted({m["id"] for m in matches["functions"] if m["status"] == "auto"}),
            "needs_confirm": [m["name"] for m in matches["functions"] if m["status"] == "confirm"],
            "kept_in_page": [m["name"] for m in matches["functions"] if m["status"] != "auto" and m["name"] not in removed],
            "libraries": [l["lib"] for l in matches["libraries"]],
            "size_bytes": {"original": orig_size, "generated": new_size}}
