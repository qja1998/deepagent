"""Example usage of Chat Agent."""
import asyncio
from src.agents.chat_agent import ChatAgent
from src.context.context_manager import ContextManager


async def main():
    """기본 Chat Agent 사용 예제"""
    # Context Manager 초기화
    context_manager = ContextManager(project_root=".")
    context_manager.set_current_file("src/agents/chat_agent.py")
    context_manager.set_selection(start_line=1, end_line=10)
    
    # Chat Agent 초기화
    agent = ChatAgent(context_manager=context_manager)
    
    # 질문 처리
    result = await agent.process("이 파일의 주요 기능을 설명해주세요.")
    
    print("Response:", result["response"])
    print("\nContext Used:", result["context_used"])


if __name__ == "__main__":
    asyncio.run(main())

