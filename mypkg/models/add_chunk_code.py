from sqlalchemy import Integer, Text, ForeignKey
from sqlalchemy.schema import Column
from mypkg.db_settings import Base

class AddChunkCode(Base):
    __tablename__ = 'add_chunk_code'
    id = Column(Integer, primary_key=True)
    code = Column(Text)
    add_chunk_id = Column(Integer, ForeignKey('add_chunk.id'))
    
    def __init__(self, code, add_chunk_id):
        self.code = code
        self.add_chunk_id = add_chunk_id
