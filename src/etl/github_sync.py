import os
from pathlib import Path
from github import Auth, Github, GithubException
from config.settings import DEFAULT_GITHUB_REPO

def upload_to_github(
    file_path: Path,
    repo_name: str = DEFAULT_GITHUB_REPO,
    token: str = None,
    commit_message: str = "Daily Data Update"
):
    """Upload or update a file in the GitHub repository."""
    token = token or os.environ.get("GIT_TOKEN")
    if not token:
        print("GIT_TOKEN not found in environment. Skipping GitHub upload.")
        return False

    auth = Auth.Token(token)
    try:
        print(f"Connecting to GitHub repository: {repo_name}...")
        g = Github(auth=auth)
        repo = g.get_repo(repo_name)

        relative_repo_path = file_path.name
        with open(file_path, "rb") as f:
            content = f.read()

        try:
            contents = repo.get_contents(relative_repo_path)
            print(f"File {relative_repo_path} exists on GitHub. Updating...")
            repo.update_file(contents.path, commit_message, content, contents.sha)
        except GithubException as e:
            if e.status == 404:
                print(f"File {relative_repo_path} does not exist on GitHub. Creating new...")
                repo.create_file(relative_repo_path, "Initial Data Upload", content)
            else:
                raise

        print("GitHub upload successful!")
        return True
    except Exception as e:
        print(f"GitHub Upload Failed: {e}")
        return False
