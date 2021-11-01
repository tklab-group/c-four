from mypkg import operate_git
import os
from mypkg.db_settings import Base, engine, session
from mypkg.random_chunk import split_list, generate_random_chunk_set
from mypkg.intractive_module import yes_no_input
from mypkg.models.context import Context

def main():
    path = os.getcwd()
    repo = operate_git.get_repo(path)
    diffs = operate_git.get_diffs(repo)
    Base.metadata.create_all(engine)
    
    for diff in diffs:
        context = Context(diff.a_path)
        session.add(context)
        session.commit()
        context.convert_diff_to_chunk(diff.diff.decode())
        
    all_context = Context.query.all()
    for context in all_context:
        for add_chunk in context.add_chunks:
            print((add_chunk.start_id, add_chunk.end_id))
            print(add_chunk.generate_add_patch())
        for remove_chunk in context.remove_chunks:
            print((remove_chunk.start_id, remove_chunk.end_id))
            print(remove_chunk.generate_remove_patch())

    # while chunk_sets:
    #     print('patch content')
    #     for add_chunk in chunk_set.add_chunks:
    #         patch_content = context.make_add_patch_content(add_chunk)
    #         patch = make_patch.make_full_patch(diff.a_path, patch_content)
    #         print(patch)
    #     for remove_chunk in chunk_set.remove_chunks:
    #         patch_content = context.make_remove_patch_content(remove_chunk)
    #         patch = make_patch.make_full_patch(diff.a_path, patch_content)
    #         print(patch)
    #
    #     if yes_no_input():
    #         chunk_set = chunk_sets.pop(0)
    
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
