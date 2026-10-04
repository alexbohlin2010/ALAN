"""Audit s03: country masks, built independently of pipeline/story/02.

Method A (primary): own scanline point-in-polygon in numpy (even-odd rule over every ring of
the selected features; a pixel is inside if its centre is inside; edges straight in lon/lat,
as in the raster's plate-carree grid). Method B (cross-check): a separate GDAL RasterizeLayer
call (ALL_TOUCHED=FALSE) on the same grid. Method C: exact polygon area on the same sphere
(edges straight in lon/lat: integral of R^2 cos(lat) dlat dlon), compared with the mask area.

Selections (human decisions): India = countries ADMIN 'India'; Ukraine = countries ADMIN
'Ukraine'; France = map_units GEOUNIT 'France' (GU_A3 FXX), with and without Corsica.
Also: Crimea (disputed B89) vs Ukraine mask, Donetsk/Luhansk (C02/C03) vs Ukraine mask,
Corsica parts listed, overseas France absent.

  .venv/bin/python audits/story/s03_masks.py
Output: results/s03_masks.json, results/s03_masks.npz (packed masks + windows)
"""
import json, math, time
import numpy as np
from osgeo import gdal, ogr
from common import (COG, R_AUTHALIC, OUT_COUNTRY, open_layer, row_area_km2, centre_lat, centre_lon,
                    relerr, write_result, RESULTS)

CORSICA_BOX = (8.4, 41.3, 9.7, 43.1)   # lon_min, lat_min, lon_max, lat_max: generous box around the island


def features(layer, field, value):
    ds, L = open_layer(layer)
    out = []
    for f in L:
        if f.GetField(field) == value:
            out.append((f.GetField("GU_A3"), f.GetField("BRK_A3"), f.GetGeometryRef().Clone()))
    return out


def polygons(geom):
    """List of polygons, each a list of rings (Nx2 arrays of lon, lat)."""
    gtype = ogr.GT_Flatten(geom.GetGeometryType())
    parts = [geom] if gtype == ogr.wkbPolygon else [geom.GetGeometryRef(i) for i in range(geom.GetGeometryCount())]
    polys = []
    for p in parts:
        rings = []
        for k in range(p.GetGeometryCount()):
            r = p.GetGeometryRef(k)
            rings.append(np.array([(r.GetX(i), r.GetY(i)) for i in range(r.GetPointCount())], np.float64))
        polys.append(rings)
    return polys


def ring_area_km2(xy):
    """Signed area of a ring with edges straight in lon/lat, on a sphere of radius R."""
    lam = np.radians(xy[:, 0]); phi = np.radians(xy[:, 1])
    l1, l2, p1, p2 = lam[:-1], lam[1:], phi[:-1], phi[1:]
    dp = p2 - p1
    with np.errstate(invalid="ignore", divide="ignore"):
        term = np.where(np.abs(dp) > 1e-15, (l2 - l1) * (np.cos(p1) - np.cos(p2)) / dp, (l2 - l1) * np.sin(p1))
    return R_AUTHALIC ** 2 * term.sum() / 1e6


def poly_area_km2(polys):
    tot = 0.0
    for rings in polys:
        tot += abs(ring_area_km2(rings[0])) - sum(abs(ring_area_km2(h)) for h in rings[1:])
    return tot


def window_for(polys, gt, W, H):
    xs = np.concatenate([r[:, 0] for p in polys for r in p]); ys = np.concatenate([r[:, 1] for p in polys for r in p])
    c0 = max(int(math.floor((xs.min() - gt[0]) / gt[1])) - 2, 0)
    c1 = min(int(math.ceil((xs.max() - gt[0]) / gt[1])) + 2, W)
    r0 = max(int(math.floor((ys.max() - gt[3]) / gt[5])) - 2, 0)
    r1 = min(int(math.ceil((ys.min() - gt[3]) / gt[5])) + 2, H)
    return c0, r0, c1 - c0, r1 - r0


