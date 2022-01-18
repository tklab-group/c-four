from mypkg.models.context import Context
from mypkg.models.add_chunk import AddChunk
from mypkg.models.add_chunk_code import AddChunkCode
from mypkg.models.remove_chunk import RemoveChunk
from mypkg.models.chunk_set import ChunkSet
from mypkg.models.code_info import CodeInfo
from mypkg.db_settings import session
import re

def make_file_unit_json(diffs):
    data = {"contexts": [], "chunk_sets": []}
    add_line_id = remove_line_id = 0
    context_id = 1
    
    for diff in diffs:
        context = {"id": context_id, "path": diff.a_path, "code_infos": []}
        chunk_set = {"add_chunks": [], "remove_chunks": []}
        diff = diff.diff.decode().split('\n')
        diff.pop()
        add_line_infos, remove_line_ids = [], []
        regexp = re.compile(',| ')
        add_line_count = 0

        for line in diff:
            if line.startswith('@@'):
                line_id_strs = [token[1:] for token in regexp.split(line.split('@@')[1]) if token.startswith(('+', '-'))]
                remove_line_id = int(line_id_strs[0])
                add_line_id = remove_line_id + add_line_count
            elif line.startswith('+'):
                add_line_infos.append(CodeInfo(add_line_id, line[1:], context_id))
                add_line_id += 1
                add_line_count += 1
            elif line.startswith('-'):
                remove_line_ids.append(remove_line_id)
                context["code_infos"].append({"code": line[1:], "line_id": remove_line_id})
                remove_line_id += 1
                add_line_id += 1
            else:
                context["code_infos"].append({"code": line[1:], "line_id": remove_line_id})
                add_line_id += 1
                remove_line_id += 1
        
        if bool(add_line_infos):
            convert_lines_to_add_chunk(add_line_infos, context_id, chunk_set)
        if bool(remove_line_ids):
            convert_lines_to_remove_chunk(remove_line_ids, context_id, chunk_set)

        data["contexts"].append(context)
        data["chunk_sets"].append(chunk_set)
        context_id += 1
        
    return data

def convert_lines_to_add_chunk(infos, context_id, chunk_set):
    first_info = infos.pop(0)
    start_id, codes = first_info.line_id, [first_info.code]
    prev_id = end_id = start_id
    infos.append(CodeInfo(-1, '', context_id))
    appeared_line = 0
    add_chunk_id = 1
    
    for info in infos:
        id = info.line_id
        if id == prev_id + 1:
            end_id = id
            codes.append(info.code)
        else:
            add_chunk = {"id": add_chunk_id, "start_id": start_id - appeared_line, "end_id": end_id - appeared_line, "context_id": context_id, "codes": []}
            for code in codes:
                add_chunk["codes"].append(code)
            appeared_line += end_id - start_id + 1
            start_id = end_id = id
            codes = [info.code]
            add_chunk_id += 1
            chunk_set["add_chunks"].append(add_chunk)
        prev_id = id

def convert_lines_to_remove_chunk(ids, context_id, chunk_set):
    start_id = ids.pop(0)
    prev_id = end_id = start_id
    ids.append(-1)
    remove_chunk_id = 1
    
    for id in ids:
        if id == prev_id + 1:
            end_id = id
        else:
            chunk_set["remove_chunks"].append({"id": remove_chunk_id, "start_id": start_id, "end_id": end_id, "context_id": context_id})
            start_id = end_id = id
        prev_id = id
    
def convert_json_to_data(json):
    for ct in json["contexts"]:
        context = Context(ct["path"])
        session.add(context)
        session.commit()
        for code in ct["code_infos"]:
            session.add(CodeInfo(code["line_id"], code["code"], context.id))
            session.commit()
    
    for cs in json["chunk_sets"]:
        chunk_set = ChunkSet()
        session.add(chunk_set)
        session.commit()
        
        for ac in cs["add_chunks"]:
            add_chunk = AddChunk(ac["start_id"], ac["end_id"], ac["context_id"], chunk_set.id)
            session.add(add_chunk)
            session.commit()
            for acc in ac["codes"]:
                session.add(AddChunkCode(acc, add_chunk.id))
            session.commit()

        for rc in cs["remove_chunks"]:
            remove_chunk = RemoveChunk(rc["start_id"], rc["end_id"], rc["context_id"], chunk_set.id)
            session.add(remove_chunk)
            session.commit()
