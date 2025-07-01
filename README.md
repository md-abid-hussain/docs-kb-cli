# 📚 docs-kb

AI-powered documentation knowledge base for GitHub repositories using MindsDB and local LLMs.

## 🌟 Features

- 🔍 **Intelligent Document Discovery**: Automatically finds and processes Markdown files (.md, .mdx) from GitHub repositories
- 🤖 **Local AI-Powered Search**: Uses Ollama with nomic-embed-text embeddings and gemma2 reranking for privacy-focused AI
- 💬 **Interactive Chat Interface**: Query your documentation with natural language
- 🔄 **Smart Sync**: Efficiently syncs repository changes by comparing file SHAs
- 📊 **Repository Management**: Track multiple repositories with detailed metadata
- 🗃️ **Local Database**: SQLite-based storage for repository metadata and file tracking

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

## 📖 Detailed Commands

### `docs-kb ingest`
Ingest files from a GitHub repository into the knowledge base.

```bash
docs-kb ingest REPO_NAME [OPTIONS]

Arguments:
  REPO_NAME  GitHub repository name (e.g., 'owner/repo')  [required]

Options:
  -b, --branch TEXT  Branch to ingest from  [default: main]
  --help            Show this message and exit
```

**Examples:**
```bash
# Ingest from main branch
docs-kb ingest microsoft/vscode

# Ingest from specific branch
docs-kb ingest facebook/react --branch canary

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

### `docs-kb version`
Show version and project information.

```bash
docs-kb version [OPTIONS]

Options:
  --help  Show this message and exit
```

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

## 🚨 Troubleshooting

### Common Issues

**1. Ollama Connection Error**
```bash
# Check if Ollama is running
curl http://localhost:11434/api/tags

# Start Ollama if not running
ollama serve
```

**2. MindsDB Connection Error**
- Ensure MindsDB is running and accessible
- Check connection credentials if using MindsDB Cloud

**3. GitHub Rate Limits**
```bash
# Set GitHub token to increase rate limits
export GITHUB_TOKEN=your_token
```

**4. No Files Found**
- Repository might not contain .md or .mdx files
- Check if branch exists and has documentation

**5. Permission Errors**
```bash
# Ensure write permissions for database directory
chmod 755 ~/.docs-kb/
```


## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## 📋 Requirements

- Python 3.9+
- Ollama with nomic-embed-text and gemma2 models
- MindsDB (local or cloud)
- Optional: GitHub Personal Access Token

## 📄 License

MIT

## 🙋‍♂️ Support

For issues and questions:
1. Check the troubleshooting section above
2. Search existing issues
3. Create a new issue with detailed information

---

Built with ❤️ using MindsDB, Ollama, and Python