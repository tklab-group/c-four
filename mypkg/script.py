from mypkg import gitpython
from mypkg import parse_diff
import inspect
import os

def main():
    path = os.getcwd()
    repo = gitpython.get_repo(path)
    diffs = gitpython.get_diffs(repo)
    patches = [ gitpython.make_patch(d.a_path, d.diff.decode()) for d in diffs ]
    gitpython.auto_commit(repo, patches)

    # for diff in diffs[:1]:
    #     print(diff.a_path)
    #     print(diff.diff.decode())
    #     added_chunks, removed_chunks = parse_diff.parse_diff(diff.diff.decode())
    #     print("added_chunks: {0}".format(added_chunks))
    #     print("removed_chunks: {0}".format(removed_chunks))
        
        # patch = gitpython.make_patch(diff.a_path, diff.diff.decode())
        # print(diff.a_path)
        # print(patch)

if __name__ == '__main__':
    main()
