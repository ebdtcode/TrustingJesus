"""Push generated content to GitHub via the REST API.

Uses PyGithub to create/update files and commit them in a single commit.
This allows the Azure Function to push results directly without needing
a local git checkout.
"""

from __future__ import annotations

import base64
import logging
from typing import Optional

from github import Github, GithubException, InputGitTreeElement

from .config import GitHubConfig

logger = logging.getLogger(__name__)


class GitHubClient:
    def __init__(self, config: GitHubConfig):
        if not config.token:
            raise ValueError(
                "GITHUB_TOKEN is required. Create a fine-grained PAT with "
                "Contents:read+write permission on the target repo."
            )
        if not config.repo:
            raise ValueError(
                "GITHUB_REPO is required. Set it to 'owner/repo' format."
            )
        self._gh = Github(config.token)
        self._repo = self._gh.get_repo(config.repo)
        self._branch = config.branch

    @classmethod
    def from_config(cls, config: GitHubConfig) -> "GitHubClient":
        return cls(config)

    def commit_files(
        self,
        files: dict[str, str],
        message: str,
    ) -> str:
        """Create a single commit adding/updating multiple files.

        Args:
            files: Mapping of repo-relative paths to file content.
                   e.g. {"sermons_summaries/My_Sermon.md": "---\ntitle:..."}
            message: Commit message.

        Returns:
            The commit SHA.
        """
        ref = self._repo.get_git_ref(f"heads/{self._branch}")
        base_sha = ref.object.sha
        base_commit = self._repo.get_git_commit(base_sha)
        base_tree = base_commit.tree

        tree_elements = []
        for path, content in files.items():
            blob = self._repo.create_git_blob(content, "utf-8")
            tree_elements.append(
                InputGitTreeElement(
                    path=path,
                    mode="100644",
                    type="blob",
                    sha=blob.sha,
                )
            )

        new_tree = self._repo.create_git_tree(tree_elements, base_tree)
        new_commit = self._repo.create_git_commit(
            message=message,
            tree=new_tree,
            parents=[base_commit],
        )
        ref.edit(new_commit.sha)

        logger.info(
            "Committed %d files to %s/%s: %s",
            len(files),
            self._repo.full_name,
            self._branch,
            new_commit.sha[:8],
        )
        return new_commit.sha

    def get_file_content(self, path: str) -> Optional[str]:
        """Read a file from the repo. Returns None if not found."""
        try:
            content_file = self._repo.get_contents(path, ref=self._branch)
            if isinstance(content_file, list):
                return None
            return content_file.decoded_content.decode("utf-8")
        except GithubException as e:
            if e.status == 404:
                return None
            raise

    def update_json_file(self, path: str, updater_fn) -> str:
        """Read a JSON file, apply an updater function, and return the new content.

        The updater_fn receives the parsed JSON and should return the modified object.
        The caller should include the result in a commit_files() call.
        """
        import json

        existing = self.get_file_content(path)
        data = json.loads(existing) if existing else {}
        updated = updater_fn(data)
        return json.dumps(updated, indent=2, ensure_ascii=False)
