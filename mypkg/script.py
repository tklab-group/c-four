from mypkg import operate_git
from mypkg import make_patch
from mypkg.make_patch import Context
import inspect
import os

def main():
    path = os.getcwd()
    repo = operate_git.get_repo(path)
    diffs = operate_git.get_diffs(repo)
    
    for diff in diffs:
        context = Context()
        context.parse_diff(diff.diff.decode())

        for ac in context.add_chunks:
            patch_content = context.make_add_patch_content(ac)
            patch = make_patch.make_full_patch(diff.a_path, patch_content)
            print(patch)
            operate_git.auto_commit(repo, patch, diff.a_path, ac.start_id, ac.end_id)
            operate_git.apply_patch(repo, patch)
            operate_git.auto_commit(repo, diff.a_path, ac.start_id, ac.end_id)

        for rc in context.remove_chunks:
            patch_content = context.make_remove_patch_content(rc)
            patch = make_patch.make_full_patch(diff.a_path, patch_content)
            print(patch)
            operate_git.auto_commit(repo, patch, diff.a_path, rc.start_id, rc.end_id)

if __name__ == '__main__':
    main()
