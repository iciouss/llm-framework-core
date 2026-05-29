import io
import json
import os
import tempfile
import zipfile
from pathlib import Path

from llm_framework.extensions.rag._converter import to_markdown


def write_tmp(suffix: str, content: str | bytes) -> Path:
    mode = "wb" if isinstance(content, bytes) else "w"
    f = tempfile.NamedTemporaryFile(suffix=suffix, mode=mode, delete=False)
    f.write(content)
    f.close()
    return Path(f.name)


def test_plain_text():
    p = write_tmp(".txt", "Hello plain text.")
    result = to_markdown(p)
    assert "Hello plain text." in result
    os.unlink(p)
    print("plain text: OK")
    print(result)


def test_markdown_passthrough():
    p = write_tmp(".md", "# Title\n\nParagraph content.")
    result = to_markdown(p)
    assert "# Title" in result and "Paragraph content" in result
    os.unlink(p)
    print("markdown passthrough: OK")
    print(result)


def test_html():
    src = "<html><body><h1>Title</h1><script>var x=1;</script><p>Body text</p><ul><li>Item</li></ul></body></html>"
    p = write_tmp(".html", src)
    result = to_markdown(p)
    assert "Title" in result, f"title missing: {result!r}"
    assert "Body text" in result, f"body text missing: {result!r}"
    assert "Item" in result, f"list item missing: {result!r}"
    assert "var x" not in result, f"script not stripped: {result!r}"
    os.unlink(p)
    print("html: OK")
    print(result)


def test_xml():
    src = (
        """<?xml version="1.0"?><root><item>Value A</item><item>Value B</item></root>"""
    )
    p = write_tmp(".xml", src)
    result = to_markdown(p)
    assert "Value A" in result and "Value B" in result, f"xml text missing: {result!r}"
    os.unlink(p)
    print("xml: OK")
    print(result)


def test_ipynb_cell_types():
    nb = {
        "metadata": {"kernelspec": {"language": "python"}},
        "cells": [
            {
                "cell_type": "markdown",
                "source": ["# Notebook Title\n", "Some explanation."],
            },
            {"cell_type": "code", "source": "print(42)"},
        ],
    }
    p = write_tmp(".ipynb", json.dumps(nb))
    result = to_markdown(p)
    assert "# Notebook Title" in result, f"markdown cell heading missing: {result!r}"
    assert "Some explanation" in result, f"markdown cell text missing: {result!r}"
    assert "```python" in result, f"code fence missing: {result!r}"
    assert "print(42)" in result, f"code content missing: {result!r}"
    os.unlink(p)
    print("ipynb cell types: OK")
    print(result)


def test_docx_plain_paragraph():
    W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    doc_xml = f"""<?xml version="1.0"?>
<w:document xmlns:w="{W}">
  <w:body>
    <w:p><w:r><w:t>Simple paragraph text.</w:t></w:r></w:p>
  </w:body>
</w:document>"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("word/document.xml", doc_xml)
    p = write_tmp(".docx", buf.getvalue())
    result = to_markdown(p)
    assert "Simple paragraph text" in result, f"docx text missing: {result!r}"
    os.unlink(p)
    print("docx plain paragraph: OK")
    print(result)


def test_docx_headings():
    W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
    doc_xml = f"""<?xml version="1.0"?>
<w:document xmlns:w="{W}">
  <w:body>
    <w:p>
      <w:pPr><w:pStyle w:val="Heading1"/></w:pPr>
      <w:r><w:t>Chapter One</w:t></w:r>
    </w:p>
    <w:p>
      <w:pPr><w:pStyle w:val="Heading2"/></w:pPr>
      <w:r><w:t>Section A</w:t></w:r>
    </w:p>
    <w:p><w:r><w:t>Body text here.</w:t></w:r></w:p>
  </w:body>
</w:document>"""
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as zf:
        zf.writestr("word/document.xml", doc_xml)
    p = write_tmp(".docx", buf.getvalue())
    result = to_markdown(p)
    assert "# Chapter One" in result, f"h1 missing: {result!r}"
    assert "## Section A" in result, f"h2 missing: {result!r}"
    assert "Body text here" in result, f"body missing: {result!r}"
    os.unlink(p)
    print("docx headings: OK")
    print(result)


def test_unknown_extension_fallback():
    p = write_tmp(".log", "Log line one.\nLog line two.")
    result = to_markdown(p)
    assert "Log line" in result, f"fallback text missing: {result!r}"
    os.unlink(p)
    print("unknown extension fallback: OK")
    print(result)


def main():
    test_plain_text()
    test_markdown_passthrough()
    test_html()
    test_xml()
    test_ipynb_cell_types()
    test_docx_plain_paragraph()
    test_docx_headings()
    test_unknown_extension_fallback()
    print("\nAll rag format tests passed.")


main()
