from sqlalchemy import Integer, String, Text, ForeignKey
from sqlalchemy.schema import Column
from sqlalchemy.orm import relationship
from mypkg.db_settings import Base, session
from mypkg.models.code_info import CodeInfo
from mypkg.models.remove_chunk import RemoveChunk
from mypkg.models.add_chunk import AddChunk
from mypkg.models.add_chunk_code import AddChunkCode
import re

class Context(Base):
    __tablename__ = 'context'
    id = Column(Integer, primary_key=True)
    path = Column(String(255), nullable=False)
    code_infos = relationship("CodeInfo", backref='context')
    remove_chunks = relationship("RemoveChunk", backref='context')
    add_chunks = relationship("AddChunk", backref='context')
    
    def __init__(self, path):
        self.path = path

    def convert_diff_to_chunk(self, diff):
        diff = diff.split('\n')
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
                add_line_infos.append(CodeInfo(add_line_id, line[1:], self.id))
                add_line_id += 1
                add_line_count += 1
            elif line.startswith('-'):
                remove_line_ids.append(remove_line_id)
                session.add(CodeInfo(remove_line_id, line[1:], self.id))
                remove_line_id += 1
                add_line_id += 1
            else:
                session.add(CodeInfo(remove_line_id, line[1:], self.id))
                add_line_id += 1
                remove_line_id += 1

        session.commit()
        if bool(add_line_infos):
            self.convert_lines_to_add_chunk(add_line_infos)
        if bool(remove_line_ids):
            self.convert_lines_to_remove_chunk(remove_line_ids)
            
    def convert_lines_to_add_chunk(self, infos):
        first_info = infos.pop(0)
        start_id, codes = first_info.line_id, [first_info.code]
        prev_id = end_id = start_id
        infos.append(CodeInfo(-1, '', self.id))
        appeared_line = 0
    
        for info in infos:
            id = info.line_id
            if id == prev_id + 1:
                end_id = id
                codes.append(info.code)
            else:
                new_chunk = AddChunk(start_id - appeared_line, end_id - appeared_line, self.id)
                session.add(new_chunk)
                session.commit()
                for code in codes:
                    session.add(AddChunkCode(code, new_chunk.id))
                appeared_line += end_id - start_id + 1
                start_id = end_id = id
                codes = [info.code]
            prev_id = id
            
        session.commit()

    def convert_lines_to_remove_chunk(self, ids):
        start_id = ids.pop(0)
        prev_id = end_id = start_id
        ids.append(-1)
        for id in ids:
            if id == prev_id + 1:
                end_id = id
            else:
                session.add(RemoveChunk(start_id, end_id, self.id))
                start_id = end_id = id
            prev_id = id

        session.commit()
