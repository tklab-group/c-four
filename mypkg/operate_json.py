import os.path

from mypkg.models.context import Context
from mypkg.models.add_chunk import AddChunk
from mypkg.models.add_chunk_code import AddChunkCode
from mypkg.models.remove_chunk import RemoveChunk
from mypkg.models.chunk_set import ChunkSet
from mypkg.models.code_info import CodeInfo
from mypkg.models.chunk_relation import ChunkRelation, ChunkType
from mypkg.db_settings import session
import re
from collections import defaultdict
import itertools
import json
from sqlalchemy import or_

def make_single_unit_json(diffs):
    data = {"contexts": {}, "chunk_sets": [], "chunk_relations": []}
    chunk_set = {"add_chunks": {}, "remove_chunks": {}}
    context_id = add_chunk_id = remove_chunk_id = 1
    
    for diff in diffs:
        context = {"path": diff.a_path, "code_infos": []}
        add_chunk_id, remove_chunk_id = _convert_diff_to_chunks(diff, context, chunk_set, context_id, add_chunk_id, remove_chunk_id)

        data["contexts"][context_id] = context
        context_id += 1

    data["chunk_sets"].append(chunk_set)
    return data

def make_file_unit_json(diffs):
    data = {"contexts": {}, "chunk_sets": [], "chunk_relations": []}
    context_id = add_chunk_id = remove_chunk_id = 1
    
    for diff in diffs:
        chunk_set = {"add_chunks": {}, "remove_chunks": {}}
        context = {"path": diff.a_path, "code_infos": []}
        add_chunk_id, remove_chunk_id = _convert_diff_to_chunks(diff, context, chunk_set, context_id, add_chunk_id, remove_chunk_id)

        data["contexts"][context_id] = context
        data["chunk_sets"].append(chunk_set)
        context_id += 1

    return data
    
def set_related_chunks_for_default_mode(input_json):
    context_chunk_dict = defaultdict(list)

    for chunk_set in input_json["chunk_sets"]:
        for chunk_id, add_chunk in chunk_set["add_chunks"].items():
            context_chunk_dict[add_chunk["context_id"]].append({"id": chunk_id, "type": "add"})
        for chunk_id, remove_chunk in chunk_set["remove_chunks"].items():
            context_chunk_dict[remove_chunk["context_id"]].append({"id": chunk_id, "type": "remove"})

    for chunk_sets in context_chunk_dict.values():
        for chunk_pairs in itertools.combinations(chunk_sets, 2):
            input_json["chunk_relations"].append([
                {
                    "chunk_type": chunk_pairs[0]["type"],
                    "chunk_id": chunk_pairs[0]["id"],
                },
                {
                    "chunk_type": chunk_pairs[1]["type"],
                    "chunk_id": chunk_pairs[1]["id"],
                }
            ])

def construct_data_from_json(input_json):
    for context_id, ct in sorted(input_json["contexts"].items()):
        context = Context(ct["path"])
        session.add(context)
        session.commit()
        for code in ct["code_infos"]:
            session.add(CodeInfo(code["line_id"], code["code"], context_id))
            session.commit()
    
    for cs in input_json["chunk_sets"]:
        chunk_set = ChunkSet()
        session.add(chunk_set)
        session.commit()
        
        for chunk_id, ac in sorted(cs["add_chunks"].items()):
            add_chunk = AddChunk(ac["start_id"], ac["end_id"], ac["context_id"], chunk_set.id)
            session.add(add_chunk)
            session.commit()
            
            for acc in ac["codes"]:
                session.add(AddChunkCode(acc, chunk_id))
            session.commit()

        for chunk_id, rc in sorted(cs["remove_chunks"].items()):
            remove_chunk = RemoveChunk(rc["start_id"], rc["end_id"], rc["context_id"], chunk_set.id)
            session.add(remove_chunk)
            session.commit()
    
    for cr in input_json["chunk_relations"]:
        first_chunk, second_chunk = cr[0], cr[1]
        first_chunk_id, second_chunk_id = first_chunk["chunk_id"], second_chunk["chunk_id"]
        
        if first_chunk["chunk_type"] == "add":
            first_chunk_type = ChunkType.ADD
        else:
            first_chunk_type = ChunkType.REMOVE

        if second_chunk["chunk_type"] == "add":
            second_chunk_type = ChunkType.ADD
        else:
            second_chunk_type = ChunkType.REMOVE
        
        session.add(ChunkRelation(first_chunk_id, first_chunk_type, second_chunk_id, second_chunk_type))
    session.commit()

def construct_json_from_data(log_path):
    data = {"chunk_sets": []}
    for cs in ChunkSet.query.all():
        chunk_set = {"add_chunks": [], "remove_chunks": []}
        for ac in cs.add_chunks:
            chunk_set["add_chunks"].append({"id": ac.id, "start_id": ac.start_id, "end_id": ac.end_id, "context_id": ac.context_id})
        for rc in cs.remove_chunks:
            chunk_set["remove_chunks"].append({"id": rc.id, "start_id": rc.start_id, "end_id": rc.end_id, "context_id": rc.context_id})
        if chunk_set["add_chunks"] or chunk_set["remove_chunks"]:
            data["chunk_sets"].append(chunk_set)

    file_num = 1
    file_name = log_path + '/output_' + str(file_num) + '.json'
    while os.path.isfile(file_name):
        file_num += 1
        file_name = log_path + '/output_' + str(file_num) + '.json'
    
    with open(file_name, 'w') as f:
        json.dump(data, f, indent=4)
    return data

