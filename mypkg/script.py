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
        
    unstage_chunk_set = ChunkSet()
    session.add(unstage_chunk_set)
    session.commit()
    
    while chunk_sets:
        chunk_set = chunk_sets.pop(0)
        application = generate_chunk_select_prompt(chunk_set, unstage_chunk_set.id)
        application.run()
        
        if not chunk_sets:
            if unstage_chunk_set.add_chunks or unstage_chunk_set.remove_chunks:
                chunk_sets.append(unstage_chunk_set)
                unstage_chunk_set = ChunkSet()
                session.add(unstage_chunk_set)
                session.commit()

if __name__ == '__main__':
    main()
