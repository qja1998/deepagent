"""MCP Tools for File System Operations."""
from typing import List, Optional
import os
import glob
from pathlib import Path


class FileSystemTools:
    """파일 시스템 조작을 위한 MCP 도구"""
    
    @staticmethod
    async def read_file(file_path: str) -> str:
        """
        파일 내용 읽기
        
        Args:
            file_path: 읽을 파일 경로
            
        Returns:
            파일 내용 문자열
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        if not path.is_file():
            raise ValueError(f"Path is not a file: {file_path}")
        
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    
    @staticmethod
    async def write_file(file_path: str, content: str) -> bool:
        """
        파일에 내용 쓰기
        
        Args:
            file_path: 쓸 파일 경로
            content: 파일 내용
            
        Returns:
            성공 여부
        """
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    
    @staticmethod
    async def edit_file(
        file_path: str,
        old_content: str,
        new_content: str
    ) -> bool:
        """
        파일 편집 (diff 기반)
        
        Args:
            file_path: 편집할 파일 경로
            old_content: 기존 내용
            new_content: 새로운 내용
            
        Returns:
            성공 여부
        """
        current_content = await FileSystemTools.read_file(file_path)
        
        if current_content != old_content:
            raise ValueError(
                "File content mismatch. File may have been modified."
            )
        
        return await FileSystemTools.write_file(file_path, new_content)
    
    @staticmethod
    async def list_files(
        directory: str,
        pattern: str = "*",
        recursive: bool = False
    ) -> List[str]:
        """
        파일 목록 조회
        
        Args:
            directory: 디렉토리 경로
            pattern: 파일 패턴 (glob 형식)
            recursive: 재귀적 검색 여부
            
        Returns:
            파일 경로 리스트
        """
        path = Path(directory)
        if not path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")
        if not path.is_dir():
            raise ValueError(f"Path is not a directory: {directory}")
        
        if recursive:
            pattern = f"**/{pattern}"
        
        files = glob.glob(str(path / pattern))
        return [str(Path(f).relative_to(path)) for f in files]
    
    @staticmethod
    async def search_files(
        directory: str,
        query: str,
        file_extensions: Optional[List[str]] = None
    ) -> List[str]:
        """
        파일 내용 검색
        
        Args:
            directory: 검색할 디렉토리
            query: 검색 쿼리
            file_extensions: 검색할 파일 확장자 리스트
            
        Returns:
            매칭된 파일 경로 리스트
        """
        results = []
        path = Path(directory)
        
        if not path.exists():
            return results
        
        extensions = file_extensions or ["*"]
        
        for ext in extensions:
            pattern = f"**/*.{ext}" if ext != "*" else "**/*"
            files = path.glob(pattern)
            
            for file_path in files:
                if file_path.is_file():
                    try:
                        content = await FileSystemTools.read_file(str(file_path))
                        if query.lower() in content.lower():
                            results.append(str(file_path))
                    except (UnicodeDecodeError, PermissionError):
                        # 바이너리 파일이나 권한 없는 파일은 건너뛰기
                        continue
        
        return results

