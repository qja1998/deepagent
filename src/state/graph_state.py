"""State definitions for Cursor Clone Agent."""
from typing import Annotated, Dict, Any, List, Optional, TypedDict
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages


class AgentState(TypedDict):
    """에이전트 상태 - ReAct 패턴 기반 자율 에이전트"""
    user_input: str
    context: Dict[str, Any]
    messages: Annotated[List[BaseMessage], add_messages]
    
    # ReAct 패턴 상태
    plan: Optional[str]  # 현재 계획
    selected_tool: Optional[str]  # 선택된 도구
    tool_input: Optional[Dict[str, Any]]  # 도구 입력
    tool_output: Optional[str]  # 도구 출력
    reflection: Optional[str]  # 반성 및 평가
    
    # 자기반복 및 최선의 결과 유지
    iteration_count: int  # 현재 반복 횟수
    max_iterations: int  # 최대 반복 횟수
    best_result: Optional[str]  # 지금까지의 최선의 결과
    best_quality: float  # 최선의 결과의 품질 점수
    current_quality: float  # 현재 결과의 품질 점수
    improved: bool  # 이번 반복에서 개선되었는지 여부
    
    # 작업 이력
    history: List[Dict[str, Any]]  # 작업 이력
    
    # 제어 플래그
    next_action: str  # 다음 액션: "reasoning", "end"
    should_continue: bool  # 계속 진행 여부
    
    # 최종 결과
    final_output: Optional[str]  # 최종 출력 (최선의 결과)
    errors: List[str]  # 에러 목록

