import os, sys, zipfile, rasterio
sys.path.insert(0,'/private/tmp/claude-501/-Users-alexander/ee65fd05-1210-4209-bd1e-915d9081a843/scratchpad')
import httpzip
os.environ.update(GDAL_DISABLE_READDIR_ON_OPEN='EMPTY_DIR', CPL_VSIL_CURL_USE_HEAD='NO', GDAL_HTTP_MAX_RETRY='3')
LON, LAT = -3.70, 40.42
for z in sys.argv[1:]:
    url=f'https://zenodo.org/records/6638505/files/{z}?download=1'
    names=[n.filename for n in zipfile.ZipFile(httpzip.HTTPFile(url)).infolist() if n.filename.endswith('G2F.cal2N.Ao2_rect.tiff')]
    print(z, len(names), 'frames', flush=True)
    for n in names:
        try:
            with rasterio.open(f'/vsizip/{{/vsicurl/{url}}}/{n}') as s:
                b=s.bounds
                if b.left<=LON<=b.right and b.bottom<=LAT<=b.top:
                    print('HIT', z, n, s.width, s.height, s.crs, [round(v,3) for v in b], s.res, s.dtypes[0], flush=True)
        except Exception as e:
            print('ERR', n, str(e)[:80], flush=True)
    print('done', z, flush=True)
