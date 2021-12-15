from sqlalchemy import Integer, ForeignKey
from sqlalchemy.schema import Column
from mypkg.db_settings import Base, session
from mypkg.make_patch import generate_full_patch
from mypkg.models.code_info import CodeInfo

def decrement_line_id(count, end_id, chunks):
    for chunk in chunks:
        if chunk.start_id > end_id:
            chunk.start_id -= count
            chunk.end_id -= count
            session.commit()
    
    for index, chunk in enumerate(chunks):
        if chunk.start_id > end_id:
            chunks[index].start_id -= count
            chunks[index].end_id -= count
            
class RemoveChunk(Base):
    __tablename__ = 'remove_chunk'
    id = Column(Integer, primary_key=True)
    start_id = Column(Integer, nullable=False)
    end_id = Column(Integer, nullable=False)
    context_id = Column(Integer, ForeignKey('context.id'))
    chunk_set_id = Column(Integer, ForeignKey('chunk_set.id'), nullable=True)
    
    def __init__(self, start_id, end_id, context_id, chunk_set_id=None):
        self.start_id = start_id
        self.end_id = end_id
        self.context_id = context_id

    def generate_remove_patch(self):
        start_id, end_id = self.start_id, self.end_id
        removed_count = end_id - start_id + 1
        a_start_id = b_start_id = start_id
        a_line_num, b_line_num = removed_count, 0
        patch_code = ""
    
        for code_info in self.context.code_infos:
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
    
        patch_code = '@@ -{0},{1} +{2},{3} @@\n'.format(a_start_id, a_line_num, b_start_id, b_line_num) + patch_code
        return generate_full_patch(self.context.path, patch_code)
    
    def reflect_staged_diffs(self):
        start_id, end_id = self.start_id, self.end_id
        removed_count = end_id - start_id + 1
        context = self.context

        context.code_infos = [c for c in context.code_infos if not start_id <= c.line_id <= end_id]
        
        for code_info in context.code_infos:
            if start_id <= code_info.line_id <= end_id:
                CodeInfo.query.filter(CodeInfo.id == code_info.id).delete()
        
        for code_info in context.code_infos:
            if code_info.line_id > end_id:
                code_info.line_id -= removed_count
                session.commit()
    
        decrement_line_id(removed_count, end_id, context.add_chunks)
        decrement_line_id(removed_count, end_id, context.remove_chunks)
