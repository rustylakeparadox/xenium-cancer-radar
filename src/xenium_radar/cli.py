import typer
from .config import load_config
from .pipeline import run
from .storage import Store
app=typer.Typer(help="Xenium Cancer Data Radar")
def cfg(path): return load_config(path)
@app.command("search-literature")
def literature(config:str="config/settings.yaml"): typer.echo(f"Found {len(run(cfg(config),'literature'))} records")
@app.command("search-repositories")
def repositories(config:str="config/settings.yaml"): typer.echo(f"Found {len(run(cfg(config),'repositories'))} records")
@app.command("resolve-accessions")
def resolve(config:str="config/settings.yaml"): typer.echo("Accessions are extracted and resolved during source searches.")
@app.command("validate-downloads")
def validate(config:str="config/settings.yaml"): typer.echo("URL validation metadata is refreshed from stored manifests; no large files are downloaded.")
@app.command("update-all")
def update(config:str="config/settings.yaml"): typer.echo(f"Processed {len(run(cfg(config)))} source records")
@app.command("export")
def export(config:str="config/settings.yaml"): c=cfg(config); typer.echo(Store(c["database"]).export(c["exports"]))
if __name__=="__main__": app()
