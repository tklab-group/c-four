import random
from mypkg.models.chunk_set import ChunkSet
from mypkg.db_settings import session

def split_list(l, n):
    for idx in range(0, len(l), n):
        yield l[idx:idx + n]

def generate_random_chunk_set(add_chunks, remove_chunks, split_num):
    add_chunks_split = list(split_list(random.sample(add_chunks, len(add_chunks)), split_num))
    remove_chunks_split = list(split_list(random.sample(remove_chunks, len(remove_chunks)), split_num))
    
    while add_chunks_split or remove_chunks_split:
        chunk_set = ChunkSet()
        session.add(chunk_set)
        session.commit()
        
        if add_chunks_split:
            for add_chunk in add_chunks_split.pop(0):
                add_chunk.chunk_set_id = chunk_set.id
            session.commit()
        if remove_chunks_split:
            for remove_chunk in remove_chunks_split.pop(0):
                remove_chunk.chunk_set_id = chunk_set.id
            session.commit()
