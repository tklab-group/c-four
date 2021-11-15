from sqlalchemy import Integer, String
from sqlalchemy.schema import Column
from mypkg.db_settings import Base
from sqlalchemy.orm import relationship
from mypkg.models.remove_chunk import RemoveChunk
from mypkg.models.add_chunk import AddChunk

class ChunkSet(Base):
    __tablename__ = 'chunk_set'
    id = Column(Integer, primary_key=True)
    remove_chunks = relationship("RemoveChunk", backref='chunk_set')
    add_chunks = relationship("AddChunk", backref='chunk_set')
    message = Column(String(255), nullable=False)
    
    def __init__(self):
        self.message = ''
