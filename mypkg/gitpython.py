import os
import git
from git import Repo

def get_repo():
    return Repo(os.getcwd())
