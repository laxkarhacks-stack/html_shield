"""FastAPI server.  Run: uvicorn server:app --reload
 POST /analyze           (html file upload) -> ZIP
 POST /api/fn/{fn_id}    shared function call (generated apps yahi hit karte hain)
 GET  /theme/{n}.css, /shield.js, /lib/*"""
import json, importlib.util, pathlib
from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response, FileResponse, HTMLResponse
from core.pipeline import process, make_zip
from core.generator import list_themes
from core.matcher import load_registry

ROOT = pathlib.Path(__file__).parent
ALLOWED_ORIGINS = ["*"]   # PRODUCTION me apni domains daalo: ["https://tumhari-site.vercel.app"]
app = FastAPI(title="HTML Shield")
app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS, allow_methods=["*"], allow_headers=["*"])

@app.post("/analyze")
async def analyze_html(file: UploadFile = File(...), theme: str = Form("clean"), api: str = Form("")):
    if theme not in list_themes(): raise HTTPException(400, "bad theme")
    html = (await file.read()).decode("utf-8", "ignore")
    r = process(html, pathlib.Path(file.filename).stem, theme, api)      # sirf padhna, execute nahi
    return Response(make_zip(r), media_type="application/zip",
                    headers={"Content-Disposition": f'attachment; filename="{pathlib.Path(file.filename).stem}.zip"'})

@app.post("/analyze/preview", response_class=HTMLResponse)
async def preview(file: UploadFile = File(...), theme: str = Form("clean")):
    return process((await file.read()).decode("utf-8", "ignore"), "preview", theme)["preview"]

@app.post("/api/fn/{fn_id}")
async def call_fn(fn_id: str, request: Request):
    reg = load_registry()["functions"]
    if fn_id not in reg: raise HTTPException(404, "unknown function")   # sirf registry wale, path traversal nahi
    form = await request.form()
    args = []
    for m in json.loads(form["meta"]):
        if "v" in m: args.append(m["v"])
        else: args.append([await form[k].read() for k in m["f"]])
    spec = importlib.util.spec_from_file_location(fn_id, ROOT / "shared/functions" / reg[fn_id]["file"])
    mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
    try: result = mod.run(args)
    except Exception as e: raise HTTPException(400, str(e))
    if isinstance(result, tuple): return Response(result[1], media_type=result[0])
    return result

@app.get("/theme/{name}.css")
def theme(name: str):
    if name not in list_themes(): raise HTTPException(404)
    return FileResponse(ROOT / f"shared/themes/{name}.css", media_type="text/css")

@app.get("/shield.js")
def shield(): return FileResponse(ROOT / "shared/shield.js", media_type="application/javascript")

app.mount("/lib", __import__("fastapi.staticfiles", fromlist=["x"]).StaticFiles(directory=ROOT / "shared/libs", check_dir=False))
