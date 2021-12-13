from mypkg.models.chunk_set import ChunkSet
from mypkg.db_settings import session

def split_chunks_by_file(all_chunks):
    appeared_paths = {}
    
    for chunk in all_chunks:
        if chunk.context.path not in appeared_paths:
            chunk_set = ChunkSet()
            session.add(chunk_set)
            session.commit()
    
            appeared_paths[chunk.context.path] = chunk_set.id
            chunk.chunk_set_id = chunk_set.id
        else:
            chunk_set = ChunkSet.query.filter(ChunkSet.id == appeared_paths[chunk.context.path]).first()
            chunk.chunk_set_id = chunk_set.id
