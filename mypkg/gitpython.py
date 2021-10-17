import os
import git
from git import Repo

path = os.getcwd()
repo = Repo(path)
print(repo.untracked_files)

def get_repo():
    return Repo(os.getcwd)