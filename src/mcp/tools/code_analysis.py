"""Code Analysis Tools."""
import ast
from typing import List, Dict, Any, Optional
from pathlib import Path


class CodeAnalysisTools:
    """코드 분석 도구"""
    
    @staticmethod
    def parse_ast(file_path: str) -> Dict[str, Any]:
        """
        Python 파일을 AST로 파싱
        
        Args:
            file_path: 파일 경로
            
        Returns:
            파싱 결과 딕셔너리
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                tree = ast.parse(f.read())
            
            functions = []
            classes = []
            
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    functions.append({
                        "name": node.name,
                        "lineno": node.lineno,
                        "end_lineno": getattr(node, 'end_lineno', node.lineno)
                    })
                elif isinstance(node, ast.ClassDef):
                    classes.append({
                        "name": node.name,
                        "lineno": node.lineno,
                        "end_lineno": getattr(node, 'end_lineno', node.lineno)
                    })
            
            return {
                "functions": functions,
                "classes": classes,
                "success": True
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    def analyze_complexity(file_path: str) -> List[Dict[str, Any]]:
        """
        순환 복잡도 분석
        
        Args:
            file_path: 파일 경로
            
        Returns:
            복잡도 분석 결과 리스트
        """
        try:
            from radon.complexity import cc_visit
            
            with open(file_path, 'r', encoding='utf-8') as f:
                results = cc_visit(f.read())
            
            return [{
                "name": r.name,
                "complexity": r.complexity,
                "lineno": r.lineno
            } for r in results]
        except ImportError:
            # radon이 설치되지 않은 경우 기본 구현
            return []
        except Exception:
            return []
    
    @staticmethod
    def detect_issues(file_path: str) -> List[Dict[str, Any]]:
        """
        코드 이슈 감지
        
        Args:
            file_path: 파일 경로
            
        Returns:
            이슈 리스트
        """
        issues = []
        
        # 기본적인 문법 오류 감지
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                ast.parse(f.read())
        except SyntaxError as e:
            issues.append({
                "type": "syntax_error",
                "message": str(e),
                "lineno": e.lineno,
                "offset": e.offset
            })
        
        return issues

