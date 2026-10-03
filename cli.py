"""Use: python cli.py samples/pdf_merge_tool.html --theme dark --api https://your-api.onrender.com"""
import argparse, pathlib
from core.pipeline import process, make_zip
from core.generator import list_themes
p = argparse.ArgumentParser(); p.add_argument("html")
p.add_argument("--theme", default="clean", choices=list_themes()); p.add_argument("--api", default="")
p.add_argument("--confirm", nargs="*", default=[], help="function names jinhe shared maan lo")
a = p.parse_args()
f = pathlib.Path(a.html)
r = process(f.read_text(encoding="utf-8"), f.stem, a.theme, a.api, set(a.confirm))
out = pathlib.Path("out"); out.mkdir(exist_ok=True)
(out / f"{f.stem}.zip").write_bytes(make_zip(r))
print(r["report"]); print(f"\nZIP: out/{f.stem}.zip")
