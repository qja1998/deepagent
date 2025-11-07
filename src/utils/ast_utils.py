"""AST utility functions."""
import ast
from typing import List, Dict, Any, Optional
from pathlib import Path


class ASTUtils:
    """AST 관련 유틸리티 함수"""
    
    @staticmethod
    def extract_functions(file_path: Path) -> List[Dict[str, Any]]:
        """
        파일에서 함수 추출
        
        Args:
            file_path: 파일 경로
            
        Returns:
            함수 정보 리스트
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            
            functions = []
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append({
                        "name": node.name,
                        "lineno": node.lineno,
                        "end_lineno": getattr(node, 'end_lineno', node.lineno),
                        "args": [arg.arg for arg in node.args.args],
                        "decorators": [ast.unparse(d) for d in node.decorator_list] if hasattr(ast, 'unparse') else []
                    })
            
            return functions
        except Exception:
            return []
    
    @staticmethod
    def extract_classes(file_path: Path) -> List[Dict[str, Any]]:
        """
        파일에서 클래스 추출
        
        Args:
            file_path: 파일 경로
            
        Returns:
            클래스 정보 리스트
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            
            classes = []
            for node in ast.walk(tree):
                if isinstance(node, ast.ClassDef):
                    methods = [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
                    classes.append({
                        "name": node.name,
                        "lineno": node.lineno,
                        "end_lineno": getattr(node, 'end_lineno', node.lineno),
                        "methods": methods,
                        "bases": [ast.unparse(b) for b in node.bases] if hasattr(ast, 'unparse') else []
                    })
            
            return classes
        except Exception:
            return []
    
    @staticmethod
    def find_dependencies(file_path: Path) -> List[str]:
        """
        파일의 import 의존성 추출
        
        Args:
            file_path: 파일 경로
            
        Returns:
            의존성 모듈 리스트
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            
            dependencies = []
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        dependencies.append(alias.name)
                elif isinstance(node, ast.ImportFrom):
                    if node.module:
                        dependencies.append(node.module)
            
            return dependencies
        except Exception:
            return []

