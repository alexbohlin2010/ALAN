"""Compare independent extraction (a01) with data/derived/impacts/spectra_278.json. Reads only JSON outputs."""
import json, math
A = json.load(open("audits/impacts_spectra/results/a01_extract.json"))
D = json.load(open("data/derived/impacts/spectra_278.json"))
out = []
def P(*a):
    s = " ".join(str(x) for x in a); print(s); out.append(s)
# curve identity: legend swatch y (a01_log): blue swatch y=144.14 next to 'Short' (148.33); magenta 153.08 next to 'Long' (157.27)
mp = {"short": "blue", "long": "magenta"}
P("Pipeline stroke short:", D["curves"]["short"]["stroke"], "| long:", D["curves"]["long"]["stroke"])
for k in ("short", "long"):
    c = A["curves"][mp[k]]; s = D["curves"][k]["samples"]
    P(f"[{k}] n_mine={c['n']} n_pipeline={len(s)} n_field={D['curves'][k]['n']} colour_match={c['colour']==D['curves'][k]['stroke'][4:-1]}")
    dn = max(abs(a - b[0]) for a, b in zip(c["nm"], s)); dv = max(abs(a - b[1]) for a, b in zip(c["value"], s))
    i = max(range(len(s)), key=lambda i: abs(c["value"][i]-s[i][1]))
    P(f"[{k}] max|dnm|={dn:.5f} (pipeline rounds to 0.01) max|dvalue|={dv:.6f} (pipeline rounds to 1e-5); worst value idx {i}: mine {c['value'][i]:.6f} pipeline {s[i][1]}")
    nm = c["nm"]; v = c["value"]
    imax = max(range(len(v)), key=lambda i: v[i])
    P(f"[{k}] my global max {v[imax]:.5f} at {nm[imax]:.2f} nm; pipeline {D['curves'][k]['peak_value_extracted']} at {D['curves'][k]['peak_nm_extracted']}")
    # local maxima (strict, window +-5 samples, value > 0.5*global)
    loc = [(round(nm[i],2), round(v[i],5)) for i in range(5, len(v)-5) if v[i] == max(v[i-5:i+6]) and v[i] > 0.3*v[imax]]
    P(f"[{k}] local maxima (+-5 samples window, >30% of max): {loc}")
    near = lambda t: max((i for i in range(len(nm)) if abs(nm[i]-t) < 3), key=lambda i: v[i])
    tgt = 478 if k == "short" else 608
    j = near(tgt); P(f"[{k}] max within +-3 nm of caption {tgt}: {v[j]:.5f} at {nm[j]:.2f} nm (= {v[j]/v[imax]*100:.1f}% of global max)")
    mono = all(nm[i] < nm[i+1] for i in range(len(nm)-1)); P(f"[{k}] my nm strictly increasing: {mono}; range {nm[0]:.2f}-{nm[-1]:.2f}; min value mine {min(v):.6f}")
    # integrals (value x nm, trapezoid), mW/m2 if values are per nm
    for lab, xs, ys in (("mine", nm, v), ("pipeline", [q[0] for q in s], [q[1] for q in s])):
        I = sum((xs[i+1]-xs[i])*(ys[i+1]+ys[i])/2 for i in range(len(xs)-1))
        P(f"[{k}] trapezoid integral ({lab}) = {I:.3f} value*nm  (documented {D['documented'][k]['irradiance_W_m2']*1000:.0f} mW/m2) ratio {I/(D['documented'][k]['irradiance_W_m2']*1000):.3f}")
    # pipeline invariants
    pn = [q[0] for q in s]; pv = [q[1] for q in s]
    P(f"[{k}] pipeline nm strictly increasing: {all(pn[i]<pn[i+1] for i in range(len(pn)-1))}; range {pn[0]}-{pn[-1]}; negatives: {sum(1 for x in pv if x<0)} (min {min(pv)}); duplicates nm: {len(pn)-len(set(pn))}")
P("top-level keys:", list(D.keys()), "| label:", D.get("label"), "| units:", D.get("units"))
open("audits/impacts_spectra/results/a02_compare.txt", "w").write("\n".join(out) + "\n")
