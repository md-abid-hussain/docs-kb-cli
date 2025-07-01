import os
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from ..core.file_loader import FileLoader
from ..core.mindsdb_client import mindsdb_client
from ..core.models import list_repositories

mcp = FastMCP(name="MindsDB Knowledge Base Server")


@mcp.tool()
def how_to_use_docs_kb_mcp() -> str:
    """
    Documentation Knowledge Base MCP Server Usage Guide

    ## 🚀 What it does:
    - Query ingested documentation repositories using natural language
    - Access GitHub repository files and structure without ingestion
    - Browse repository trees with filtering options

    ## 📚 Knowledge Base Tools:
    1. **list_available_repositories()** - See all ingested repositories
    2. **query_repository(repo_name, branch, query)** - Search ingested docs with natural language

    ## 🔧 GitHub Tools (work with any repo):
    3. **get_repository_tree(repo_name, branch)** - Browse repo file structure
    4. **get_single_file(repo_name, file_path, branch)** - Get specific file content
    5. **load_multiple_files(repo_name, file_paths, branch)** - Load multiple files at once

    The function name will be concatenated with mcp-server prefix

    ## 📝 Examples:
    - Query: `query_repository("facebook/react", "main", "How to use hooks?")`
    - Browse: `get_repository_tree("microsoft/vscode", "main", [".md"], "docs/")`
    - File: `get_single_file("nodejs/node", "README.md", "main")`

    ## ⚙️ Setup:
    Requires GITHUB_TOKEN environment variable for GitHub API access.
    """
    return (
        "Documentation Knowledge Base MCP Server - Query docs and access GitHub repos"
    )


@mcp.tool()
def list_available_repositories() -> List[Dict[str, str]]:
    """
    List all available repositories in the knowledge base.

    Returns:
        List of dictionaries containing repository information with keys:
        - id: Repository ID
        - name: Repository name (e.g., 'owner/repo')
        - branch: Repository branch
        - knowledge_base_name: Associated knowledge base name
        - created_at: Creation timestamp
        - last_ingested: Last ingestion timestamp
        - file_count: Number of files in repository
    """
    try:
        repositories = list_repositories()

        result = []
        for repo in repositories:
            repo_info = {
                "id": str(repo.id),
                "name": repo.name,
                "branch": repo.branch,
            }
            result.append(repo_info)

        return result
    except Exception as e:
        raise Exception(f"Failed to list repositories: {str(e)}")


@mcp.tool()
def query_repository_docs(
    repo_name: str, branch: str, query: str, limit: Optional[int] = 10
) -> Dict[str, any]:
    """
    Query a repository's knowledge base with natural language.

    Args:
        repo_name: Repository name in format 'owner/repo'
        branch: Repository branch name
        query: Natural language query to search the repository
        limit: Maximum number of results to return (default: 10)

    Returns:
        Dictionary containing:
        - success: Boolean indicating if query was successful
        - results: List of matching documents with content and metadata
        - total_results: Number of results found
        - kb_name: Knowledge base name used for the query
    """
    try:
        # Generate knowledge base name using same pattern as MindsDBClient
        kb_name = f"kb_{repo_name.replace('/', '_').replace('-', '_')}_{branch}"

        # Query the knowledge base
        results_df = mindsdb_client.query(kb_name, query, limit)

        if results_df is None or results_df.empty:
            return {
                "success": True,
                "results": [],
                "total_results": 0,
                "kb_name": kb_name,
                "message": "No results found for the query",
            }

        # Convert DataFrame to list of dictionaries
        results = []
        for _, row in results_df.iterrows():
            result_item = {
                "content": row.get("chunk_content", ""),
                "source": row.get("id", "Unknown Source"),
                "repository": row.get("repository", repo_name),
                "branch": row.get("branch", branch),
                "path": row.get("path", ""),
                "name": row.get("name", ""),
                "size": row.get("size", ""),
                "sha": row.get("sha", ""),
                "relevance": (
                    float(row.get("relevance", 0.0)) if "relevance" in row else None
                ),
                "distance": (
                    float(row.get("distance", 1.0)) if "distance" in row else None
                ),
            }
            results.append(result_item)

        return {
            "success": True,
            "results": results,
            "total_results": len(results),
            "kb_name": kb_name,
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "results": [],
            "total_results": 0,
            "kb_name": f"kb_{repo_name.replace('/', '_').replace('-', '_')}_{branch}",
        }


