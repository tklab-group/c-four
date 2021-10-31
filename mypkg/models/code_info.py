from sqlalchemy import Integer, Text, ForeignKey
from sqlalchemy.schema import Column
from mypkg.db_settings import Base

class CodeInfo(Base):
    __tablename__ = 'code_info'
    id = Column(Integer, primary_key=True)
    line_id = Column(Integer, nullable=False)
    code = Column(Text)
    context_id = Column(Integer, ForeignKey('context.id'))
    
    def __init__(self, line_id, code, context_id):
        self.line_id = line_id
        self.code = code
        self.context_id = context_id
