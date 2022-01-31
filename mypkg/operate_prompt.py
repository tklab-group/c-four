from mypkg.db_settings import Base, engine, session
from mypkg.models.add_chunk import AddChunk
from mypkg.models.remove_chunk import RemoveChunk
from mypkg.models.chunk_set import ChunkSet
from mypkg.prompts.main_prompt import generate_main_screen, ExitState
from prompt_toolkit.shortcuts import yes_no_dialog
from mypkg.operate_json import get_related_chunks, construct_json_from_data

def run_prompt(repo, log_path):
    while True:
        all_chunks = []
        all_add_chunks = AddChunk.query.all()
        all_remove_chunks = RemoveChunk.query.all()
        all_chunks.extend(all_add_chunks)
        all_chunks.extend(all_remove_chunks)
        
        # split_chunks_by_file(all_chunks)
        chunk_sets = ChunkSet.query.all()
        cur_chunk_set_idx = 0
        
        #Start and run application
        while cur_chunk_set_idx < len(chunk_sets):
            cur_chunks = []
            cur_chunk_set = chunk_sets[cur_chunk_set_idx]
            cur_chunks.extend(cur_chunk_set.add_chunks)
            cur_chunks.extend(cur_chunk_set.remove_chunks)
            
            related_chunks = []
            for cur_chunk in cur_chunks:
                related_chunks.extend(get_related_chunks(cur_chunk, cur_chunks))
            
            pending_chunks = [chunk for chunk in all_chunks if chunk.chunk_set_id is None]
            related_chunks.extend(pending_chunks)
            related_chunks = list(set(related_chunks))
            
            application = generate_main_screen(chunk_sets, cur_chunk_set_idx, related_chunks)
            cur_chunk_set_idx, exit_state = application.run()
            if exit_state == ExitState.APPEND:
                new_chunk_set = ChunkSet()
                session.add(new_chunk_set)
                session.commit()
                chunk_sets.append(new_chunk_set)
            elif exit_state == ExitState.REMOVE:
                chunk_sets.pop(cur_chunk_set_idx)
                ChunkSet.query.filter(ChunkSet.id == cur_chunk_set.id).delete()
                if cur_chunk_set_idx == len(chunk_sets):
                    cur_chunk_set_idx -= 1
        
        construct_json_from_data(log_path)
        # stage and commit current chunk sets
        for chunk_set in chunk_sets:
            chunk_set.commit_self_chunks(repo)
        
        for chunk_set in chunk_sets:
            for add_chunk in chunk_set.add_chunks:
                AddChunk.query.filter(AddChunk.id == add_chunk.id).delete()
            session.commit()
            for remove_chunk in chunk_set.remove_chunks:
                RemoveChunk.query.filter(RemoveChunk.id == remove_chunk.id).delete()
            session.commit()
            ChunkSet.query.filter(ChunkSet.id == chunk_set.id).delete()
            session.commit()
        
        other_chunks = []
        other_chunks.extend(AddChunk.query.all())
        other_chunks.extend(RemoveChunk.query.all())
        
        if other_chunks:
            result = yes_no_dialog(
                title="Confirm staging of pending chunks",
                text="There is still {} pending chunks.\nDo you want to stage these chunks?".format(len(other_chunks))
            ).run()
            
            if result:
                new_chunk_set = ChunkSet()
                session.add(new_chunk_set)
                session.commit()
                for other_chunk in other_chunks:
                    other_chunk.chunk_set_id = new_chunk_set.id
                session.commit()
            else:
                break
        else:
            break
