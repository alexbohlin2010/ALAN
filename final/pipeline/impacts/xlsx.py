"""Minimal read-only .xlsx reader (Python standard library only: zipfile + XML).

Reads the first worksheet into a header list and a list of row lists (cell values as
strings, empty cells as None). Numbers stay as the text stored in the file, so nothing is
re-rounded. Used because the project's .venv has no openpyxl/pandas (no new dependency).
"""
import re
import zipfile
import xml.etree.ElementTree as ET

NS = "{http://schemas.openxmlformats.org/spreadsheetml/2006/main}"


def _col_index(ref):
    n = 0
    for ch in re.match(r"[A-Z]+", ref).group():
        n = n * 26 + ord(ch) - 64
    return n - 1


def _text(node):
    return "".join(t.text or "" for t in node.iter(f"{NS}t"))


def read_first_sheet(path):
    with zipfile.ZipFile(path) as z:
        shared = []
        if "xl/sharedStrings.xml" in z.namelist():
            shared = [_text(si) for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall(f"{NS}si")]
        sheet = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
    rows = []
    for row in sheet.iter(f"{NS}row"):
        cells = {}
        for c in row.findall(f"{NS}c"):
            v = c.find(f"{NS}v")
            if v is None:
                inline = c.find(f"{NS}is")
                val = _text(inline) if inline is not None else None
            elif c.get("t") == "s":
                val = shared[int(v.text)]
            else:
                val = v.text
            cells[_col_index(c.get("r"))] = val
        rows.append(cells)
    width = max(rows[0]) + 1
    header = [rows[0].get(i) for i in range(width)]
    data = [[r.get(i) for i in range(width)] for r in rows[1:] if r]
    return header, data
