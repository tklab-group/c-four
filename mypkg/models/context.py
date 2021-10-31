from sqlalchemy import Integer, String, Text, ForeignKey
from sqlalchemy.schema import Column
from sqlalchemy.orm import relationship
from mypkg.db_settings import Base
from models.code_info import CodeInfo
from models.remove_chunk import RemoveChunk
from models.add_chunk import AddChunk

class Context(Base):
    __tablename__ = 'context'
    id = Column(Integer, primary_key=True)
    path = Column(String(255), nullable=False)
    code_infos = relationship("CodeInfo", backref='context')
    remove_chunks = relationship("RemoveChunk", backref='context')
    add_chunks = relationship("AddChunk", backref='context')
    
    def __init__(self, path):
        self.path = path
