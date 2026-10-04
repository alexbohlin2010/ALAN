"""Recheck2 q03: strict JSON validity of the 3 outputs: UTF-8, parses with no NaN/Infinity constants and no duplicate
keys (at any depth), no NaN/Infinity tokens outside string literals, every number token matches the JSON grammar.
Writes results/q03_strict_json.txt."""
import json, re
R = "audits/night_spectra/recheck2_2026-10-04/results"
NUM = re.compile(r"-?(0|[1-9]\d*)(\.\d+)?([eE][+-]?\d+)?")
L = []
for f in ("philadelphia.json", "cherry_springs.json", "spectra_meta.json"):
    p = f"data/derived/spectra/{f}"
    text = open(p, "rb").read().decode("utf-8")  # raises if not UTF-8
    consts, dups, nums = [], [], [0, 0]
    def pc(name): consts.append(name); return None
    def hook(pairs):
        ks = [k for k, _ in pairs]
        if len(ks) != len(set(ks)): dups.append(ks)
        return dict(pairs)
    def num(s):
        nums[0] += 1
        if not NUM.fullmatch(s): nums[1] += 1
        return s
    json.loads(text, parse_constant=pc, object_pairs_hook=hook, parse_float=num, parse_int=num)
    outside = re.sub(r'"(?:[^"\\]|\\.)*"', '""', text)  # strip string literals
    bad_tokens = re.findall(r"NaN|Infinity", outside)
    ok = not consts and not dups and not bad_tokens and nums[1] == 0
    L.append(f"{'PASS' if ok else 'FAIL'} {f}: utf-8 ok; constants {consts}; duplicate-key objects {len(dups)}; "
             f"NaN/Infinity outside strings {len(bad_tokens)}; number tokens {nums[0]}, non-grammar {nums[1]}; "
             f"null outside strings {len(re.findall(r'null', outside))}")
open(f"{R}/q03_strict_json.txt", "w").write("\n".join(L) + "\n")
print("\n".join(L))
