from mypkg import operate_git
import os
from mypkg.db_settings import Base, engine, session
from mypkg.random_chunk import split_list, generate_random_chunk_set
from mypkg.intractive_module import yes_no_input
from mypkg.models.context import Context
from mypkg.models.add_chunk import AddChunk
from mypkg.models.remove_chunk import RemoveChunk
from mypkg.models.chunk_set import ChunkSet
from prompt_toolkit import Application
from mypkg.prompt import generate_chunk_select_prompt

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

    generate_random_chunk_set(AddChunk.query.all(), RemoveChunk.query.all(), 2)
    chunk_sets = ChunkSet.query.all()
    if chunk_sets:
        chunk_set = chunk_sets.pop(0)
    
    while True:
        application = generate_chunk_select_prompt(chunk_set.add_chunks, chunk_set.remove_chunks)
        application.run()
        if chunk_sets:
            chunk_set = chunk_sets.pop(0)
        else:
            break
    
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
