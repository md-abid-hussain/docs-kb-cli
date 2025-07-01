from textwrap import dedent
from typing import Dict, List

import requests
from mindsdb_sdk import connect
from pandas import DataFrame
from rich.console import Console

from .models import add_repository, create_db_and_tables

console = Console()


class MindsDBClient:
    def __init__(self):
        self.client = connect()
        self.repo_db = "repo_db"
        self.repo_table = "repository"
        create_db_and_tables()

    def ingest(self, repo_name: str, branch: str, data: DataFrame, files: List[Dict]):
        kb = self._create_or_get_kb(repo_name, branch)
        console.print(
            f"🚀 [bold blue]Ingesting[/bold blue] [yellow]{len(data)} records[/yellow] into knowledge base '[cyan]{kb.name}[/cyan]'...",
            style="blue",
        )
        kb.insert(data)
        console.print(
            f"✅ [bold green]Successfully ingested[/bold green] [yellow]{len(data)} records[/yellow] into knowledge base '[cyan]{kb.name}[/cyan]'",
            style="green",
        )

        # Create repository record after successful ingestion
        try:
            repository = add_repository(
                name=repo_name, branch=branch, files=files, knowledge_base_name=kb.name
            )
            return repository
        except Exception as e:
            print(f"⚠️  Warning: Failed to create repository record: {e}")
            # Don't fail the ingestion if DB record creation fails
            return None

    def query(self, kb_name: str, query: str, limit: int = 10):
        kb = self.client.knowledge_bases.get(kb_name)
        if not kb:
            raise ValueError(f"Knowledge base '{kb_name}' does not exist.")
        result = kb.find(query, limit=limit).fetch()
        if result.empty:
            print(f"No results found for query: {query}")
            return None

        return result

    def _create_or_get_kb(self, repo_name: str, branch: str):
        knowledge_base_name = self._get_kb_name(repo_name, branch)
        try:
            kb = self.client.knowledge_bases.get(knowledge_base_name)
            return kb
        except (requests.exceptions.HTTPError, Exception) as e:
            if "not found" in str(e).lower() or "does not exist" in str(e).lower():
                print(f"Creating knowledge base '{knowledge_base_name}'...")
                create_kb_sql = dedent(
                    f"""
                CREATE KNOWLEDGE_BASE {knowledge_base_name}
                USING
                    embedding_model = {{
                        "provider": "ollama",
                        "model_name": "nomic-embed-text",
                        "base_url":"http://localhost:11434"
                    }},
                    reranking_model = {{
                        "provider": "ollama",
                        "model_name": "gemma2",
                        "base_url":"http://localhost:11434"
                    }},
                    metadata_columns = ['repository', 'branch', 'path', 'name', 'size', 'sha'],
                    content_columns = ['content'],
                    id_column = 'id';
                """
                )

                self.client.query(create_kb_sql).fetch()
                return self.client.knowledge_bases.get(knowledge_base_name)
            else:
                raise e

    def _get_kb_name(self, repo_name: str, branch: str) -> str:
        return f"kb_{repo_name.replace('/', '_').replace('-', '_')}_{branch}"

    def _delete_knowledge_base(self, kb_name: str):
        try:
            self.client.knowledge_bases.drop(kb_name)
            print(f"Knowledge base '{kb_name}' deleted successfully.")
        except Exception as e:
            print(f"Error deleting knowledge base '{kb_name}': {e}")


mindsdb_client = MindsDBClient()
