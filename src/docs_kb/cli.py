import typer
from dotenv import load_dotenv
from rich.console import Console

from .commands import ingest, list, manage, query, start_mcp

load_dotenv()
console = Console()

app = typer.Typer(
    name="docs-kb",
    help="""[bold blue]🤖 AI-powered documentation knowledge base for GitHub repositories.

    Use commands to ingest, query, sync, and manage repository documentation.""",
    rich_markup_mode="rich",
    no_args_is_help=True,
    invoke_without_command=True,
    add_completion=False,
)

app.add_typer(ingest.app)
app.add_typer(query.app)
app.add_typer(manage.app)
app.add_typer(list.app)
app.add_typer(start_mcp.app)


@app.callback()
def main():
    """
    🤖 AI-powered documentation knowledge base for GitHub repositories.

    Use commands to ingest, query, sync, and manage repository documentation.
    """
    pass


@app.command(name="version", help="Show version information")
def version():
    """Show version information."""
    console.print("📚 docs-kb version 0.1.0", style="blue bold")
    console.print("🤖 AI-powered documentation knowledge base", style="dim")


if __name__ == "__main__":
    app()
