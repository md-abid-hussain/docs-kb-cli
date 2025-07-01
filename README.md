# 📚 docs-kb

CLI tool to create knowledge base on open source docs using **MindsDB Knowledge Base** and Ollama and serve to agent with MCP (Model Context Protocol) server.

## 🌟 Features

- 🔍 **Intelligent Document Discovery**: Automatically finds and processes Markdown files (.md, .mdx) from GitHub repositories
- 🤖 **Local AI-Powered Search**: Uses Ollama with nomic-embed-text embeddings and gemma2 reranking for privacy-focused AI
- 💬 **Interactive Chat Interface**: Query your documentation with natural language
- 🔄 **Smart Sync**: Efficiently syncs repository changes by comparing file SHAs
- 📊 **Repository Management**: Track multiple repositories with detailed metadata
- 🗃️ **Local Database**: SQLite-based storage for repository metadata and file tracking
- 🌐 **MCP Server**: Model Context Protocol server for integration with AI assistants like Claude Desktop
- 🔧 **GitHub Integration**: Create GitHub clients directly in MindsDB for enhanced repository access

## 🛠️ Prerequisites

### 1. Ollama Setup
Install and run [Ollama](https://ollama.ai/) locally:

```bash
# Install required models
ollama pull nomic-embed-text
ollama pull gemma2

# Ensure Ollama is running on http://localhost:11434
ollama serve
```

### 2. MindsDB
Install and run MindsDB [docs](https://docs.mindsdb.com/setup/self-hosted/docker).

### 3. GitHub Token
For private repositories or to avoid rate limits:
```bash
export GITHUB_TOKEN=your_github_token
```

## 📦 Installation

### Using uv (Recommended)
```bash
# Clone the repository
git clone <your-repo-url>
cd docs-kb

# Install with uv
uv pip install -e .
```

### Using pip
```bash
pip install -e .
```

## 🚀 Quick Start

### 1. Ingest a Repository
```bash
# Ingest documentation from a GitHub repository
docs-kb ingest owner/repository-name

# Ingest from a specific branch
docs-kb ingest owner/repository-name --branch develop

# Create GitHub client in MindsDB during ingestion
docs-kb ingest owner/repository-name --mindsdb-github-client
```

### 2. Query Your Documentation
```bash
# Start interactive chat with your documentation
docs-kb query
```

### 3. List Repositories
```bash
# View all ingested repositories
docs-kb list
```

### 4. Manage Repositories
```bash
# Sync, delete, or manage repositories
docs-kb manage
```

### 5. Start MCP Server
```bash
# Start MCP server for AI assistant integration
docs-kb start-mcp-server

# Start on custom host and port
docs-kb start-mcp-server --host 0.0.0.0 --port 8080
```

## 📖 Detailed Commands

### `docs-kb ingest`
Ingest files from a GitHub repository into the knowledge base.

```bash
docs-kb ingest REPO_NAME [OPTIONS]

Arguments:
  REPO_NAME  GitHub repository name (e.g., 'owner/repo')  [required]

Options:
  -b, --branch TEXT                Branch to ingest from  [default: main]
  -m, --mindsdb-github-client     Create GitHub client in MindsDB server
  --help                          Show this message and exit
```

**Examples:**
```bash
# Ingest from main branch
docs-kb ingest microsoft/vscode

# Ingest from specific branch
docs-kb ingest facebook/react --branch canary

# Ingest with GitHub client creation in MindsDB
docs-kb ingest microsoft/vscode --mindsdb-github-client

# Ingest with GitHub token for private repos
GITHUB_TOKEN=your_token docs-kb ingest private-org/private-repo
```

### `docs-kb query`
Interactive chat interface to query your documentation.

```bash
docs-kb query [OPTIONS]

Options:
  --help  Show this message and exit
```

**Usage:**
- Select a repository from the list
- Ask questions in natural language
- Type 'exit', 'quit', or press Ctrl+C to end the session

**Example Session:**
```
🗣️  You: How do I set up authentication?
🤖 Bot: Based on the documentation, here's how to set up authentication...

🗣️  You: What are the available configuration options?
🤖 Bot: The available configuration options include...
```

### `docs-kb list`
Display all ingested repositories with their metadata.

```bash
docs-kb list [OPTIONS]

Options:
  --help  Show this message and exit
```

**Output includes:**
- Repository name and branch
- Knowledge base name
- Number of files
- Creation date
- Last sync date

### `docs-kb manage`
Manage existing repositories with options to sync or delete.

```bash
docs-kb manage [OPTIONS]

Options:
  --help  Show this message and exit
```

**Available Actions:**
- **🔄 Sync**: Update repository with latest changes from GitHub
- **🗑️ Delete**: Remove repository and its knowledge base permanently

### `docs-kb start-mcp-server`
Start the Model Context Protocol (MCP) server for AI assistant integration.

```bash
docs-kb start-mcp-server [OPTIONS]

Options:
  -h, --host TEXT     Host to bind to  [default: localhost]
  -p, --port INTEGER  Port to bind to  [default: 8000]
  --help             Show this message and exit
```

**Examples:**
```bash
# Start server on default localhost:8000
docs-kb start-mcp-server

# Start server on custom host and port
docs-kb start-mcp-server --host 0.0.0.0 --port 8080

# Start server accessible from other machines
docs-kb start-mcp-server --host 0.0.0.0
```

### `docs-kb version`
Show version and project information.

```bash
docs-kb version [OPTIONS]

Options:
  --help  Show this message and exit
```

## 🌐 MCP Server Integration

The docs-kb MCP server provides AI assistants like Claude Desktop with powerful tools to interact with your documentation knowledge base and GitHub repositories.

### Available MCP Tools

#### 1. `how_to_use_docs_kb_mcp()`
Get comprehensive usage guide for the MCP server.

#### 2. `list_available_repositories()`
List all ingested repositories in the knowledge base.

**Returns:**
- Repository ID, name, branch
- Knowledge base name
- Creation and ingestion timestamps
- File count

#### 3. `query_repository_docs(repo_name, branch, query, limit=10)`
Query a repository's knowledge base with natural language.

**Parameters:**
- `repo_name`: Repository name (e.g., 'owner/repo')
- `branch`: Repository branch
- `query`: Natural language search query
- `limit`: Maximum results to return

**Returns:**
- Search results with content and metadata
- Relevance scores and source information
- Total results count

#### 4. `get_repository_tree(repo_name, branch, file_extensions, path_filter)`
Browse GitHub repository file structure with filtering.

**Parameters:**
- `repo_name`: Repository name
- `branch`: Repository branch (default: 'main')
- `file_extensions`: File types to include (e.g., ['.md', '.py'])
- `path_filter`: Path prefix filter (e.g., 'docs/')

**Returns:**
- Filtered list of files
- Total file count
- Applied filters summary

#### 5. `get_single_file(repo_name, file_path, branch='main')`
Retrieve content of a specific file from GitHub.

**Parameters:**
- `repo_name`: Repository name
- `file_path`: Path to the file
- `branch`: Repository branch

**Returns:**
- File content and metadata
- File information (size, SHA, etc.)
- Encoding details

#### 6. `load_multiple_files(repo_name, file_paths, branch='main', max_concurrent=10)`
Load multiple files from GitHub repository concurrently.

**Parameters:**
- `repo_name`: Repository name
- `file_paths`: List of file paths to load
- `branch`: Repository branch
- `max_concurrent`: Maximum concurrent requests

**Returns:**
- Successfully loaded files
- Failed file paths
- Loading statistics

### MCP Server Setup

1. **Start the MCP Server:**
   ```bash
   docs-kb start-mcp-server
   ```

2. **Configure MCP Client** 
    - Use the MCP client in your AI assistant
    - Connect to the server at `http://localhost:8000` (or custom host/port)

3. **Use with AI Assistants:**
   - The server provides tools for querying ingested documentation
   - Browse and access any GitHub repository files
   - Perform natural language searches across documentation

## 🔄 Sync Process

The sync command intelligently compares your local knowledge base with the latest GitHub repository state:

1. **Discovery**: Fetches current file list from GitHub
2. **Comparison**: Compares file SHAs to detect changes
3. **Classification**: Categorizes files as new, modified, deleted, or unchanged
4. **Selective Update**: Only processes files that have actually changed
5. **Knowledge Base Update**: Updates embeddings for changed content
6. **Metadata Update**: Updates local database with new file information

**Change Types:**
- 🆕 **New Files**: Added to knowledge base
- 📝 **Modified Files**: Content updated in knowledge base
- 🗑️ **Deleted Files**: Removed from knowledge base
- ✅ **Unchanged Files**: No action needed

## 🗄️ Data Storage

### Local Database
- **Location**: `~/.docs-kb/docs_kb.db` (SQLite)
- **Contents**: Repository metadata, file tracking, sync history
- **Schema**: Defined in [`src/docs_kb/core/models.py`](src/docs_kb/core/models.py)

### Knowledge Base
- **Platform**: MindsDB
- **Embeddings**: Ollama nomic-embed-text model
- **Reranking**: Ollama gemma2 model
- **Content**: Document chunks with metadata (repository, branch, path, SHA, etc.)

### GitHub Integration
- **MindsDB GitHub Clients**: Optional GitHub database connections in MindsDB
- **Purpose**: Enhanced repository access and integration
- **Creation**: Use `--mindsdb-github-client` flag during ingestion

## 🏗️ Architecture

### Core Components

- **[`src/docs_kb/core/file_loader.py`](src/docs_kb/core/file_loader.py)**: GitHub file discovery and loading
- **[`src/docs_kb/core/mindsdb_client.py`](src/docs_kb/core/mindsdb_client.py)**: MindsDB knowledge base operations
- **[`src/docs_kb/core/models.py`](src/docs_kb/core/models.py)**: Database models and operations
- **[`src/docs_kb/cli.py`](src/docs_kb/cli.py)**: Command-line interface

### Commands

- **[`src/docs_kb/commands/ingest.py`](src/docs_kb/commands/ingest.py)**: Repository ingestion logic
- **[`src/docs_kb/commands/query.py`](src/docs_kb/commands/query.py)**: Interactive chat interface
- **[`src/docs_kb/commands/sync.py`](src/docs_kb/commands/sync.py)**: Smart synchronization
- **[`src/docs_kb/commands/manage.py`](src/docs_kb/commands/manage.py)**: Repository management
- **[`src/docs_kb/commands/list.py`](src/docs_kb/commands/list.py)**: Repository listing
- **[`src/docs_kb/commands/start_mcp.py`](src/docs_kb/commands/start_mcp.py)**: MCP server startup

### MCP Server

- **[`src/docs_kb/mcp_server/server.py`](src/docs_kb/mcp_server/server.py)**: FastMCP server implementation
- **Protocol**: Model Context Protocol for AI assistant integration
- **Tools**: 6 comprehensive tools for documentation and repository access

## 🔧 Configuration

### Environment Variables

```bash
# GitHub token for private repositories or higher rate limits
export GITHUB_TOKEN=your_github_personal_access_token
```

### Ollama Configuration

Ensure these models are available:
```bash
ollama list
# Should show:
# nomic-embed-text:latest
# gemma2:latest
```

### MindsDB GitHub Client

When using the `--mindsdb-github-client` flag, docs-kb creates a GitHub database connection in MindsDB:

```sql
CREATE DATABASE github_client
WITH ENGINE = 'github'
PARAMETERS = {
    repository = 'owner/repo',
    branch = 'main',
    "api_key": 'your_github_token'
};
```

This enables MindsDB MCP for advance repository analysis and querying when combined with docs-kb-mcp.


## 📋 Requirements

- Python 3.13+
- Ollama with nomic-embed-text and gemma2 models
- MindsDB (local or cloud)
- Optional: GitHub Personal Access Token
- For MCP: Compatible AI assistant (Claude Desktop, etc.)

## 📄 License

MIT

## 🙋‍♂️ Support

For issues and questions:
1. Check the troubleshooting section above
2. Search existing issues
3. Create a new issue with detailed information

---

Built with ❤️ using MindsDB, Ollama, FastMCP, and Python