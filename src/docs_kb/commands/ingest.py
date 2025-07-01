import click
import pandas as pd
import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm
from typing_extensions import Annotated

from ..core.file_loader import FileLoader
from ..core.mindsdb_client import mindsdb_client
from ..utils import get_or_request_github_token

app = typer.Typer()
console = Console()


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
        # Display repository info
        display_ingestion_info(repo_name, branch)

        # Get GitHub token
        github_token = get_or_request_github_token()
        if not github_token:
            console.print("❌ GitHub token is required for ingestion", style="red")
            raise typer.Exit(code=1)

        console.print(
            f"🔍 Discovering files from repository: {repo_name} on branch: {branch}...",
            style="blue"
        )

        file_loader = FileLoader(
            repo_name=repo_name,
            branch=branch,
            github_token=github_token,
        )

        # Discover files with status indicator
        with console.status(
            "[bold blue]🔍 Discovering files...", spinner="dots"
        ):
            discovered_files = file_loader.discover_files()

        if not discovered_files:
            console.print(
                f"❌ No files found in repository {repo_name} on branch {branch}",
                style="red"
            )
            raise typer.Exit(code=1)

        console.print(
            f"📁 Discovered {len(discovered_files)} files in repository {repo_name} on branch {branch}.",
            style="green"
        )

        # Show file discovery summary
        display_discovery_summary(discovered_files)

        # Ask for confirmation
        if not Confirm.ask("Do you want to proceed with ingestion?", default=True):
            console.print("❌ Ingestion cancelled by user.", style="yellow")
            raise typer.Exit(code=0)

        # Start ingestion process
        console.print("\n📥 [bold blue]Starting Ingestion Process[/bold blue]")
        
        with console.status(
            f"[bold blue]📥 Loading {len(discovered_files)} files from repository...", 
            spinner="dots"
        ):
            files = file_loader.load_files()

        console.print(f"✅ Loaded {len(files)} files successfully", style="green")

        # Prepare data records
        console.print("🔄 Preparing data for ingestion...", style="blue")
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

        # Ingest into knowledge base
        with console.status(
            f"[bold blue]🚀 Ingesting {len(files)} files into knowledge base...", 
            spinner="dots"
        ):
            mindsdb_client.ingest(
                repo_name=repo_name, branch=branch, data=df, files=discovered_files
            )

        console.print(
            f"✅ Successfully ingested {len(files)} files from repository {repo_name} on branch {branch}.",
            style="green bold"
        )

        # Display success summary
        display_success_summary(repo_name, branch, len(files))

    except click.exceptions.Abort:
        console.print("\n👋 Goodbye!", style="yellow")
        raise typer.Exit(code=0)
    except KeyboardInterrupt:
        console.print("\n👋 Goodbye!", style="yellow")
        raise typer.Exit(code=0)
    except Exception as e:
        console.print(f"❌ Error during ingestion: {e}", style="red")
        raise typer.Exit(code=1)


def display_ingestion_info(repo_name: str, branch: str):
    """
    Display information about the ingestion process.
    """
    info_text = f"""[bold]Repository:[/bold] {repo_name}
[bold]Branch:[/bold] {branch}
[bold]Process:[/bold] Ingest documentation files into knowledge base
[bold]File Types:[/bold] .md, .mdx files"""

    panel = Panel(
        info_text,
        title="📥 Repository Ingestion",
        border_style="blue",
        padding=(1, 2),
    )
    console.print(panel)


def display_discovery_summary(discovered_files):
    """
    Display summary of discovered files.
    """
    if len(discovered_files) <= 5:
        console.print("\n📄 [bold blue]Discovered Files:[/bold blue]")
        for file in discovered_files:
            console.print(f"  • {file['path']}", style="cyan")
    else:
        console.print("\n📄 [bold blue]Sample Files:[/bold blue]")
        for file in discovered_files[:5]:
            console.print(f"  • {file['path']}", style="cyan")
        console.print(f"  ... and {len(discovered_files) - 5} more files", style="dim")


def display_success_summary(repo_name: str, branch: str, file_count: int):
    """
    Display success summary after ingestion.
    """
    success_text = f"""[bold green]✅ Ingestion Completed Successfully![/bold green]

[bold]Repository:[/bold] {repo_name}
[bold]Branch:[/bold] {branch}
[bold]Files Processed:[/bold] {file_count}
[bold]Status:[/bold] Ready for querying

💡 Use 'docs-kb query' to start asking questions about your documentation!"""

    panel = Panel(
        success_text,
        title="🎉 Ingestion Complete",
        border_style="green",
        padding=(1, 2),
    )
    console.print(panel)