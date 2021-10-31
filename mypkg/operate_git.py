from git import Repo
import tempfile

def get_repo(path):
    return Repo(path)

def get_diffs(repo):
    return repo.head.commit.diff(None, create_patch=True).iter_change_type('M')

def apply_patch(repo, patch):
    with tempfile.NamedTemporaryFile(mode='w+') as tf:
        tf.write(patch)
        tf.seek(0)
        repo.git.apply(['--cached', tf.name])
        
def auto_commit(repo, path, start_id, end_id):
    repo.git.commit('-m', '{0}: ({1},{2})'.format(path, start_id, end_id))
