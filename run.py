#!/usr/bin/env python3
"""Quick start example for Cursor Clone Agent - Agent Mode Only."""
import asyncio
import sys
from pathlib import Path
from dotenv import load_dotenv

# 환경 변수 로드
load_dotenv()

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from src.orchestrator import CursorAgentOrchestrator


async def main():
    """간단한 실행 예제"""
    print("🚀 Cursor Clone Agent 시작... (Agent Mode - ReAct Pattern)\n")
    
    # 사용자 입력 받기
    if len(sys.argv) > 1:
        user_input = " ".join(sys.argv[1:])
    else:
        user_input = "이 프로젝트의 구조를 설명해줘"
    
    print(f"📝 요청: {user_input}\n")
    
    try:
        # Orchestrator 초기화 (Agent Mode만 지원)
        orchestrator = CursorAgentOrchestrator(project_root=str(project_root))
        
        # 요청 처리
        print("🔄 처리 중... (ReAct 패턴으로 자기반복 수행)\n")
        result = await orchestrator.invoke(user_input)
        
        # 결과 출력
        print("=" * 60)
        print("📤 최종 결과 (최선의 결과):")
        print("=" * 60)
        print(result.get("response", "응답이 없습니다."))
        print("=" * 60)
        
        print("\n📊 실행 정보:")
        print(f"  반복 횟수: {result.get('iterations', 0)}")
        print(f"  최선의 품질 점수: {result.get('best_quality', 0.0):.2f}")
        print(f"  작업 이력: {len(result.get('history', []))}개")
        
        if result.get("reflection"):
            print(f"\n💭 Reflection:")
            print(f"  {result['reflection'][:200]}...")
        
        if result.get("errors"):
            print(f"\n⚠️  에러: {len(result['errors'])}개")
            for error in result["errors"][:3]:
                print(f"  - {error}")
        
    except Exception as e:
        print(f"❌ 오류 발생: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
