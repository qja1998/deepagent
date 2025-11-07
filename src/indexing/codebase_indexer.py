"""Codebase Indexing System."""
from typing import List, Dict, Any, Optional
from pathlib import Path
import ast
from langchain.embeddings import OpenAIEmbeddings
from langchain.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document


class CodeChunk:
    """코드 청크 데이터 클래스"""
    def __init__(
        self,
        content: str,
        chunk_type: str,
        start_line: int,
        end_line: int,
        file_path: str,
        language: str
    ):
        self.content = content
        self.chunk_type = chunk_type
        self.start_line = start_line
        self.end_line = end_line
        self.file_path = file_path
        self.language = language


class CodebaseIndexer:
    """코드베이스 인덱싱 시스템"""
    
    def __init__(self, project_path: str, persist_directory: str = ".cursor_index"):
        """
        Codebase Indexer 초기화
        
        Args:
            project_path: 프로젝트 루트 경로
            persist_directory: 벡터 스토어 저장 디렉토리
        """
        self.project_path = Path(project_path)
        self.embeddings = OpenAIEmbeddings()
        self.vector_store = Chroma(
            collection_name="codebase",
            embedding_function=self.embeddings,
            persist_directory=str(self.project_path / persist_directory)
        )
    
    def discover_files(self, extensions: Optional[List[str]] = None) -> List[Path]:
        """
        프로젝트 내 파일 발견
        
        Args:
            extensions: 검색할 파일 확장자 리스트
            
        Returns:
            파일 경로 리스트
        """
        if extensions is None:
            extensions = [".py", ".js", ".ts", ".jsx", ".tsx"]
        
        files = []
        for ext in extensions:
            files.extend(self.project_path.rglob(f"*{ext}"))
        
        return files
    
    def parse_ast(self, file_path: Path) -> Optional[ast.AST]:
        """
        Python 파일을 AST로 파싱
        
        Args:
            file_path: 파일 경로
            
        Returns:
            AST 노드 또는 None
        """
        if file_path.suffix != ".py":
            return None
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return ast.parse(f.read(), filename=str(file_path))
        except Exception:
            return None
    
    def chunk_file(self, file_path: Path) -> List[CodeChunk]:
        """
        파일을 의미있는 청크로 분할
        
        Args:
            file_path: 파일 경로
            
        Returns:
            코드 청크 리스트
        """
        chunks = []
        
        # Python 파일인 경우 AST 기반 청킹
        if file_path.suffix == ".py":
            tree = self.parse_ast(file_path)
            if tree:
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                        chunk = CodeChunk(
                            content=ast.get_source_segment(
                                open(file_path).read(), node
                            ) or "",
                            chunk_type=node.__class__.__name__,
                            start_line=node.lineno,
                            end_line=node.end_lineno if hasattr(node, 'end_lineno') else node.lineno,
                            file_path=str(file_path.relative_to(self.project_path)),
                            language="python"
                        )
                        chunks.append(chunk)
        
        return chunks
    
    def index_project(self):
        """프로젝트 전체 인덱싱"""
        files = self.discover_files()
        
        documents = []
        for file_path in files:
            chunks = self.chunk_file(file_path)
            for chunk in chunks:
                documents.append(Document(
                    page_content=chunk.content,
                    metadata={
                        "file_path": chunk.file_path,
                        "chunk_type": chunk.chunk_type,
                        "language": chunk.language,
                        "lines": f"{chunk.start_line}-{chunk.end_line}"
                    }
                ))
        
        if documents:
            self.vector_store.add_documents(documents)
            self.vector_store.persist()
    
    def semantic_search(self, query: str, k: int = 5) -> List[Document]:
        """
        의미 기반 검색
        
        Args:
            query: 검색 쿼리
            k: 반환할 결과 수
            
        Returns:
            검색 결과 문서 리스트
        """
        return self.vector_store.similarity_search(query, k=k)