def scanline_mask(polys, gt, win):
    c0, r0, w, h = win
    segs = []
    for rings in polys:
        for r in rings:
            segs.append(np.column_stack([r[:-1], r[1:]]))
    E = np.concatenate(segs)                  # x1, y1, x2, y2
    x1, y1, x2, y2 = E.T
    xc = centre_lon(gt, np.arange(c0, c0 + w))
    m = np.zeros((h, w), bool)
    for i in range(h):
        y = centre_lat(gt, r0 + i)
        sel = (y1 > y) != (y2 > y)
        if not sel.any():
            continue
        xs = x1[sel] + (y - y1[sel]) * (x2[sel] - x1[sel]) / (y2[sel] - y1[sel])
        xs.sort()
        m[i] = (np.searchsorted(xs, xc, side="right") % 2) == 1
    return m


def gdal_mask(geoms, gt, win):
    c0, r0, w, h = win
    drv = gdal.GetDriverByName("MEM")
    ds = drv.Create("", w, h, 1, gdal.GDT_Byte)
    ds.SetGeoTransform((gt[0] + c0 * gt[1], gt[1], 0.0, gt[3] + r0 * gt[5], 0.0, gt[5]))
    mem = ogr.GetDriverByName("Memory" if ogr.GetDriverByName("MEM") is None else "MEM").CreateDataSource("")
    L = mem.CreateLayer("x", geom_type=ogr.wkbMultiPolygon)
    for g in geoms:
        f = ogr.Feature(L.GetLayerDefn()); f.SetGeometry(g); L.CreateFeature(f)
    gdal.RasterizeLayer(ds, [1], L, burn_values=[1], options=["ALL_TOUCHED=FALSE"])
    return ds.GetRasterBand(1).ReadAsArray().astype(bool)


def tight(m, win):
    rr = np.where(m.any(1))[0]; cc = np.where(m.any(0))[0]
    return dict(col0=int(win[0] + cc[0]), row0=int(win[1] + rr[0]),
                width=int(cc[-1] - cc[0] + 1), height=int(rr[-1] - rr[0] + 1))


def mask_area(m, gt, win):
    return float((m.sum(1) * row_area_km2(gt, np.arange(win[1], win[1] + win[3]))).sum())


def boundary_pixels(m):
    """Inside pixels with an outside 4-neighbour, and outside pixels with an inside 4-neighbour."""
    p = np.pad(m, 1)
    nb_out = ~p[:-2, 1:-1] | ~p[2:, 1:-1] | ~p[1:-1, :-2] | ~p[1:-1, 2:]
    nb_in = p[:-2, 1:-1] | p[2:, 1:-1] | p[1:-1, :-2] | p[1:-1, 2:]
    return m & nb_out, ~m & nb_in


