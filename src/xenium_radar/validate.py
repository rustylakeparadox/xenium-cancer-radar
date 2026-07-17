from .models import FileEntry
XENIUM_FILES=("cell_feature_matrix.h5","cell_feature_matrix.tar.gz","cells.csv.gz","cells.parquet","transcripts.csv.gz","transcripts.parquet","cell_boundaries.csv.gz","cell_boundaries.parquet","nucleus_boundaries.csv.gz","nucleus_boundaries.parquet","morphology.ome.tif","morphology_focus","experiment.xenium","panel.tsv","gene_panel.json",".zarr",".h5ad")
def is_xenium_file(name): return any(name.lower().endswith(x) or x in name.lower() for x in XENIUM_FILES)
def validate_url(client,url,name=""):
 try:
  r=client.head(url); headers=r.headers
  if r.status_code in (405,501): r=client.get(url,headers={"Range":"bytes=0-0"},stream=True)
  return FileEntry(name=name or url.rsplit("/",1)[-1],url=url,http_status=r.status_code,size_bytes=int(headers["Content-Length"]) if headers.get("Content-Length","").isdigit() else None,content_type=headers.get("Content-Type"),supports_range="bytes" in headers.get("Accept-Ranges","").lower() or r.status_code==206,last_modified=headers.get("Last-Modified"),login_required=r.status_code in (401,403),publicly_downloadable=r.status_code in (200,206))
 except Exception:
  return FileEntry(name=name or url,url=url,publicly_downloadable=False)
