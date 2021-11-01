from sqlalchemy import Integer, ForeignKey
from sqlalchemy.schema import Column
from mypkg.db_settings import Base
from mypkg.make_patch import generate_full_patch

class RemoveChunk(Base):
    __tablename__ = 'remove_chunk'
    id = Column(Integer, primary_key=True)
    start_id = Column(Integer, nullable=False)
    end_id = Column(Integer, nullable=False)
    context_id = Column(Integer, ForeignKey('context.id'))
    
    def __init__(self, start_id, end_id, context_id):
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
