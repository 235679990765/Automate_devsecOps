import os, uuid, git

WORKSPACE = "./workspace"

def load_repo(repo_input: str) -> str:
    os.makedirs(WORKSPACE, exist_ok=True)

    if os.path.exists(repo_input):
        return os.path.abspath(repo_input)

    repo_id = str(uuid.uuid4())
    path = os.path.join(WORKSPACE, repo_id)
    git.Repo.clone_from(repo_input, path)
    return path
