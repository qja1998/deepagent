"""External Tools Integration."""
import subprocess
from typing import Dict, Any, List, Optional
from pathlib import Path


class ExternalToolsMCP:
    """외부 도구 통합 MCP"""
    
    @staticmethod
    async def run_tests(test_path: str) -> Dict[str, Any]:
        """
        테스트 실행
        
        Args:
            test_path: 테스트 경로
            
        Returns:
            테스트 결과 딕셔너리
        """
        try:
            result = subprocess.run(
                ["pytest", test_path],
                capture_output=True,
                text=True,
                timeout=60
            )
            
            return {
                "success": result.returncode == 0,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "returncode": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {
                "success": False,
                "error": "Test execution timeout"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    async def run_linter(file_path: str) -> List[Dict[str, Any]]:
        """
        Linter 실행
        
        Args:
            file_path: 파일 경로
            
        Returns:
            린터 결과 리스트
        """
        issues = []
        
        # pylint 실행 (Python 파일인 경우)
        if Path(file_path).suffix == ".py":
            try:
                result = subprocess.run(
                    ["pylint", file_path],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                # 결과 파싱 (간단한 구현)
                for line in result.stdout.split('\n'):
                    if ':' in line and ('error' in line.lower() or 'warning' in line.lower()):
                        issues.append({
                            "type": "lint",
                            "message": line,
                            "file": file_path
                        })
            except Exception:
                pass
        
        return issues
    
    @staticmethod
    async def git_status() -> Dict[str, Any]:
        """
        Git 상태 확인
        
        Returns:
            Git 상태 딕셔너리
        """
        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True,
                text=True
            )
            
            modified = []
            untracked = []
            
            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                code = line[:2]
                file_path = line[3:]
                
                if code.startswith('M'):
                    modified.append(file_path)
                elif code.startswith('??'):
                    untracked.append(file_path)
            
            return {
                "success": True,
                "modified": modified,
                "untracked": untracked
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }
    
    @staticmethod
    async def git_diff(file_path: Optional[str] = None) -> str:
        """
        Git diff 확인
        
        Args:
            file_path: 파일 경로 (선택사항)
            
        Returns:
            diff 문자열
        """
        try:
            cmd = ["git", "diff"]
            if file_path:
                cmd.append(file_path)
            
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            return result.stdout
        except Exception as e:
            return f"Error: {str(e)}"

