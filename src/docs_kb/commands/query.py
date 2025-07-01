from typing import List, Optional

import click
import pandas as pd
import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from ..core.mindsdb_client import mindsdb_client
from ..core.models import Repository, list_repositories

app = typer.Typer()
console = Console()


@app.command(name="query", help="Interactive chat with repository knowledge base.")
def query_command():
    """
    Start an interactive chat session with a repository knowledge base.
    """
    try:
        # List available repositories
        repositories = list_repositories()

        if not repositories:
            console.print(
                "❌ No repositories found. Please ingest a repository first.",
                style="red",
            )
            raise typer.Exit(code=1)

        # Display repository selection
        selected_repo = select_repository(repositories)
        if not selected_repo:
            console.print("👋 Goodbye!", style="yellow")
            raise typer.Exit(code=0)

        # Display repository info
        display_repository_info(selected_repo)

        console.print(
            f"\n🤖 Starting chat with repository: {selected_repo.name}",
            style="green bold",
        )
        console.print(
            "💡 Type 'exit' or 'quit' to end the session, or press Ctrl+C", style="dim"
        )
        console.print("-" * 60)

        # Start interactive chat loop
        start_chat_session(selected_repo)

    except click.exceptions.Abort:
        console.print("\n👋 Goodbye!", style="yellow")
        raise typer.Exit(code=0)
    except KeyboardInterrupt:
        console.print("\n👋 Goodbye!", style="yellow")
        raise typer.Exit(code=0)
    except Exception as e:
        console.print(f"❌ Error: {e}", style="red")
        raise typer.Exit(code=1)


def select_repository(repositories: List[Repository]) -> Optional[Repository]:
    """
    Display repository selection menu and return selected repository.
    """
    # Create selection table
    table = Table(
        title="📚 Available Repositories", show_header=True, header_style="bold blue"
    )
    table.add_column("No.", style="cyan", width=6)
    table.add_column("Repository", style="green")
    table.add_column("Branch", style="yellow")
    table.add_column("Last Ingested", style="magenta")
    table.add_column("Files", style="blue")

    for i, repo in enumerate(repositories, 1):
        last_ingested = (
            repo.last_ingested.strftime("%Y-%m-%d %H:%M")
            if repo.last_ingested
            else "Never"
        )
        file_count = str(len(repo.files)) if repo.files else "0"
        table.add_row(str(i), repo.name, repo.branch, last_ingested, file_count)

    console.print(table)

    while True:
        try:
            choice = Prompt.ask(
                "\n[bold cyan]Select a repository[/bold cyan]",
                choices=[str(i) for i in range(1, len(repositories) + 1)],
                show_choices=True,
            )

            repo_index = int(choice) - 1
            return repositories[repo_index]

        except (ValueError, IndexError):
            console.print("❌ Invalid selection. Please try again.", style="red")
        except click.exceptions.Abort:
            return None


def start_chat_session(repository: Repository):
    """
    Start an interactive chat session with the selected repository.
    """
    while True:
        try:
            # Get user input
            user_question = Prompt.ask(
                "\n[bold green]🗣️  You[/bold green]", default=""
            ).strip()

            # Check for exit commands
            if user_question.lower() in ["exit", "quit", "bye", ""]:
                if user_question.lower() in ["exit", "quit", "bye"]:
                    console.print("👋 Goodbye!", style="yellow")
                break

            if not user_question:
                continue

            # Show searching indicator and query inside the status context
            try:
                with console.status(
                    "[bold blue]🔍 Searching knowledge base...", spinner="dots"
                ):
                    # Query the knowledge base
                    results_df = mindsdb_client.query(
                        repository.knowledge_base_name, user_question
                    )

                # Process and display results (outside the status context)
                display_query_results(user_question, results_df)

            except Exception as e:
                console.print(f"\n❌ Error querying knowledge base: {e}", style="red")

        except click.exceptions.Abort:
            console.print("\n👋 Goodbye!", style="yellow")
            break
        except KeyboardInterrupt:
            console.print("\n👋 Goodbye!", style="yellow")
            break


def display_query_results(question: str, results_df: pd.DataFrame):
    """
    Display query results in a formatted way.
    """
    if results_df.empty:
        console.print("\n🤖 No results found for your question.", style="yellow")
        return

    if len(results_df) > 0:
        top_result = results_df.iloc[0]
        content = top_result.get("chunk_content", "No content available")
        source = top_result.get("id", "Unknown Source")
        relevance = (
            f"{1 - top_result.get('distance', 1):.2f}"
            if "distance" in top_result
            else "N/A"
        )

        # Create response panel with most relevant content
        panel_content = content
        if len(content) > 800:
            panel_content = (
                content[:800]
                + "\n\n[dim]...(content truncated - see full results below)[/dim]"
            )

        panel = Panel(
            panel_content,
            title=f"🎯 Most Relevant Result (Score: {relevance})",
            subtitle=f"Source: {source}",
            border_style="blue",
            padding=(1, 2),
        )
        console.print(panel)

    # Display summary
    console.print(
        f"\n📊 [bold blue]Search Results[/bold blue] (Found {len(results_df)} results):"
    )

    # Always show the detailed results table
    display_detailed_results(results_df)


def display_detailed_results(results_df: pd.DataFrame):
    """
    Display detailed results table.
    """
    table = Table(title="🔍 Search Results", show_header=True, header_style="bold blue")
    table.add_column("No.", style="cyan", width=4)
    table.add_column("Content Preview", style="white", width=70)
    table.add_column("Source", style="green", width=30)
    table.add_column("Relevance", style="yellow", width=10)

    for i, row in results_df.iterrows():
        # Use chunk_content instead of content
        content = row.get("chunk_content", "")
        content_preview = content[:120] + "..." if len(content) > 120 else content

        source = row.get("id", "Unknown Source")

        # Truncate long source paths
        if len(source) > 28:
            source = "..." + source[-25:]

        relevance = f"{row.get('relevance', 1):.2f}" if "relevance" in row else "N/A"

        table.add_row(str(i + 1), content_preview, source, relevance)

        if i < len(results_df) - 1:  # Don't add space after last row
            table.add_row("", "", "", "")

    console.print(table)


def display_repository_info(repository: Repository):
    """
    Display detailed information about the selected repository.
    """
    info_text = f"""[bold]Repository:[/bold] {repository.name}
[bold]Branch:[/bold] {repository.branch}
[bold]Knowledge Base:[/bold] {repository.knowledge_base_name}
[bold]Files Count:[/bold] {len(repository.files)}
[bold]Created:[/bold] {repository.created_at.strftime('%Y-%m-%d %H:%M')}
[bold]Last Ingested:[/bold] {repository.last_ingested.strftime('%Y-%m-%d %H:%M') if repository.last_ingested else 'Never'}"""

    panel = Panel(
        info_text,
        title="📋 Repository Information",
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(panel)
