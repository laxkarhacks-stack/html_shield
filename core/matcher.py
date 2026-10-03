"""Step 04 (Function matcher) + 06 (Library matcher): registry se milata hai."""
import json, re, hashlib, pathlib
REG_PATH = pathlib.Path(__file__).parent.parent / "shared" / "registry.json"

def load_registry() -> dict:
    return json.loads(REG_PATH.read_text(encoding="utf-8"))

def norm_hash(src: str) -> str:
    s = re.sub(r"//.*|/\*.*?\*/", "", src, flags=re.S)
    s = re.sub(r"\bfunction\s+[\w$]+", "function", s)   # naam se farak na pade
    return hashlib.sha256(re.sub(r"\s+", "", s).encode()).hexdigest()[:16]

def match_function(fn: dict, reg: dict) -> dict:
    h = norm_hash(fn["source"])
    if h in reg["hashes"]:
        return {"id": reg["hashes"][h], "confidence": 1.0, "status": "auto", "hash": h}
    text = (fn["name"] + " " + fn["source"]).lower()
    best = {"id": None, "confidence": 0.0, "status": "none", "hash": h}
    for fid, e in reg["functions"].items():
        score = sum(k in text for k in e["keywords"]) / len(e["keywords"])
        if score > best["confidence"]:
            best = {"id": fid, "confidence": round(score, 2), "hash": h,
                    "status": "auto" if score >= e["auto_threshold"] else
                              "confirm" if score >= e["confirm_threshold"] else "none"}
    if best["status"] == "none": best["id"] = None
    return best

def match_all(analysis: dict, reg: dict, confirmed: set | None = None) -> dict:
    """confirmed = user ne jo function names 'haan' bole."""
    confirmed = confirmed or set()
    funcs, libs = [], []
    for f in analysis["functions"]:
        m = match_function(f, reg)
        if m["status"] == "confirm" and f["name"] in confirmed: m["status"] = "auto"
        funcs.append({"name": f["name"], "params": f["params"], **m})
    for d in analysis["dependencies"]["libraries"]:
        libs.append({**d, "shared": d["lib"] in reg["libraries"]})
    return {"functions": funcs, "libraries": libs}
