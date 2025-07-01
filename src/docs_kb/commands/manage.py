from typing import List, Optional

import click
import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from ..core.mindsdb_client import mindsdb_client
from ..core.models import Repository, delete_repository, list_repositories

app = typer.Typer()
console = Console()


@app.command(name="manage", help="Manage repositories (sync, delete, etc.).")
def manage_command():
    """
    Manage repositories with options to sync or delete.
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

        # Show management options
        action = select_management_action()
        if not action:
            console.print("👋 Goodbye!", style="yellow")
            raise typer.Exit(code=0)

        # Execute the selected action
        if action == "sync":
            from .sync import sync_repository

            sync_repository(selected_repo)
        elif action == "delete":
            delete_repository_action(selected_repo)

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
    table.add_column("Last Sync", style="magenta")
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
                "\n[bold cyan]Select a repository to manage[/bold cyan]",
                choices=[str(i) for i in range(1, len(repositories) + 1)],
                show_choices=True,
            )

            repo_index = int(choice) - 1
            return repositories[repo_index]

        except (ValueError, IndexError):
            console.print("❌ Invalid selection. Please try again.", style="red")
        except click.exceptions.Abort:
            return None


def select_management_action() -> Optional[str]:
    """
    Display management action menu and return selected action.
    """
    console.print("\n🛠️  [bold blue]Management Options[/bold blue]:")

    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Option", style="cyan", width=8)
    table.add_column("Action", style="green", width=20)
    table.add_column("Description", style="white")

    table.add_row("1", "🔄 Sync", "Sync repository with latest GitHub changes")
    table.add_row("2", "🗑️  Delete", "Delete repository and its knowledge base")

    console.print(table)

    while True:
        try:
            choice = Prompt.ask(
                "\n[bold cyan]Select an action[/bold cyan]",
                choices=["1", "2"],
                show_choices=True,
            )

            if choice == "1":
                return "sync"
            elif choice == "2":
                return "delete"

        except (ValueError, IndexError):
            console.print("❌ Invalid selection. Please try again.", style="red")
        except click.exceptions.Abort:
            return None


def delete_repository_action(repository: Repository):
    """
    Delete a repository and its knowledge base.
    """
    console.print(f"\n⚠️  [bold red]Delete Repository: {repository.name}[/bold red]")
    console.print("This will permanently delete:")
    console.print(f"  • Repository record from database")
    console.print(f"  • Knowledge base: {repository.knowledge_base_name}")
    console.print(f"  • All {len(repository.files)} ingested files")

    # First confirmation
    if not Confirm.ask(
        f"\n[bold red]Are you sure you want to delete '{repository.name}'?[/bold red]",
        default=False,
    ):
        console.print("❌ Deletion cancelled.", style="yellow")
        return

    # Second confirmation for safety
    console.print(f"\n⚠️  [bold red]FINAL WARNING[/bold red]")
    console.print("This action cannot be undone!")

    if not Confirm.ask(f"Type the repository name to confirm deletion", default=False):
        console.print("❌ Deletion cancelled.", style="yellow")
        return

    confirmation_name = Prompt.ask("Repository name")
    if confirmation_name != repository.name:
        console.print(
            "❌ Repository name doesn't match. Deletion cancelled.", style="red"
        )
        return

    try:
        # Delete knowledge base
        console.print(
            f"🗑️  Deleting knowledge base '{repository.knowledge_base_name}'..."
        )
        with console.status("[bold red]🗑️  Deleting knowledge base...", spinner="dots"):
            mindsdb_client._delete_knowledge_base(repository.knowledge_base_name)

        # Delete repository record
        console.print(f"🗑️  Deleting repository record...")
        success = delete_repository(repository.name)

        if success:
            console.print(
                f"✅ Successfully deleted repository '{repository.name}' and its knowledge base.",
                style="green bold",
            )
        else:
            console.print(
                f"❌ Failed to delete repository record from database.", style="red"
            )

    except Exception as e:
        console.print(f"❌ Error during deletion: {e}", style="red")
        raise


def display_repository_info(repository: Repository):
    """
    Display detailed information about the selected repository.
    """
    info_text = f"""[bold]Repository:[/bold] {repository.name}
[bold]Branch:[/bold] {repository.branch}
[bold]Knowledge Base:[/bold] {repository.knowledge_base_name}
[bold]Files Count:[/bold] {len(repository.files)}
[bold]Created:[/bold] {repository.created_at.strftime('%Y-%m-%d %H:%M')}
[bold]Last Sync:[/bold] {repository.last_ingested.strftime('%Y-%m-%d %H:%M') if repository.last_ingested else 'Never'}"""

    panel = Panel(
        info_text,
        title="📋 Repository Information",
        border_style="cyan",
        padding=(1, 2),
    )
    console.print(panel)
