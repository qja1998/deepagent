"""Main entry point for Cursor Clone Agent."""
import asyncio
import sys
from pathlib import Path

from src.orchestrator import CursorAgentOrchestrator


async def main():
    """메인 함수"""
    if len(sys.argv) < 2:
        print("Usage: python -m src.main <user_input>")
        print("Example: python -m src.main 'Implement a new feature'")
        sys.exit(1)
    
    user_input = sys.argv[1]
    
    # Orchestrator 초기화 (Agent Mode만 지원)
    orchestrator = CursorAgentOrchestrator(project_root=".")
    
    # 요청 처리
    result = await orchestrator.invoke(user_input)
    
    print("=" * 60)
    print("📤 최종 결과:")
    print("=" * 60)
    print(result.get("response", ""))
    print("\n" + "=" * 60)
    print("📊 실행 정보:")
    print("=" * 60)
    print(f"반복 횟수: {result.get('iterations', 0)}")
    print(f"최선의 품질 점수: {result.get('best_quality', 0.0):.2f}")
    print(f"작업 이력: {len(result.get('history', []))}개")
    if result.get("errors"):
        print(f"에러: {len(result['errors'])}개")


if __name__ == "__main__":
    asyncio.run(main())

