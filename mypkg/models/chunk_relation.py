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
    first_chunk_id = Column(Integer)
    first_chunk_type = Column(Enum(ChunkType))
    second_chunk_id = Column(Integer)
    second_chunk_type = Column(Enum(ChunkType))
    
    def __init__(self, first_chunk_id, first_chunk_type, second_chunk_id, second_chunk_type):
        self.first_chunk_id = first_chunk_id
        self.first_chunk_type = first_chunk_type
        self.second_chunk_id = second_chunk_id
        self.second_chunk_type = second_chunk_type
