import asyncio

import typer
from rich.console import Console

from ..mcp_server.server import mcp

app = typer.Typer()
console = Console()


@app.command(name="start-mcp-server", help="Start the MindsDB MCP server.")
def start(
    host: str = typer.Option("localhost", "--host", "-h", help="Host to bind to"),
    port: int = typer.Option(8000, "--port", "-p", help="Port to bind to"),
):
    """Start the MindsDB MCP server with proper async handling."""
    try:
        # Enable tracemalloc if requested (helps with debugging memory allocations)
        console.print(f"🚀 Starting MCP server on {host}:{port}...", style="blue bold")
        console.print("📚 MindsDB Knowledge Base Server", style="cyan")
        console.print("🔧 Available tools:", style="yellow")
        console.print("  • list_available_repositories", style="dim")
        console.print("  • query_repository", style="dim")
        console.print("  • get_repository_tree", style="dim")
        console.print("  • get_single_file", style="dim")
        console.print("  • load_multiple_files", style="dim")
        console.print("  • how_to_use_docs_kb_mcp", style="dim")
        console.print("\n💡 Press Ctrl+C to stop the server", style="dim")

        # Run the server with proper async handling
        asyncio.run(run_server_async(host, port))

    except KeyboardInterrupt:
        console.print("\n👋 Server stopped", style="yellow")
    except Exception as e:
        console.print(f"❌ Server error: {e}", style="red")
        raise typer.Exit(code=1)


async def run_server_async(host: str, port: int):
    """Run the MCP server asynchronously."""
    try:
        # Use the FastMCP server's async run method with proper configuration
        await mcp.run_sse_async(host=host, port=port)
    except Exception as e:
        console.print(f"❌ Failed to start server: {e}", style="red")
        raise
