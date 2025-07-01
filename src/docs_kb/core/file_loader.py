from typing import Dict, List

from github_file_loader import FileLoader as GitHubFileLoader


class FileLoader:
    def __init__(self, repo_name: str, branch: str = "main", github_token: str = None):
        self.github_file_loader = GitHubFileLoader(token=github_token)
        self.repo_name = repo_name
        self.branch = branch

    def discover_files(self) -> List[Dict[str, str]]:
        discovered_files, _ = self.github_file_loader.client.get_repository_tree(
            self.repo_name,
            self.branch,
            file_extensions=[".md", ".mdx"],
            include_sha=True,
        )
        return discovered_files

    def load_files(self):
        """Load files from the specified GitHub repository."""

        discovered_files = self.discover_files()
        if not discovered_files:
            raise ValueError(
                f"No files found in repository {self.repo_name} on branch {self.branch}"
            )

        file_paths = [file["path"] for file in discovered_files]

        loaded_files, _ = self.github_file_loader.load_files_sync(
            self.repo_name, branch=self.branch, file_paths=file_paths, max_concurrent=20
        )

        return loaded_files
