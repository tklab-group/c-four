from sqlalchemy import Integer, Text, ForeignKey
from sqlalchemy.schema import Column
from mypkg.db_settings import Base

class AddChunk(Base):
    __tablename__ = 'add_chunk'
    id = Column(Integer, primary_key=True)
    start_id = Column(Integer, nullable=False)
    end_id = Column(Integer, nullable=False)
    code = Column(Text)
    context_id = Column(Integer, ForeignKey('context.id'))
    
    def __init__(self, start_id, end_id, code, context_id):
        self.start_id = start_id
        self.end_id = end_id
        self.code = code
        self.context_id = context_id
