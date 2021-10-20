import git
from git import Repo
import textwrap
import tempfile

def get_repo(path):
    return Repo(path)

def get_diffs(repo):
    return repo.head.commit.diff(None, create_patch=True).iter_change_type('M')

def make_patch(file, diff):
    patch = textwrap.dedent("""\
    diff --git a/{0} b/{0}
    --- a/{0}
    +++ b/{0}
    """.format(file)) + diff

    return patch

def auto_commit(repo, patch):
    with tempfile.NamedTemporaryFile(mode='w+') as tf:
        tf.write(patch)
        tf.seek(0)
        repo.git.apply(['--cached', tf.name])
        repo.git.commit('-m', 'commit: {0}'.format(tf.name))
