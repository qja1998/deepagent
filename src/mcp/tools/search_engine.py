"""Search Engine Tools."""
from typing import List, Dict, Any
from ..indexing.codebase_indexer import CodebaseIndexer


class SearchEngineMCP:
    """검색 엔진 MCP 도구"""
    
    def __init__(self, indexer: Optional[CodebaseIndexer] = None):
        """
        Search Engine 초기화
        
        Args:
            indexer: CodebaseIndexer 인스턴스
        """
        self.indexer = indexer
    
    async def semantic_search(
        self,
        query: str,
        k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        의미 검색
        
        Args:
            query: 검색 쿼리
            k: 반환할 결과 수
            
        Returns:
            검색 결과 리스트
        """
        if not self.indexer:
            return []
        
        results = self.indexer.semantic_search(query, k=k)
        
        return [{
            "content": r.page_content,
            "metadata": r.metadata,
            "score": getattr(r, 'score', 0.0)
        } for r in results]
    
    async def index_codebase(self, project_path: str) -> bool:
        """
        코드베이스 인덱싱
        
        Args:
            project_path: 프로젝트 경로
            
        Returns:
            성공 여부
        """
        if not self.indexer:
            self.indexer = CodebaseIndexer(project_path)
        
        try:
            self.indexer.index_project()
            return True
        except Exception:
            return False

