from sqlalchemy import Integer, ForeignKey
from sqlalchemy.schema import Column
from mypkg.db_settings import Base
from sqlalchemy.orm import relationship
from mypkg.make_patch import generate_full_patch
from mypkg.models.code_info import CodeInfo
from mypkg.db_settings import Base, session

def increment_line_id(count, start_id, chunks):
    for chunk in chunks:
        if chunk.start_id > start_id:
            chunk.start_id += count
            chunk.end_id += count
            session.commit()

class AddChunk(Base):
    __tablename__ = 'add_chunk'
    id = Column(Integer, primary_key=True)
    start_id = Column(Integer, nullable=False)
    end_id = Column(Integer, nullable=False)
    context_id = Column(Integer, ForeignKey('context.id'))
    add_chunk_codes = relationship("AddChunkCode", backref='add_chunk')
    chunk_set_id = Column(Integer, ForeignKey('chunk_set.id'), nullable=True)

    def __init__(self, start_id, end_id, context_id, chunk_set_id=None):
        self.start_id = start_id
        self.end_id = end_id
        self.context_id = context_id

    def generate_add_patch(self):
        start_id, end_id = self.start_id, self.end_id
        added_count = end_id - start_id + 1
        a_start_id = b_start_id = start_id
        a_line_num, b_line_num = 0, added_count
        append_flag = False
        patch_code = ""
    
        for index, code_info in enumerate(self.context.code_infos):
            if code_info.line_id == start_id - 1:
                append_flag = True
                patch_code += ' ' + code_info.code + '\n'
                a_start_id = b_start_id = code_info.line_id
                a_line_num += 1
                b_line_num += 1
                for chunk_code in self.add_chunk_codes:
                    patch_code += '+' + chunk_code.code + '\n'
            elif code_info.line_id == start_id:
                if not append_flag:
                    for chunk_code in self.add_chunk_codes:
                        patch_code += '+' + chunk_code.code + '\n'
                patch_code += ' ' + code_info.code + '\n'
                a_line_num += 1
                b_line_num += 1
    
        patch_code = '@@ -{0},{1} +{2},{3} @@\n'.format(a_start_id, a_line_num, b_start_id, b_line_num) + patch_code
        return generate_full_patch(self.context.path, patch_code)
    
    def reflect_staged_diffs(self):
        start_id, end_id = self.start_id, self.end_id
        added_count = end_id - start_id + 1
        context = self.context
        line_id = start_id

        for code_info in context.code_infos:
            if code_info.line_id >= start_id:
                code_info.line_id += added_count
                session.commit()

        for code in self.add_chunk_codes:
            code_info = CodeInfo(line_id, code.code + '\n', context.id)
            session.add(code_info)
            session.commit()
            line_id += 1
    
        increment_line_id(added_count, start_id, context.add_chunks)
        increment_line_id(added_count, start_id, context.remove_chunks)
