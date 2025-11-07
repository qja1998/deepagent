"""Diff Generation and Preview utilities."""
from typing import List, Dict, Any, Tuple
import difflib
from pathlib import Path


class DiffGenerator:
    """코드 변경사항 diff 생성 및 미리보기"""
    
    @staticmethod
    def generate_unified_diff(
        old_content: str,
        new_content: str,
        file_path: str
    ) -> str:
        """
        Unified diff 형식 생성
        
        Args:
            old_content: 기존 내용
            new_content: 새로운 내용
            file_path: 파일 경로
            
        Returns:
            Unified diff 문자열
        """
        old_lines = old_content.splitlines(keepends=True)
        new_lines = new_content.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            old_lines,
            new_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            lineterm=''
        )
        
        return ''.join(diff)
    
    @staticmethod
    def detect_conflicts(
        original: str,
        modified: str,
        current: str
    ) -> List[Dict[str, Any]]:
        """
        충돌 감지
        
        Args:
            original: 원본 내용
            modified: 수정된 내용
            current: 현재 파일 내용
            
        Returns:
            충돌 리스트
        """
        conflicts = []
        
        # 간단한 충돌 감지 로직
        if modified != current and original != current:
            conflicts.append({
                "type": "modification_conflict",
                "message": "File has been modified since original version",
                "original": original[:100],
                "modified": modified[:100],
                "current": current[:100]
            })
        
        return conflicts
    
    @staticmethod
    def generate_summary(diff: str) -> str:
        """
        변경사항 요약 생성
        
        Args:
            diff: diff 문자열
            
        Returns:
            요약 문자열
        """
        lines = diff.split('\n')
        added = sum(1 for line in lines if line.startswith('+') and not line.startswith('+++'))
        removed = sum(1 for line in lines if line.startswith('-') and not line.startswith('---'))
        
        return f"Changes: {added} lines added, {removed} lines removed"

