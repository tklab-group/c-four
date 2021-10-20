from mypkg import gitpython
from mypkg import parse_diff
from mypkg.parse_diff import Context
import inspect
import os

def main():
    path = os.getcwd()
    repo = gitpython.get_repo(path)
    diffs = gitpython.get_diffs(repo)
    # patches = [ gitpython.make_patch(d.a_path, d.diff.decode()) for d in diffs ]
    # for patch in patches:
    #     print(patch)
    # gitpython.auto_commit(repo, patches)
    
    for diff in diffs:
        context = Context()
        context.parse_diff(diff.diff.decode())

        for ac in context.add_chunks:
            patch_code = context.make_add_patch(ac)
            patch = gitpython.make_patch(diff.a_path, patch_code)
            print(patch)
            gitpython.auto_commit(repo, patch)
            gitpython.auto_commit(repo, patch, diff.a_path, ac.start_id, ac.end_id)

        for ac in context.remove_chunks:
            patch_code = context.make_remove_patch(ac)
        for rc in context.remove_chunks:
            patch_code = context.make_remove_patch(rc)
            patch = gitpython.make_patch(diff.a_path, patch_code)
            print(patch)
            gitpython.auto_commit(repo, patch)

if __name__ == '__main__':
    main()
