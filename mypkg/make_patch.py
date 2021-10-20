import re
from argparse import ArgumentParser
import sys
from enum import Enum, auto
import textwrap

class CodeInfo:
    def __init__(self, line_id, code):
        self.line_id = line_id
        self.code = code
        
class Chunk:
    def __init__(self, start_id, end_id):
        self.start_id = start_id
        self.end_id = end_id
        
class AddChunk(Chunk):
    def __init__(self, start_id, end_id, codes):
        super().__init__(start_id, end_id)
        self.codes = codes

def make_full_patch(file, diff):
    patch = textwrap.dedent("""\
    diff --git a/{0} b/{0}
    --- a/{0}
    +++ b/{0}
    """.format(file)) + diff

    return patch

def split_add_chunk(infos, chunks):
    first_info = infos.pop(0)
    start_id, codes = first_info.line_id, [first_info.code]
    prev_id = end_id = start_id
    infos.append(CodeInfo(-1, ''))
    appeared_line = 0
    
    for info in infos:
        id = info.line_id
        if id == prev_id + 1:
            end_id = id
            codes.append(info.code)
        else:
            chunks.append(AddChunk(start_id - appeared_line, end_id - appeared_line, codes))
            appeared_line += end_id - start_id + 1
            start_id = end_id = id
            codes = [info.code]
        prev_id = id

def split_remove_chunk(ids, chunks):
    start_id = ids.pop(0)
    prev_id = end_id = start_id
    ids.append(-1)
    for id in ids:
        if id == prev_id + 1:
            end_id = id
        else:
            chunks.append(Chunk(start_id, end_id))
            start_id = end_id = id
        prev_id = id

def increment_line_id(count, start_id, chunks):
    for index, chunk in enumerate(chunks):
        if chunk.start_id >= start_id:
            chunks[index].start_id += count
            chunks[index].end_id += count

def decrement_line_id(count, end_id, chunks):
    for index, chunk in enumerate(chunks):
        if chunk.start_id > end_id:
            chunks[index].start_id -= count
            chunks[index].end_id -= count

class Context:
    def __init__(self):
        self.code_infos = []
        self.add_chunks = []
        self.remove_chunks = []

    def parse_diff(self, lines):
        lines = lines.split('\n')
        lines.pop()
        add_line_infos, remove_line_ids = [], []
        regexp = re.compile(',| ')
        add_line_count = 0
    
        for line in lines:
            if line.startswith('@@'):
                line_id_strs = [token[1:] for token in regexp.split(line.split('@@')[1]) if token.startswith(('+', '-'))]
                remove_line_id = int(line_id_strs[0])
                add_line_id = remove_line_id + add_line_count
            elif line.startswith('+'):
                add_line_infos.append(CodeInfo(add_line_id, line[1:]))
                add_line_id += 1
                add_line_count += 1
            elif line.startswith('-'):
                remove_line_ids.append(remove_line_id)
                self.code_infos.append(CodeInfo(remove_line_id, line[1:]))
                remove_line_id += 1
                add_line_id += 1
            else:
                self.code_infos.append(CodeInfo(remove_line_id, line[1:]))
                add_line_id += 1
                remove_line_id += 1
        
        if bool(add_line_infos):
            split_add_chunk(add_line_infos, self.add_chunks)
        if bool(remove_line_ids):
            split_remove_chunk(remove_line_ids, self.remove_chunks)
    
    def make_add_patch_content(self, chunk):
        start_id, end_id = chunk.start_id, chunk.end_id
        added_count = end_id - start_id + 1
        a_start_id = b_start_id = start_id
        a_line_num, b_line_num = 0, added_count
        append_flag = False
        insert_index = 0
        patch_code = ""
    
        for index, code_info in enumerate(self.code_infos):
            if code_info.line_id == start_id - 1:
                append_flag = True
                insert_index = index + 1
                patch_code += ' ' + code_info.code + '\n'
                a_start_id = b_start_id = code_info.line_id
                a_line_num += 1
                b_line_num += 1
                for code in chunk.codes:
                    patch_code += '+' + code + '\n'
            elif code_info.line_id == start_id:
                if not append_flag:
                    insert_index = index
                    for code in chunk.codes:
                        patch_code += '+' + code + '\n'
                patch_code += ' ' + code_info.code + '\n'
                a_line_num += 1
                b_line_num += 1

        line_id = start_id

        for index, code_info in enumerate(self.code_infos):
            if code_info.line_id >= start_id:
                self.code_infos[index].line_id += added_count
                
        for code in chunk.codes:
            self.code_infos.insert(insert_index, CodeInfo(line_id, code))
            line_id += 1
            insert_index += 1
            
        increment_line_id(added_count, start_id, self.add_chunks)
        increment_line_id(added_count, start_id, self.remove_chunks)
    
        patch_code = '@@ -{0},{1} +{2},{3} @@\n'.format(a_start_id, a_line_num, b_start_id, b_line_num) + patch_code
        return patch_code
    
    def make_remove_patch_content(self, chunk):
        start_id, end_id = chunk.start_id, chunk.end_id
        patch_code = ""
        removed_count = end_id - start_id + 1
        a_start_id = b_start_id = start_id
        a_line_num = removed_count
        b_line_num = 0
        a_line_num, b_line_num = removed_count, 0
        patch_code = ""
        
        for code_info in self.code_infos:
            if code_info.line_id == start_id - 1:
                patch_code += ' ' + code_info.code + '\n'
                a_start_id = b_start_id = code_info.line_id
                a_line_num += 1
                b_line_num += 1
            elif start_id <= code_info.line_id <= end_id:
                patch_code += '-' + code_info.code + '\n'
            elif code_info.line_id == end_id + 1:
                patch_code += ' ' + code_info.code + '\n'
                a_line_num += 1
                b_line_num += 1
                
        removed_count = end_id - start_id + 1
        
        self.code_infos = [c for c in self.code_infos if not start_id <= c.line_id <= end_id]

        for index, code_info in enumerate(self.code_infos):
            if code_info.line_id > end_id:
                self.code_infos[index].line_id -= removed_count

        for index, chunk in enumerate(self.add_chunks):
            if chunk.start_id > end_id:
                self.add_chunks[index].start_id -= removed_count
                self.add_chunks[index].end_id -= removed_count

        for index, chunk in enumerate(self.remove_chunks):
            if chunk.start_id > end_id:
                self.remove_chunks[index].start_id -= removed_count
                self.remove_chunks[index].end_id -= removed_count
        decrement_line_id(removed_count, end_id, self.add_chunks)
        decrement_line_id(removed_count, end_id, self.remove_chunks)

        patch_code = '@@ -{0},{1} +{2},{3} @@\n'.format(a_start_id, a_line_num, b_start_id, b_line_num) + patch_code
        return patch_code
