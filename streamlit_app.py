import streamlit as st
import streamlit.components.v1 as components
import tempfile
from pathlib import Path
from core.pipeline import process, make_zip
from core.generator import list_themes

st.title("HTML Shield")

f = st.file_uploader("HTML file upload karo", type=["html", "htm"])
theme = st.selectbox("Theme", list_themes())
api = st.text_input(
    "API URL",
    value="https://literate-space-sniffle-gxrrj7p6g9j729jwg-8000.app.github.dev"
)

if f and st.button("Banao"):
    html = f.read().decode("utf-8", "ignore")

    r = process(
        html,
        f.name.rsplit(".", 1)[0],
        theme,
        api.strip().rstrip("/")
    )

    st.markdown(r["report"])

    st.subheader("Preview")

    # Generated app ko actual HTML file ki tarah serve karne ke liye
    preview_dir = Path(tempfile.mkdtemp())
    preview_file = preview_dir / "index.html"
    preview_file.write_text(r["app_html"], encoding="utf-8")

    st.code(str(preview_file))

    components.html(
        r["app_html"],
        height=600,
        scrolling=True
    )

    st.download_button(
        "ZIP download",
        make_zip(r),
        file_name="app.zip"
    )
