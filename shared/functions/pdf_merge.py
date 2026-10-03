"""Shared function: pdf.merge  -- ek baar likho, har app yahin se call kare."""
import io
from pypdf import PdfWriter, PdfReader

def run(args: list):
    files = args[0]                       # list[bytes]
    if not files: raise ValueError("koi PDF nahi mili")
    w = PdfWriter()
    for b in files:
        for page in PdfReader(io.BytesIO(b)).pages:
            w.add_page(page)
    out = io.BytesIO(); w.write(out)
    return "application/pdf", out.getvalue()
