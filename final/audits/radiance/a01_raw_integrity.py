"""Audit a01: raw files are untouched. SHA-256, size and mtime vs MANIFEST; folder listing.

Run at the start and at the end of the audit:
  .venv/bin/python audits/radiance/a01_raw_integrity.py start|end
Output: audits/radiance/results/a01_raw_integrity_<tag>.json
"""
import os, sys
from common import RAW_DIR, YEARS, manifest_rows, raw_path, sha256, write_result


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else "run"
    rows = manifest_rows()
    out = {"tag": tag, "listing": sorted(os.listdir(RAW_DIR)), "files": {}, "pass": True}
    for y in YEARS:
        p = raw_path(y)
        st = p.stat()
        got = sha256(p)
        ok = got == rows[y]["sha256"] and st.st_size == int(rows[y]["size_bytes"])
        out["files"][y] = dict(filename=p.name, sha256=got, manifest_sha256=rows[y]["sha256"],
                               size=st.st_size, manifest_size=int(rows[y]["size_bytes"]),
                               mtime=st.st_mtime, writable_by_owner=bool(st.st_mode & 0o200),
                               pass_=ok)
        out["pass"] &= ok
    # Nothing besides the two raw files (e.g. no .aux.xml left by GDAL)
    out["unexpected_entries"] = [n for n in out["listing"]
                                 if n not in {raw_path(y).name for y in YEARS}]
    out["pass"] &= not out["unexpected_entries"]
    write_result(f"a01_raw_integrity_{tag}.json", out)
    print("PASS" if out["pass"] else "FAIL")


if __name__ == "__main__":
    main()
