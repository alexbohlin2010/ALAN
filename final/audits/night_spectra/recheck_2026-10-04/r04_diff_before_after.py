"""r04: diff NEW outputs (data/derived/spectra/) vs PREVIOUS outputs (pre-fix copy in the scratchpad).

Run from final/. Both read as text (parse_float=str, parse_int=str) and as floats.
Lists every key path added / removed / changed; for arrays reports how many elements differ
as text and as numbers. Writes results/r04_diff.txt.
"""
import json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
RES = os.path.join(HERE, "results")
BEFORE = ("/private/tmp/claude-501/-Users-lindaxiangyideng-Documents-GitHub-ALAN--claude-worktrees-"
          "cool-ishizaka-9fd75f/f4206848-779e-44ba-ac70-d5bff7e07f5c/scratchpad/spectra_before")
AFTER = "data/derived/spectra"
lines = []

def lt(p):
    return json.loads(open(p, encoding="utf-8").read(), parse_float=str, parse_int=str)

def lf(p):
    return json.loads(open(p, encoding="utf-8").read())

def flat(o, path=""):
    """leaf paths -> value; arrays of scalars kept whole."""
    out = {}
    if isinstance(o, dict):
        for k, v in o.items():
            out.update(flat(v, f"{path}.{k}" if path else k))
    else:
        out[path] = o
    return out

def count_diff(a, b):
    """element differences for (nested) lists."""
    if isinstance(a, list) and isinstance(b, list):
        if len(a) != len(b):
            return None
        return sum(count_diff(x, y) if isinstance(x, list) else (x != y) for x, y in zip(a, b))
    return int(a != b)

for fn in ["philadelphia.json", "cherry_springs.json", "spectra_meta.json"]:
    bt, at = flat(lt(f"{BEFORE}/{fn}")), flat(lt(f"{AFTER}/{fn}"))
    bf, af = flat(lf(f"{BEFORE}/{fn}")), flat(lf(f"{AFTER}/{fn}"))
    lines.append(f"== {fn}")
    added = [k for k in at if k not in bt]
    removed = [k for k in bt if k not in at]
    lines.append(f"  added ({len(added)}): {added}")
    lines.append(f"  removed ({len(removed)}): {removed}")
    for k in at:
        if k in bt:
            if at[k] != bt[k]:
                nt = count_diff(at[k], bt[k])
                nf = count_diff(af[k], bf[k])
                if isinstance(at[k], list):
                    lines.append(f"  CHANGED {k}: text-different elements {nt}, number-different elements {nf}")
                else:
                    lines.append(f"  CHANGED {k}: {bt[k]!r} -> {at[k]!r} (number-equal: {af[k] == bf[k]})")
            else:
                lines.append(f"  same    {k}")
    lines.append(f"  key order before: {list(lt(f'{BEFORE}/{fn}').keys())}")
    lines.append(f"  key order after:  {list(lt(f'{AFTER}/{fn}').keys())}")
open(os.path.join(RES, "r04_diff.txt"), "w").write("\n".join(lines) + "\n")
print("\n".join(lines))
