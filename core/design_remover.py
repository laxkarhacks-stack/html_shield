"""Step 01 - Design Remover: HTML se saari design (CSS) hata deta hai.
Structure, id, class, onclick, JS sab same rehta hai (kyunki JS unpe depend karta hai)."""
from bs4 import BeautifulSoup, Comment

def remove_design(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    css_parts, removed = [], {"style_tags": 0, "style_attrs": 0, "css_links": 0}

    for tag in soup.find_all("style"):
        css_parts.append(tag.get_text()); tag.decompose(); removed["style_tags"] += 1

    for tag in soup.find_all("link"):
        rel = " ".join(tag.get("rel", [])).lower()
        href = tag.get("href", "")
        if "stylesheet" in rel or href.lower().endswith(".css"):
            css_parts.append(f"/* external: {href} */"); tag.decompose(); removed["css_links"] += 1

    for tag in soup.find_all(True):
        if tag.has_attr("style"):
            css_parts.append(f"/* inline {tag.name}#{tag.get('id','')} */ {tag['style']}")
            del tag["style"]; removed["style_attrs"] += 1
        if tag.name not in ("canvas", "img", "svg"):
            for a in ("bgcolor", "color", "align", "border", "width", "height"):
                if tag.has_attr(a): del tag[a]

    for c in soup.find_all(string=lambda s: isinstance(s, Comment)):
        c.extract()

    return {"html": str(soup), "css": "\n".join(css_parts), "removed": removed}
