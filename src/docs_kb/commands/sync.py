from typing import Dict, List, Optional

import click
import pandas as pd
import typer
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Confirm, Prompt
from rich.table import Table

from ..core.file_loader import FileLoader
from ..core.mindsdb_client import mindsdb_client
from ..core.models import Repository, list_repositories
from ..utils import get_or_request_github_token

app = typer.Typer()
console = Console()


@app.command(name="sync", help="Sync repository with latest changes from GitHub.")
def sync_command():
    """
    Sync a repository with the latest changes from GitHub.
    Compares file SHAs and updates only changed files.
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

        # Start sync process
        sync_repository(selected_repo)

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
                "\n[bold cyan]Select a repository to sync[/bold cyan]",
                choices=[str(i) for i in range(1, len(repositories) + 1)],
                show_choices=True,
            )

            repo_index = int(choice) - 1
            return repositories[repo_index]

        except (ValueError, IndexError):
            console.print("❌ Invalid selection. Please try again.", style="red")
        except click.exceptions.Abort:
            return None


def sync_repository(repository: Repository):
    """
    Sync repository with latest changes from GitHub.
    """
    console.print(
        f"\n🔄 Starting sync for repository: {repository.name}", style="blue bold"
    )

    try:
        github_token = get_or_request_github_token()
        # Initialize file loader
        file_loader = FileLoader(
            repo_name=repository.name,
            branch=repository.branch,
            github_token=github_token,
        )

        # Discover current files on GitHub
        with console.status(
            "[bold blue]🔍 Discovering files on GitHub...", spinner="dots"
        ):
            current_files = file_loader.discover_files()

        console.print(f"📁 Found {len(current_files)} files on GitHub", style="cyan")

        # Get stored files from database
        stored_files = repository.files or []
        console.print(f"💾 Found {len(stored_files)} files in database", style="cyan")

        # Compare files and find changes
        changes = compare_files(stored_files, current_files)

        # Display changes summary
        display_changes_summary(changes)

        if not has_changes(changes):
            console.print("✅ Repository is already up to date!", style="green")
            return

        # Ask for confirmation
        if not Confirm.ask(
            f"\nProceed with syncing {count_total_changes(changes)} changes?",
            default=True,
        ):
            console.print("❌ Sync cancelled by user.", style="yellow")
            return

        # Process changes
        process_changes(repository, file_loader, changes)

        console.print("✅ Sync completed successfully!", style="green bold")

    except Exception as e:
        console.print(f"❌ Error during sync: {e}", style="red")
        raise


def compare_files(
    stored_files: List[Dict], current_files: List[Dict]
) -> Dict[str, List[Dict]]:
    """
    Compare stored files with current files and categorize changes.
    """
    # Create lookup dictionaries
    stored_lookup = {file["path"]: file for file in stored_files}
    current_lookup = {file["path"]: file for file in current_files}

    # Find different types of changes
    changes = {
        "new": [],  # Files that exist on GitHub but not in database
        "modified": [],  # Files that exist in both but have different SHAs
        "deleted": [],  # Files that exist in database but not on GitHub
        "unchanged": [],  # Files that exist in both with same SHA
    }

    # Check for new and modified files
    for path, current_file in current_lookup.items():
        if path not in stored_lookup:
            changes["new"].append(current_file)
        elif stored_lookup[path]["sha"] != current_file["sha"]:
            changes["modified"].append(current_file)
        else:
            changes["unchanged"].append(current_file)

    # Check for deleted files
    for path, stored_file in stored_lookup.items():
        if path not in current_lookup:
            changes["deleted"].append(stored_file)

    return changes


def display_changes_summary(changes: Dict[str, List[Dict]]):
    """
    Display a summary of changes found.
    """
    console.print("\n📊 [bold blue]Sync Analysis[/bold blue]:")

    # Create summary table
    table = Table(show_header=True, header_style="bold blue")
    table.add_column("Change Type", style="cyan")
    table.add_column("Count", style="yellow")
    table.add_column("Action", style="green")

    table.add_row("🆕 New Files", str(len(changes["new"])), "Will be added")
    table.add_row("📝 Modified Files", str(len(changes["modified"])), "Will be updated")
    table.add_row("🗑️ Deleted Files", str(len(changes["deleted"])), "Will be removed")
    table.add_row(
        "✅ Unchanged Files", str(len(changes["unchanged"])), "No action needed"
    )

    console.print(table)

    # Show detailed changes if any
    if changes["new"]:
        console.print(
            f"\n🆕 [bold green]New Files ({len(changes['new'])}):[/bold green]"
        )
        for file in changes["new"][:5]:  # Show first 5
            console.print(f"  • {file['path']}", style="green")
        if len(changes["new"]) > 5:
            console.print(f"  ... and {len(changes['new']) - 5} more", style="dim")

    if changes["modified"]:
        console.print(
            f"\n📝 [bold yellow]Modified Files ({len(changes['modified'])}):[/bold yellow]"
        )
        for file in changes["modified"][:5]:  # Show first 5
            console.print(f"  • {file['path']}", style="yellow")
        if len(changes["modified"]) > 5:
            console.print(f"  ... and {len(changes['modified']) - 5} more", style="dim")

    if changes["deleted"]:
        console.print(
            f"\n🗑️ [bold red]Deleted Files ({len(changes['deleted'])}):[/bold red]"
        )
        for file in changes["deleted"][:5]:  # Show first 5
            console.print(f"  • {file['path']}", style="red")
        if len(changes["deleted"]) > 5:
            console.print(f"  ... and {len(changes['deleted']) - 5} more", style="dim")


def has_changes(changes: Dict[str, List[Dict]]) -> bool:
    """
    Check if there are any changes to process.
    """
    return (
        len(changes["new"]) > 0
        or len(changes["modified"]) > 0
        or len(changes["deleted"]) > 0
    )


def count_total_changes(changes: Dict[str, List[Dict]]) -> int:
    """
    Count total number of changes.
    """
    return len(changes["new"]) + len(changes["modified"]) + len(changes["deleted"])


def delete_files_from_knowledge_base(kb_name: str, file_paths: List[str]):
    """
    Delete specific files from the knowledge base by their file paths.

    Args:
        kb_name: Name of the knowledge base
        file_paths: List of file paths to delete
    """
    if not file_paths:
        return

    try:
        kb = mindsdb_client.client.knowledge_bases.get(kb_name)

        # Delete files one by one using their path as ID
        for file_path in file_paths:
            try:
                # Use SQL to delete specific records
                delete_sql = f"DELETE FROM {kb.name} WHERE id = '{file_path}'"
                mindsdb_client.client.query(delete_sql).fetch()
            except Exception as e:
                console.print(
                    f"  ⚠️ Warning: Could not delete {file_path}: {e}", style="yellow"
                )

        console.print(
            f"🗑️ Deleted {len(file_paths)} files from knowledge base", style="red"
        )

    except Exception as e:
        console.print(f"❌ Error deleting files from knowledge base: {e}", style="red")
        raise


def process_changes(
    repository: Repository, file_loader: FileLoader, changes: Dict[str, List[Dict]]
):
    """
    Process the changes by updating the knowledge base.
    """
    # Step 1: Delete modified and deleted files from knowledge base
    files_to_delete = []

    # Add modified files to deletion list (we'll re-add them with new content)
    if changes["modified"]:
        modified_paths = [file["path"] for file in changes["modified"]]
        files_to_delete.extend(modified_paths)
        console.print(
            f"🔄 Will delete {len(modified_paths)} modified files and re-add them",
            style="blue",
        )

    # Add deleted files to deletion list
    if changes["deleted"]:
        deleted_paths = [file["path"] for file in changes["deleted"]]
        files_to_delete.extend(deleted_paths)
        console.print(f"🗑️ Will delete {len(deleted_paths)} removed files", style="red")

    # Delete files from knowledge base
    if files_to_delete:
        with console.status(
            f"[bold red]🗑️ Deleting {len(files_to_delete)} files from knowledge base...",
            spinner="dots",
        ):
            delete_files_from_knowledge_base(
                repository.knowledge_base_name, files_to_delete
            )

    # Step 2: Add new and modified files using the ingest function
    files_to_ingest = changes["new"] + changes["modified"]

    if files_to_ingest:
        console.print(
            f"\n📥 Ingesting {len(files_to_ingest)} files (new + modified)...",
            style="blue",
        )

        # Load file contents for files to ingest
        file_paths = [file["path"] for file in files_to_ingest]

        with console.status(
            f"[bold blue]📥 Loading {len(files_to_ingest)} files...", spinner="dots"
        ):
            loaded_files, _ = file_loader.github_file_loader.load_files_sync(
                repository.name,
                branch=repository.branch,
                file_paths=file_paths,
                max_concurrent=20,
            )

        # Prepare data for ingestion using the same format as the ingest command
        data_records = []
        for file_obj in loaded_files:
            record = {
                "id": file_obj.path,
                "content": file_obj.content,
                "repository": repository.name,
                "branch": repository.branch,
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

        # Use the MindsDB client's ingest method to add the files
        with console.status(
            f"[bold blue]🔄 Ingesting {len(loaded_files)} files into knowledge base...",
            spinner="dots",
        ):
            kb = mindsdb_client.client.knowledge_bases.get(
                repository.knowledge_base_name
            )
            kb.insert(df)

        console.print(
            f"✅ Successfully ingested {len(loaded_files)} files", style="green"
        )

        # Display breakdown
        if changes["new"]:
            console.print(f"  📁 Added {len(changes['new'])} new files", style="green")
        if changes["modified"]:
            console.print(
                f"  🔄 Updated {len(changes['modified'])} modified files", style="blue"
            )

    # Step 3: Update repository record with latest file information
    update_repository_files(repository, file_loader.discover_files())


def update_repository_files(repository: Repository, current_files: List[Dict]):
    """
    Update repository record with current file information.
    """
    from datetime import datetime

    from ..core.models import get_session

    with get_session() as session:
        # Get fresh repository instance
        repo = session.get(Repository, repository.id)
        if repo:
            repo.files = current_files
            repo.last_ingested = datetime.now()
            session.add(repo)
            session.commit()
            console.print(
                f"📝 Updated repository record with {len(current_files)} files",
                style="cyan",
            )


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
