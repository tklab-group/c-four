from mypkg import operate_git
from mypkg import make_patch
from mypkg.make_patch import Context
import inspect
import os
import itertools
import random
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine

class ChunkSet:
    def __init__(self):
        self.add_chunks = []
        self.remove_chunks = []
        
    def extend_add_chunks(self, add_chunks):
        self.add_chunks.extend(add_chunks)

    def extend_remove_chunks(self, remove_chunks):
        self.remove_chunks.extend(remove_chunks)

def split_list(l, n):
    for idx in range(0, len(l), n):
        yield l[idx:idx + n]

def generate_random_chunk_set(add_chunks, remove_chunks):
    chunk_sets = []
    split_num = 2
    
    add_chunks_split = list(split_list(random.sample(add_chunks, len(add_chunks)), split_num))
    remove_chunks_split = list(split_list(random.sample(remove_chunks, len(remove_chunks)), split_num))
    
    while add_chunks_split or remove_chunks_split:
        chunk_set = ChunkSet()
        if add_chunks_split:
            add_chunk = add_chunks_split.pop(0)
            chunk_set.extend_add_chunks(add_chunk)
        if remove_chunks_split:
            remove_chunk = remove_chunks_split.pop(0)
            chunk_set.extend_remove_chunks(remove_chunk)
        chunk_sets.append(chunk_set)

    return chunk_sets

def yes_no_input():
    choice = input("Please respond with 'yes' or 'no' [y/N]: ").lower()
    if choice in ['y', 'ye', 'yes']:
        return True
    elif choice in ['n', 'no']:
        return False
    else:
        return False

def main():
    path = os.getcwd()
    repo = operate_git.get_repo(path)
    diffs = operate_git.get_diffs(repo)
    add_chunks, remove_chunks = [], []
    
    for diff in diffs:
        context = Context()
        context.parse_diff(diff.diff.decode(), diff.a_path)
        add_chunks.extend(context.add_chunks)
        remove_chunks.extend(context.remove_chunks)
    
    chunk_sets = generate_random_chunk_set(add_chunks, remove_chunks)
    chunk_set = chunk_sets.pop(0)
    
    while chunk_sets:
        print('patch content')
        for add_chunk in chunk_set.add_chunks:
            patch_content = context.make_add_patch_content(add_chunk)
            patch = make_patch.make_full_patch(diff.a_path, patch_content)
            print(patch)
        for remove_chunk in chunk_set.remove_chunks:
            patch_content = context.make_remove_patch_content(remove_chunk)
            patch = make_patch.make_full_patch(diff.a_path, patch_content)
            print(patch)
        
        if yes_no_input():
            chunk_set = chunk_sets.pop(0)
    
    # for context in contexts:
    #     for ac in context.add_chunks:
    #         patch_content = context.make_add_patch_content(ac)
    #         patch = make_patch.make_full_patch(diff.a_path, patch_content)
    #         print(patch)
    #         operate_git.apply_patch(repo, patch)
    #         operate_git.auto_commit(repo, diff.a_path, ac.start_id, ac.end_id)
    #
    #     for rc in context.remove_chunks:
    #         patch_content = context.make_remove_patch_content(rc)
    #         patch = make_patch.make_full_patch(diff.a_path, patch_content)
    #         print(patch)
    #         operate_git.apply_patch(repo, patch)
    #         operate_git.auto_commit(repo, diff.a_path, rc.start_id, rc.end_id)

if __name__ == '__main__':
    main()
