"""Context Manager for collecting project context."""
from typing import Dict, Any, Optional, List
from pathlib import Path
import subprocess
import json


class ContextManager:
    """프로젝트 컨텍스트 수집 및 관리"""
    
    def __init__(self, project_root: Optional[str] = None):
        """
        Context Manager 초기화
        
        Args:
            project_root: 프로젝트 루트 디렉토리 경로
        """
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.current_file: Optional[str] = None
        self.selection: Optional[Dict[str, int]] = None
        self.open_files: List[str] = []
    
    def set_current_file(self, file_path: str):
        """현재 편집 중인 파일 설정"""
        self.current_file = file_path
    
    def set_selection(
        self,
        start_line: int,
        end_line: int,
        start_col: int = 0,
        end_col: int = 0
    ):
        """선택 영역 설정"""
        self.selection = {
            "start_line": start_line,
            "end_line": end_line,
            "start_col": start_col,
            "end_col": end_col
        }
    
    def add_open_file(self, file_path: str):
        """열린 파일 목록에 추가"""
        if file_path not in self.open_files:
            self.open_files.append(file_path)
    
    def get_project_structure(self, max_depth: int = 3) -> Dict[str, Any]:
        """
        프로젝트 구조 파악
        
        Args:
            max_depth: 최대 탐색 깊이
            
        Returns:
            프로젝트 구조 딕셔너리
        """
        structure = {
            "root": str(self.project_root),
            "files": [],
            "directories": []
        }
        
        def traverse(path: Path, depth: int = 0):
            if depth > max_depth:
                return
            
            if path.is_file():
                structure["files"].append({
                    "path": str(path.relative_to(self.project_root)),
                    "size": path.stat().st_size
                })
            elif path.is_dir():
                dir_info = {
                    "path": str(path.relative_to(self.project_root)),
                    "children": []
                }
                structure["directories"].append(dir_info)
                
                try:
                    for child in path.iterdir():
                        if child.name.startswith('.'):
                            continue
                        traverse(child, depth + 1)
                except PermissionError:
                    pass
        
        traverse(self.project_root)
        return structure
    
    def get_git_status(self) -> Dict[str, Any]:
        """
        Git 상태 수집
        
        Returns:
            Git 상태 정보
        """
        status = {
            "branch": None,
            "modified_files": [],
            "untracked_files": [],
            "staged_files": [],
            "has_changes": False
        }
        
        try:
            # 현재 브랜치
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                status["branch"] = result.stdout.strip()
            
            # 변경된 파일
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                for line in result.stdout.strip().split('\n'):
                    if not line:
                        continue
                    code = line[:2]
                    file_path = line[3:]
                    
                    if code.startswith('M'):
                        status["modified_files"].append(file_path)
                    if code.startswith('??'):
                        status["untracked_files"].append(file_path)
                    if code[1] == 'M':
                        status["staged_files"].append(file_path)
                
                status["has_changes"] = len(status["modified_files"]) > 0 or \
                                       len(status["untracked_files"]) > 0
        
        except (subprocess.SubprocessError, FileNotFoundError):
            # Git이 없거나 에러 발생 시 빈 상태 반환
            pass
        
        return status
    
    def collect_context(self, request: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        컨텍스트 수집
        
        Args:
            request: 추가 요청 정보
            
        Returns:
            수집된 컨텍스트 딕셔너리
        """
        context = {
            "current_file": self.current_file,
            "selection": self.selection,
            "open_files": self.open_files.copy(),
            "project_structure": self.get_project_structure(),
            "git_status": self.get_git_status(),
            "project_root": str(self.project_root)
        }
        
        # 현재 파일 내용 추가
        if self.current_file:
            try:
                file_path = Path(self.current_file)
                if file_path.exists() and file_path.is_file():
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        context["current_file_content"] = content
                        
                        # 선택 영역이 있으면 해당 부분만 추출
                        if self.selection:
                            lines = content.split('\n')
                            start = self.selection["start_line"] - 1
                            end = self.selection["end_line"]
                            context["selected_content"] = '\n'.join(lines[start:end])
            except (UnicodeDecodeError, PermissionError):
                context["current_file_content"] = None
        
        return context

