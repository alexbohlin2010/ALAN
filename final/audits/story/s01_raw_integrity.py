"""Audit s01: raw radiance + boundary files untouched (SHA-256 and size vs both MANIFESTs),
no stray files (e.g. .aux.xml) under data/raw/, and a fingerprint of the audited outputs,
pipeline scripts and COGs (to detect a concurrent change during the audit).

  .venv/bin/python audits/story/s01_raw_integrity.py start|end
Output: audits/story/results/s01_raw_integrity_<tag>.json
"""
import os, sys, time
from common import (FINAL, RAD_RAW, BND_RAW, COG, OUT_GLOBAL, OUT_COUNTRY, read_manifest,
                    sha256, write_result)


def check_manifest(folder):
    rows = read_manifest(folder / "MANIFEST.csv")
    out, ok = [], True
    for r in rows:
        p = folder / r["path"]
        st = p.stat()
        got = sha256(p)
        good = got == r["sha256"] and st.st_size == int(r["size_bytes"])
        ok &= good
        out.append(dict(path=str(p.relative_to(FINAL)), sha256=got, manifest_sha256=r["sha256"],
                        size=st.st_size, manifest_size=int(r["size_bytes"]), mtime=st.st_mtime,
                        pass_=good))
    listed = {str((folder / r["path"]).resolve()) for r in rows} | {str((folder / "MANIFEST.csv").resolve())}
    present = set()
    for d, _, files in os.walk(folder):
        for n in files:
            if n != ".DS_Store":
                present.add(str((Path(d) / n).resolve()))
    unexpected = sorted(present - listed)
    return out, ok and not unexpected, unexpected


from pathlib import Path


def main():
    tag = sys.argv[1] if len(sys.argv) > 1 else "run"
    res = {"tag": tag, "utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "pass": True}
    for name, folder in (("radiance", RAD_RAW), ("boundaries", BND_RAW)):
        files, ok, unexpected = check_manifest(folder)
        res[name] = dict(files=files, unexpected_files=unexpected, pass_=ok)
        res["pass"] &= ok
    fp = {}
    for p in [OUT_GLOBAL, OUT_COUNTRY, FINAL / "pipeline/story/01_radiance_change.py",
              FINAL / "pipeline/story/02_country_change.py", COG[2015], COG[2025]]:
        fp[str(p.relative_to(FINAL))] = dict(sha256=sha256(p), mtime=p.stat().st_mtime)
    res["fingerprint_not_raw"] = fp
    write_result(f"s01_raw_integrity_{tag}.json", res)
    print("PASS" if res["pass"] else "FAIL")


if __name__ == "__main__":
    main()