def get_related_chunks(cur_chunk, cur_chunks):
    if isinstance(cur_chunk, AddChunk):
        own_type = ChunkType.ADD
    else:
        own_type = ChunkType.REMOVE
    
    first_relations = ChunkRelation.query.filter(ChunkRelation.first_chunk_id == cur_chunk.id, ChunkRelation.first_chunk_type == own_type)
    second_relations = ChunkRelation.query.filter(ChunkRelation.second_chunk_id == cur_chunk.id, ChunkRelation.second_chunk_type == own_type)

    def convert_type_to_class(chunk_type):
        if chunk_type == ChunkType.ADD:
            return AddChunk
        else:
            return RemoveChunk
    
    def is_included(target_chunk_id, target_chunk_type):
        for pair_chunk in cur_chunks:
            if pair_chunk.id == target_chunk_id and type(pair_chunk) == convert_type_to_class(target_chunk_type):
                return True
        return False

    related_chunks = []
    for fr in first_relations:
        if is_included(fr.second_chunk_id, fr.second_chunk_type):
            continue
        chunk_class = convert_type_to_class(fr.second_chunk_type)
        related_chunks.extend(chunk_class.query.filter_by(id = fr.second_chunk_id))
    for sr in second_relations:
        if is_included(sr.first_chunk_id, sr.first_chunk_type):
            continue
        chunk_class = convert_type_to_class(sr.first_chunk_type)
        related_chunks.extend(chunk_class.query.filter_by(id = sr.first_chunk_id))
    
    return related_chunks

def convert_external_json_to_internal(initial_json, diffs):
    data = {"contexts": {}, "chunk_sets": [], "chunk_relations": []}
    chunk_set = {"add_chunks": {}, "remove_chunks": {}}
    context_id = add_chunk_id = remove_chunk_id = 1
    
    for diff in diffs:
        context = {"path": diff.a_path, "code_infos": []}
        add_chunk_id, remove_chunk_id = _convert_diff_to_chunks(diff, context, chunk_set, context_id, add_chunk_id, remove_chunk_id)
        
        data["contexts"][context_id] = context
        context_id += 1
    
    data["chunk_sets"].append(chunk_set)
    _import_initial_json_info(initial_json, data)
    return data

def _import_initial_json_info(initial_json, data):
    add_chunks, remove_chunks = {}, {}
    chunk_sets = []
    
    for cs in data["chunk_sets"]:
        add_chunks.update(cs["add_chunks"])
        remove_chunks.update(cs["remove_chunks"])
    
    for cs in initial_json["chunk_sets"]:
        chunk_set = {"add_chunks": {}, "remove_chunks": {}}
        for chunk in cs:
            if chunk["chunk_type"] == "add":
                chunk_set["add_chunks"][chunk["chunk_id"]] = add_chunks[chunk["chunk_id"]]
            elif chunk["chunk_type"] == "remove":
                chunk_set["remove_chunks"][chunk["chunk_id"]] = remove_chunks[chunk["chunk_id"]]
            else:
                print('Given json is invalid')
                return None
        chunk_sets.append(chunk_set)
    
    data["chunk_sets"] = chunk_sets
    data["chunk_relations"] = initial_json["chunk_relations"]
    
def _convert_diff_to_chunks(diff, context, chunk_set, context_id, add_chunk_id, remove_chunk_id):
    diff = diff.diff.decode().split('\n')
    diff.pop()
    add_line_infos, remove_line_ids = [], []
    regexp = re.compile(',| ')
    add_line_count = 0
    add_line_id = remove_line_id = 0
    
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
        add_chunk_id = _convert_lines_to_add_chunk(add_line_infos, context_id, chunk_set["add_chunks"], add_chunk_id)
    if bool(remove_line_ids):
        remove_chunk_id = _convert_lines_to_remove_chunk(remove_line_ids, context_id, chunk_set["remove_chunks"], remove_chunk_id)
    
    return add_chunk_id, remove_chunk_id

def _convert_lines_to_add_chunk(infos, context_id, add_chunks, add_chunk_id):
    first_info = infos.pop(0)
    start_id, codes = first_info.line_id, [first_info.code]
    prev_id = end_id = start_id
    infos.append(CodeInfo(-1, '', context_id))
    appeared_line = 0
    
    for info in infos:
        line_id = info.line_id
        if line_id == prev_id + 1:
            end_id = line_id
            codes.append(info.code)
        else:
            add_chunk = {"start_id": start_id - appeared_line, "end_id": end_id - appeared_line, "context_id": context_id, "codes": []}
            for code in codes:
                add_chunk["codes"].append(code)
            appeared_line += end_id - start_id + 1
            start_id = end_id = line_id
            codes = [info.code]
            add_chunks[add_chunk_id] = add_chunk
            add_chunk_id += 1
        prev_id = line_id
    
    return add_chunk_id

def _convert_lines_to_remove_chunk(ids, context_id, remove_chunks, remove_chunk_id):
    start_id = ids.pop(0)
    prev_id = end_id = start_id
    ids.append(-1)
    
    for line_id in ids:
        if line_id == prev_id + 1:
            end_id = line_id
        else:
            remove_chunks[remove_chunk_id] = {"start_id": start_id, "end_id": end_id, "context_id": context_id}
            remove_chunk_id += 1
            start_id = end_id = line_id
        prev_id = line_id
    
    return remove_chunk_id
