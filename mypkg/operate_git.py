from git import Repo
import tempfile

def get_repo(path):
    return Repo(path)

def get_diffs(repo):
    return repo.index.diff(None, create_patch=True).iter_change_type('M')

def apply_patch(repo, patch):
    with tempfile.NamedTemporaryFile(mode='w+') as tf:
        tf.write(patch)
        tf.seek(0)
        repo.git.apply(['--cached', tf.name])
        
def commit_cur_staging(repo, message):
    repo.git.commit('-m', message)
