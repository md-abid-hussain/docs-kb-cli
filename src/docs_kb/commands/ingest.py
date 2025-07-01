import os

import pandas as pd
import typer
from typing_extensions import Annotated

from ..core.file_loader import FileLoader
from ..core.mindsdb_client import mindsdb_client

app = typer.Typer()


@app.command(name="ingest", help="Ingest files from a GitHub repository.")
def ingest(
    repo_name: Annotated[
        str, typer.Argument(help="GitHub repository name (e.g., 'owner/repo')")
    ],
    branch: Annotated[
        str, typer.Option("--branch", "-b", help="Branch to ingest from")
    ] = "main",
):
    """
    Ingest files from a GitHub repository.
    """
    try:
        typer.echo(
            f"🔍 Discovering files from repository: {repo_name} on branch: {branch}..."
        )

        file_loader = FileLoader(
            repo_name=repo_name,
            branch=branch,
            github_token=os.getenv("GITHUB_TOKEN"),
        )

        discovered_files = file_loader.discover_files()
        if not discovered_files:
            typer.echo(f"No files found in repository {repo_name} on branch {branch}")
            raise typer.Exit(code=1)

        typer.echo(
            f"ℹ️  Discovered {len(discovered_files)} files in repository {repo_name} on branch {branch}."
        )

        proceed = typer.confirm("Do you want to proceed with ingestion?", default=True)
        if not proceed:
            typer.echo("❌ Ingestion cancelled by user.")
            raise typer.Exit(code=0)

        typer.echo("📥 Starting Ingestion")
        typer.echo(f"Loading files from repository {repo_name} on branch {branch}...")

        files = file_loader.load_files()

        data_records = []
        for file_obj in files:
            record = {
                "id": file_obj.path,
                "content": file_obj.content,
                "repository": repo_name,
                "branch": branch,
                "path": file_obj.path,
                "name": file_obj.name,
                "size": file_obj.size,
                "sha": file_obj.sha,
            }
            data_records.append(record)

        df = pd.DataFrame(
            data_records,
            columns=[
                "id",
                "content",
                "repository",
                "branch",
                "path",
                "name",
                "size",
                "sha",
            ],
        )

        mindsdb_client.ingest(
            repo_name=repo_name, branch=branch, data=df, files=discovered_files
        )

        typer.echo(
            f"✅ Successfully ingested {len(files)} files from repository {repo_name} on branch {branch}."
        )

    except Exception as e:
        typer.echo(f"❌ Error during ingestion: {e}")
        raise typer.Exit(code=1)
