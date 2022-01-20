from sqlalchemy import Integer, Enum
from sqlalchemy.schema import Column
from mypkg.db_settings import Base
import enum

class ChunkType(enum.Enum):
    ADD = enum.auto()
    REMOVE = enum.auto()

class ChunkRelation(Base):
    __tablename__ = 'chunk_relation'
    id = Column(Integer, primary_key=True)
    parent_chunk_id = Column(Integer)
    parent_chunk_type = Column(Enum(ChunkType))
    child_chunk_id = Column(Integer)
    child_chunk_type = Column(Enum(ChunkType))
    
    def __init__(self, parent_chunk_id, parent_chunk_type, child_chunk_id, child_chunk_type):
        self.parent_chunk_id = parent_chunk_id
        self.parent_chunk_type = parent_chunk_type
        self.child_chunk_id = child_chunk_id
        self.child_chunk_type = child_chunk_type
