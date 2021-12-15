from sqlalchemy import Integer, String
from sqlalchemy.schema import Column
from mypkg.db_settings import Base
from sqlalchemy.orm import relationship
from mypkg.models.remove_chunk import RemoveChunk
from mypkg.models.add_chunk import AddChunk
from mypkg.operate_git import apply_patch, commit_cur_staging

class ChunkSet(Base):
    __tablename__ = 'chunk_set'
    id = Column(Integer, primary_key=True)
    remove_chunks = relationship("RemoveChunk", backref='chunk_set')
    add_chunks = relationship("AddChunk", backref='chunk_set')
    message = Column(String(255), nullable=False)
    
    def __init__(self):
        self.message = ''
        
    def commit_self_chunks(self, repo):
        if not self.add_chunks and not self.remove_chunks:
            return None
        
        for add_chunk in self.add_chunks:
            patch = add_chunk.generate_add_patch()
            apply_patch(repo, patch)
            print(patch)
            add_chunk.reflect_staged_diffs()
            
        for remove_chunk in self.remove_chunks:
            patch = remove_chunk.generate_remove_patch()
            apply_patch(repo, patch)
            print(patch)
            remove_chunk.reflect_staged_diffs()
            
        commit_cur_staging(repo, self.message)
