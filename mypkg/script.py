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
    
    other_chunk_set = ChunkSet()
    session.add(other_chunk_set)
    session.commit()
    
    cur_chunk_set_idx = 0
    chunk_sets_size = len(chunk_sets)
    
    while cur_chunk_set_idx < chunk_sets_size:
        application = generate_chunk_select_prompt(cur_chunk_set_idx, other_chunk_set.id)
        cur_chunk_set_idx = application.run()

if __name__ == '__main__':
    main()
