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