def main():
    t0 = time.time()
    g = gdal.Open(str(COG[2015])); gt = g.GetGeoTransform(); W, H = g.RasterXSize, g.RasterYSize
    out = dict(geotransform=gt, areas={}, checks={})
    store = {}

    ind = features("ne_10m_admin_0_countries", "ADMIN", "India")
    ukr = features("ne_10m_admin_0_countries", "ADMIN", "Ukraine")
    fra = features("ne_10m_admin_0_map_units", "GEOUNIT", "France")
    out["checks"]["feature_counts"] = dict(India=len(ind), Ukraine=len(ukr), France_FXX=len(fra),
                                           France_GU_A3=[f[0] for f in fra])
    fra_polys = polygons(fra[0][2])
    parts = []
    for i, rings in enumerate(fra_polys):
        xy = rings[0]
        env = [float(xy[:, 0].min()), float(xy[:, 1].min()), float(xy[:, 0].max()), float(xy[:, 1].max())]
        corsica = (env[0] >= CORSICA_BOX[0] and env[1] >= CORSICA_BOX[1] and env[2] <= CORSICA_BOX[2] and env[3] <= CORSICA_BOX[3])
        parts.append(dict(index=i, envelope=env, area_km2=poly_area_km2([rings]), corsica=corsica, holes=len(rings) - 1))
    out["checks"]["france_parts"] = parts
    fra_no_cor = [p for p, d in zip(fra_polys, parts) if not d["corsica"]]

    def no_cor_geom():
        mp = ogr.Geometry(ogr.wkbMultiPolygon)
        for i, d in enumerate(parts):
            if not d["corsica"]:
                mp.AddGeometry(fra[0][2].GetGeometryRef(i).Clone())
        return mp

    defs = {"India": (polygons(ind[0][2]), [ind[0][2]]),
            "France (mainland incl. Corsica)": (fra_polys, [fra[0][2]]),
            "France (mainland excl. Corsica)": (fra_no_cor, [no_cor_geom()]),
            "Ukraine (excl. Crimea)": (polygons(ukr[0][2]), [ukr[0][2]])}
    theirs = json.loads(OUT_COUNTRY.read_text())["areas"]
    for name, (polys, geoms) in defs.items():
        win = window_for(polys, gt, W, H)
        mA = scanline_mask(polys, gt, win)
        mB = gdal_mask(geoms, gt, win)
        diff = mA ^ mB
        dr, dc = np.nonzero(diff)
        bi, bo = boundary_pixels(mA)
        a_mask = mask_area(mA, gt, win); a_poly = poly_area_km2(polys)
        tw = theirs[name]
        tt = tight(mA, win)
        lon = centre_lon(gt, [win[0], win[0] + win[2] - 1]); lat = centre_lat(gt, [win[1], win[1] + win[3] - 1])
        out["areas"][name] = dict(
            search_window=dict(col0=win[0], row0=win[1], width=win[2], height=win[3]),
            mask_tight_bbox=tt,
            mask_tight_bbox_lonlat=dict(lon_min=float(centre_lon(gt, tt["col0"])), lon_max=float(centre_lon(gt, tt["col0"] + tt["width"] - 1)),
                                        lat_max=float(centre_lat(gt, tt["row0"])), lat_min=float(centre_lat(gt, tt["row0"] + tt["height"] - 1))),
            pipeline_window=tw["window"],
            pipeline_window_contains_mask=(tw["window"]["col0"] <= tt["col0"] and tw["window"]["row0"] <= tt["row0"]
                                           and tw["window"]["col0"] + tw["window"]["width"] >= tt["col0"] + tt["width"]
                                           and tw["window"]["row0"] + tw["window"]["height"] >= tt["row0"] + tt["height"]),
            pixels_scanline=int(mA.sum()), pixels_gdal=int(mB.sum()), pixels_differ=int(diff.sum()),
            differing_pixels=[dict(row=int(win[1] + r), col=int(win[0] + c),
                                   lon=float(centre_lon(gt, win[0] + c)), lat=float(centre_lat(gt, win[1] + r)),
                                   scanline=bool(mA[r, c]), gdal=bool(mB[r, c])) for r, c in zip(dr[:50], dc[:50])],
            pipeline_pixels_inside=tw["pixels_inside"],
            area_mask_km2=a_mask, area_polygon_sphere_km2=a_poly,
            mask_vs_polygon_pct=100 * (a_mask - a_poly) / a_poly,
            pipeline_area_inside_km2=tw["area_inside_km2"],
            pipeline_area_relerr=relerr(a_mask, tw["area_inside_km2"]),
            boundary_inside_px=int(bi.sum()), boundary_outside_px=int(bo.sum()),
            n_polygons=len(polys), n_vertices=int(sum(len(r) for p in polys for r in p)))
        key = name.split(" ")[0] + ("_nocor" if "excl. Corsica" in name else "")
        store[key + "_mask"] = np.packbits(mA, axis=None); store[key + "_shape"] = np.array(mA.shape)
        store[key + "_win"] = np.array(win)
        print(name, out["areas"][name]["pixels_scanline"], out["areas"][name]["pipeline_pixels_inside"],
              "differ", int(diff.sum()), f"{time.time()-t0:.0f}s", flush=True)

    # --- disputed areas vs the Ukraine mask
    ds, L = open_layer("ne_10m_admin_0_disputed_areas")
    disp = {f.GetField("BRK_A3"): (f.GetField("NAME"), f.GetField("NOTE_BRK"), f.GetGeometryRef().Clone()) for f in L}
    def unpack(key):
        win = tuple(int(x) for x in store[key + "_win"])
        return np.unpackbits(store[key + "_mask"])[:np.prod(store[key + "_shape"])].reshape(store[key + "_shape"]).astype(bool), win
    # Kashmir and other India-related disputed polygons: share inside the India mask (fact only;
    # the human chose Natural Earth's default line)
    india_codes = [c for c, (nm, note, g) in disp.items() if note and "India" in note] + ["B45"]
    for code in ("B89", "C02", "C03", *sorted(set(india_codes))):
        um, uw = unpack("India" if code not in ("B89", "C02", "C03") else "Ukraine")
        nm, note, geom = disp[code]
        polys = polygons(geom)
        win = window_for(polys, gt, W, H)
        md = scanline_mask(polys, gt, win)
        # overlap in absolute coordinates
        rr0, cc0 = max(win[1], uw[1]), max(win[0], uw[0])
        rr1, cc1 = min(win[1] + win[3], uw[1] + uw[3]), min(win[0] + win[2], uw[0] + uw[2])
        sub_d = md[rr0 - win[1]:rr1 - win[1], cc0 - win[0]:cc1 - win[0]]
        sub_u = um[rr0 - uw[1]:rr1 - uw[1], cc0 - uw[0]:cc1 - uw[0]]
        ov = int((sub_d & sub_u).sum())
        tgt = "Ukraine" if code in ("B89", "C02", "C03") else "India"
        out["checks"][f"disputed_{code}"] = dict(name=nm, note=note, pixels=int(md.sum()), compared_with=tgt,
                                                 pixels_also_in_mask=ov,
                                                 share_in_mask_pct=100 * ov / max(int(md.sum()), 1),
                                                 area_polygon_km2=poly_area_km2(polys))
        store[f"disp_{code}_mask"] = np.packbits(md, axis=None); store[f"disp_{code}_shape"] = np.array(md.shape)
        store[f"disp_{code}_win"] = np.array(win)
    # Point checks (exact OGR Contains on the raw polygons)
    pts = {"Simferopol": (34.10, 44.95), "Sevastopol": (33.52, 44.60), "Kerch": (36.47, 45.36),
           "Donetsk": (37.80, 48.00), "Luhansk": (39.31, 48.57), "Kyiv": (30.52, 50.45),
           "Corte (Corsica)": (9.15, 42.31), "Bastia (Corsica)": (9.45, 42.70), "Paris": (2.35, 48.86),
           "Cayenne (Fr. Guiana)": (-52.33, 4.94), "Saint-Denis (Reunion)": (55.45, -20.88),
           "New Delhi": (77.21, 28.61), "Srinagar": (74.80, 34.08), "Leh": (77.58, 34.16), "Gilgit": (74.31, 35.92)}
    nocor = no_cor_geom()
    pc = {}
    for nm, (x, y) in pts.items():
        p = ogr.Geometry(ogr.wkbPoint); p.AddPoint_2D(x, y)
        pc[nm] = dict(lon=x, lat=y, in_India=ind[0][2].Contains(p), in_Ukraine=ukr[0][2].Contains(p),
                      in_France_FXX=fra[0][2].Contains(p), in_France_excl_Corsica=nocor.Contains(p))
    out["checks"]["point_checks_note"] = "approximate city coordinates typed by the agent from general knowledge; for orientation only"
    out["checks"]["point_checks"] = pc
    # countries-layer 'France' (incl. overseas) vs map_units FXX: overseas parts present there, not in FXX
    fr_c = features("ne_10m_admin_0_countries", "ADMIN", "France")
    out["checks"]["countries_layer_France_area_km2"] = poly_area_km2(polygons(fr_c[0][2]))
    out["checks"]["map_units_FXX_area_km2"] = poly_area_km2(fra_polys)
    np.savez_compressed(RESULTS / "s03_masks.npz", **store)
    out["runtime_s"] = time.time() - t0
    write_result("s03_masks.json", out)


if __name__ == "__main__":
    main()
