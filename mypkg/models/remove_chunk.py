from sqlalchemy import Integer, ForeignKey
from sqlalchemy.schema import Column
from mypkg.db_settings import Base

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
