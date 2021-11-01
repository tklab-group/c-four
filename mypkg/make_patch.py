import textwrap

def generate_full_patch(path, diff):
    patch = textwrap.dedent("""\
    diff --git a/{0} b/{0}
    --- a/{0}
    +++ b/{0}
    """.format(path)) + diff
 
    return patch

def increment_line_id(count, start_id, chunks):
    for index, chunk in enumerate(chunks):
        if chunk.start_id > start_id:
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
        removed_count = end_id - start_id + 1
        a_start_id = b_start_id = start_id
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
        
        self.code_infos = [c for c in self.code_infos if not start_id <= c.line_id <= end_id]

        for index, code_info in enumerate(self.code_infos):
            if code_info.line_id > end_id:
                self.code_infos[index].line_id -= removed_count

        decrement_line_id(removed_count, end_id, self.add_chunks)
        decrement_line_id(removed_count, end_id, self.remove_chunks)

        patch_code = '@@ -{0},{1} +{2},{3} @@\n'.format(a_start_id, a_line_num, b_start_id, b_line_num) + patch_code
        return patch_code
    
