"""Step 10 (Report), 12 (Live Preview), 13 (ZIP) + poori pipeline."""
import io, json, html as _html, zipfile
from .design_remover import remove_design
from .analyzer import analyze
from .matcher import load_registry, match_all
from .generator import generate_app, build_manifest

def make_report(name, manifest, matches, design):
    L = [f"# Report: {name}", "",
         f"- Size: {manifest['size_bytes']['original']} -> {manifest['size_bytes']['generated']} bytes",
         f"- Design removed: {design['removed']}", f"- Theme: {manifest['theme']}", "",
         "## Functions"]
    for m in matches["functions"]:
        icon = {"auto": "[API]", "confirm": "[CONFIRM?]", "none": "[page me rahega]"}[m["status"]]
        L.append(f"- `{m['name']}` {icon} -> {m['id'] or '-'} (confidence {m['confidence']})")
    L += ["", "## Libraries"] + [f"- {l['lib']} ({'shared' if l['shared'] else 'original CDN'})" for l in matches["libraries"]]
    if manifest["needs_confirm"]:
        L += ["", "## Tumhe confirm karna hai", *[f"- `{n}` shared function lag raha hai. Sahi hai?" for n in manifest["needs_confirm"]]]
    zero = [m["name"] for m in matches["functions"] if m["status"] == "auto" and not m["params"]]
    if zero:
        L += ["", "## Dhyan do", *[f"- `{n}` ke koi params nahi - wo DOM se khud padhta tha, stub ko wire karna padega." for n in zero]]
    return "\n".join(L)

def make_preview(app_html: str) -> str:
    # sandbox: scripts chalein par origin/cookies/top-navigation nahi
    return ('<!doctype html><meta charset="utf-8"><title>Preview</title>'
            '<iframe sandbox="allow-scripts allow-forms allow-downloads" style="width:100%;height:95vh;border:1px solid #888" '
            f'srcdoc="{_html.escape(app_html, quote=True)}"></iframe>')

def process(html: str, name="app", theme="clean", api="", confirmed=None) -> dict:
    reg = load_registry()
    design = remove_design(html)
    analysis = analyze(html)                      # original html se JS analysis
    matches = match_all(analysis, reg, confirmed)
    app_html, removed = generate_app(design["html"], analysis, matches, reg, theme, api)
    manifest = build_manifest(name, matches, theme, api, removed, len(html.encode()), len(app_html.encode()))
    report = make_report(name, manifest, matches, design)
    return {"app_html": app_html, "manifest": manifest, "report": report,
            "preview": make_preview(app_html), "design_css": design["css"], "matches": matches}

def make_zip(r: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr("index.html", r["app_html"])
        z.writestr("manifest.json", json.dumps(r["manifest"], indent=2, ensure_ascii=False))
        z.writestr("report.md", r["report"])
        z.writestr("preview.html", r["preview"])
        z.writestr("original_design.css", r["design_css"])
    return buf.getvalue()