@mcp.tool()
def get_repository_tree(
    repo_name: str,
    branch: str = "main",
    file_extensions: Optional[List[str]] = None,
    path_filter: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Get the file tree of a GitHub repository with optional filtering.

    Args:
        repo_name: Repository name in format 'owner/repo'
        branch: Repository branch name (default: 'main')
        file_extensions: List of file extensions to filter (e.g., ['.md', '.py'])
        path_filter: Optional path prefix to filter files (e.g., 'docs/')
    Returns:
        Dictionary containing:
        - success: Boolean indicating if operation was successful
        - files: List of file information dictionaries, each with a 'path' key
        - total_files: Number of files found
        - filters_applied: Summary of filters used
    """
    try:
        github_token = os.getenv("GITHUB_TOKEN")
        if not github_token:
            return {
                "success": False,
                "error": "GITHUB_TOKEN environment variable is required",
                "files": [],
                "total_files": 0,
                "filters_applied": {},
            }

        file_loader = FileLoader(
            repo_name=repo_name, branch=branch, github_token=github_token
        )

        # Default extensions if none provided
        if file_extensions is None:
            file_extensions = [".md", ".mdx"]

        # Fetch raw list of file paths (strings)
        try:
            discovered_files, _ = (
                file_loader.github_file_loader.client.get_repository_tree(
                    repo_name, branch
                )
            )
            if not isinstance(discovered_files, list):
                raise ValueError(
                    f"Expected list of paths, got {type(discovered_files)}"
                )
        except Exception as api_error:
            return {
                "success": False,
                "error": f"Failed to fetch repository tree: {str(api_error)}",
                "files": [],
                "total_files": 0,
                "filters_applied": {},
            }

        # Normalize extensions to lowercase
        exts = {ext.lower() for ext in file_extensions}

        # Apply extension filter
        filtered = []
        for path in discovered_files:
            _, ext = os.path.splitext(path)
            if ext.lower() in exts:
                filtered.append(path)

        # Apply path-prefix filter
        if path_filter:
            filtered = [p for p in filtered if p.startswith(path_filter)]

        # Build result list of dicts
        files_info = filtered

        return {
            "success": True,
            "files": files_info,
            "total_files": len(files_info),
            "filters_applied": {
                "file_extensions": file_extensions,
                "path_filter": path_filter,
            },
        }

    except Exception as e:
        return {
            "success": False,
            "error": f"Unexpected error: {str(e)}",
            "files": [],
            "total_files": 0,
            "filters_applied": {},
        }


@mcp.tool()
def get_single_file(
    repo_name: str, file_path: str, branch: str = "main"
) -> Dict[str, any]:
    """
    Get the content of a single file from a GitHub repository.

    Args:
        repo_name: Repository name in format 'owner/repo'
        file_path: Path to the file within the repository
        branch: Repository branch name (default: 'main')

    Returns:
        Dictionary containing:
        - success: Boolean indicating if operation was successful
        - file_content: The content of the file
        - file_info: Metadata about the file (path, name, size, sha)
        - encoding: File encoding information
    """
    try:
        github_token = os.getenv("GITHUB_TOKEN")
        file_loader = FileLoader(
            repo_name=repo_name, branch=branch, github_token=github_token
        )

        # Load single file
        loaded_files, failed_files = file_loader.github_file_loader.load_files_sync(
            repo_name, branch=branch, file_paths=[file_path], max_concurrent=1
        )

        if failed_files or not loaded_files:
            return {
                "success": False,
                "error": f"Failed to load file: {file_path}",
                "file_content": None,
                "file_info": None,
            }

        file_obj = loaded_files[0]

        file_info = {
            "path": file_obj.path,
            "name": file_obj.name,
            "size": file_obj.size,
            "sha": file_obj.sha,
            "repository": repo_name,
            "branch": branch,
        }

        return {
            "success": True,
            "file_content": file_obj.content,
            "file_info": file_info,
            "encoding": getattr(file_obj, "encoding", "utf-8"),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "file_content": None,
            "file_info": None,
        }


@mcp.tool()
def load_multiple_files(
    repo_name: str,
    file_paths: List[str],
    branch: str = "main",
    max_concurrent: int = 10,
) -> Dict[str, any]:
    """
    Load multiple files from a GitHub repository concurrently.

    Args:
        repo_name: Repository name in format 'owner/repo'
        file_paths: List of file paths to load
        branch: Repository branch name (default: 'main')
        max_concurrent: Maximum number of concurrent requests (default: 10)

    Returns:
        Dictionary containing:
        - success: Boolean indicating if operation was successful
        - loaded_files: List of successfully loaded file objects
        - failed_files: List of file paths that failed to load
        - total_requested: Number of files requested
        - total_loaded: Number of files successfully loaded
        - total_failed: Number of files that failed to load
    """
    try:
        github_token = os.getenv("GITHUB_TOKEN")
        file_loader = FileLoader(
            repo_name=repo_name, branch=branch, github_token=github_token
        )

        # Load multiple files
        loaded_files, failed_files = file_loader.github_file_loader.load_files_sync(
            repo_name,
            branch=branch,
            file_paths=file_paths,
            max_concurrent=max_concurrent,
        )

        # Convert loaded files to dictionaries
        loaded_file_data = []
        for file_obj in loaded_files:
            file_data = {
                "path": file_obj.path,
                "name": file_obj.name,
                "size": file_obj.size,
                "sha": file_obj.sha,
                "content": file_obj.content,
                "repository": repo_name,
                "branch": branch,
                "encoding": getattr(file_obj, "encoding", "utf-8"),
            }
            loaded_file_data.append(file_data)

        return {
            "success": True,
            "loaded_files": loaded_file_data,
            "failed_files": failed_files,
            "total_requested": len(file_paths),
            "total_loaded": len(loaded_files),
            "total_failed": len(failed_files),
        }

    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "loaded_files": [],
            "failed_files": file_paths,
            "total_requested": len(file_paths),
            "total_loaded": 0,
            "total_failed": len(file_paths),
        }
