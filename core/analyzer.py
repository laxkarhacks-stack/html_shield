"""Step 02 (Function Detector) + 03 (Dependency Detector) + 05 (Function Extractor).
Sirf STATIC analysis - user ka code kabhi execute nahi hota."""
import re
from bs4 import BeautifulSoup

def _match_brace(s: str, i: int) -> int:
    """'{' at s[i] ka matching '}' dhoondta hai (strings/comments skip karke)."""
    depth, n, j = 0, len(s), i
    while j < n:
        c = s[j]
        if s.startswith("//", j):
            j = s.find("\n", j); j = n if j < 0 else j; continue
        if s.startswith("/*", j):
            j = s.find("*/", j); j = n if j < 0 else j + 2; continue
        if c in "'\"`":
            q = c; j += 1
            while j < n and s[j] != q:
                j += 2 if s[j] == "\\" else 1
        elif c == "{": depth += 1
        elif c == "}":
            depth -= 1
            if depth == 0: return j
        j += 1
    return -1

_DECL = re.compile(r"(?:async\s+)?function\s*\*?\s*([A-Za-z_$][\w$]*)\s*\(([^)]*)\)\s*\{")
_ARROW = re.compile(r"(?:const|let|var)\s+([A-Za-z_$][\w$]*)\s*=\s*(?:async\s*)?(?:function\s*\(([^)]*)\)|\(([^)]*)\)\s*=>|([A-Za-z_$][\w$]*)\s*=>)\s*\{")

def detect_functions(js: str) -> list[dict]:
    found = []
    for rx in (_DECL, _ARROW):
        for m in rx.finditer(js):
            params = next((g for g in m.groups()[1:] if g is not None), "")
            cb = _match_brace(js, m.end() - 1)
            if cb < 0: continue
            found.append({"name": m.group(1), "params": [p.strip() for p in params.split(",") if p.strip()],
                          "start": m.start(), "end": cb + 1, "source": js[m.start():cb + 1]})
    found.sort(key=lambda f: f["start"])
    top, last_end = [], -1          # nested functions hatao, sirf top-level
    for f in found:
        if f["start"] >= last_end:
            top.append(f); last_end = f["end"]
    return top

def build_call_graph(funcs: list[dict]) -> None:
    names = {f["name"] for f in funcs}
    for f in funcs:
        f["calls"] = sorted({n for n in re.findall(r"\b([A-Za-z_$][\w$]*)\s*\(", f["source"])
                             if n in names and n != f["name"]})

def extract_with_helpers(name: str, funcs: list[dict]) -> list[dict]:
    """Step 05: function + uske saare helper functions."""
    by = {f["name"]: f for f in funcs}; out, seen, stack = [], set(), [name]
    while stack:
        n = stack.pop()
        if n in seen or n not in by: continue
        seen.add(n); out.append(by[n]); stack.extend(by[n]["calls"])
    return out

KNOWN_LIBS = {
    "pdf-lib": (r"pdf-lib", r"\bPDFLib\b"), "jspdf": (r"jspdf", r"\bjsPDF\b|window\.jspdf"),
    "pdfjs": (r"pdf(\.min)?\.js|pdfjs", r"\bpdfjsLib\b"), "jszip": (r"jszip", r"\bJSZip\b"),
    "html2canvas": (r"html2canvas", r"\bhtml2canvas\b"), "filesaver": (r"filesaver", r"\bsaveAs\s*\("),
    "chartjs": (r"chart(\.min)?\.js|chart\.js", r"\bnew Chart\b"), "jquery": (r"jquery", r"\$\(|\bjQuery\b"),
    "tesseract": (r"tesseract", r"\bTesseract\b"), "marked": (r"marked", r"\bmarked\("),
}

def detect_dependencies(soup: BeautifulSoup, js: str) -> dict:
    ext = [s["src"] for s in soup.find_all("script", src=True)]
    libs = []
    for lib, (url_rx, glob_rx) in KNOWN_LIBS.items():
        urls = [u for u in ext if re.search(url_rx, u, re.I)]
        if urls or re.search(glob_rx, js):
            libs.append({"lib": lib, "urls": urls})
    return {"external_scripts": ext, "libraries": libs,
            "imports": re.findall(r"import\s+.*?from\s+['\"]([^'\"]+)['\"]", js)}

def analyze(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    js = "\n".join(s.get_text() for s in soup.find_all("script") if not s.get("src"))
    funcs = detect_functions(js); build_call_graph(funcs)
    return {"functions": funcs, "dependencies": detect_dependencies(soup, js), "js": js}
