import typer
from rich.console import Console
from rich.table import Table

from ..core.models import list_repositories

app = typer.Typer()
console = Console()


@app.command(name="list", help="List all ingested repositories.")
def list_command():
    """
    List all repositories in the database.
    """
    try:
        repositories = list_repositories()

        if not repositories:
            console.print("📝 No repositories found.", style="yellow")
            console.print(
                "💡 Use 'docs-kb ingest <repo>' to add a repository.", style="dim"
            )
            return

        # Create table
        table = Table(
            title="📚 Ingested Repositories", show_header=True, header_style="bold blue"
        )
        table.add_column("Repository", style="green", width=30)
        table.add_column("Branch", style="yellow", width=10)
        table.add_column("Knowledge Base", style="cyan", width=35)
        table.add_column("Files", style="blue", width=8)
        table.add_column("Created", style="magenta", width=16)
        table.add_column("Last Sync", style="red", width=16)

        for repo in repositories:
            last_ingested = (
                repo.last_ingested.strftime("%Y-%m-%d %H:%M")
                if repo.last_ingested
                else "Never"
            )
            file_count = str(len(repo.files)) if repo.files else "0"

            table.add_row(
                repo.name,
                repo.branch,
                repo.knowledge_base_name,
                file_count,
                repo.created_at.strftime("%Y-%m-%d %H:%M"),
                last_ingested,
            )

        console.print(table)
        console.print(f"\n📊 Total: {len(repositories)} repositories", style="dim")

    except Exception as e:
        console.print(f"❌ Error listing repositories: {e}", style="red")
        raise typer.Exit(code=1)
