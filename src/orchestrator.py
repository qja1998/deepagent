"""Orchestrator for Cursor Clone Agent - Agent Mode Only with ReAct Pattern."""
from typing import Dict, Any, Optional
from langgraph.graph import StateGraph, END

from .mcp.client import CursorMCPClient
from .context.context_manager import ContextManager
from .agents.react_agent import ReActAgent
from .state.graph_state import AgentState


class CursorAgentOrchestrator:
    """
    메인 에이전트 컨트롤러
    - Agent Mode만 지원 (ReAct 패턴 기반)
    - Reflection을 통한 자기반복
    - 최선의 결과물 유지
    """
    
    def __init__(self, project_root: Optional[str] = None, max_iterations: int = 5):
        """
        Orchestrator 초기화
        
        Args:
            project_root: 프로젝트 루트 디렉토리
            max_iterations: 최대 반복 횟수
        """
        self.context_manager = ContextManager(project_root=project_root)
        self.mcp_client = CursorMCPClient()
        self.react_agent = ReActAgent(
            mcp_client=self.mcp_client,
            context_manager=self.context_manager,
            max_iterations=max_iterations
        )
        self.graph = self._build_graph()
    
    def _build_graph(self) -> StateGraph:
        """LangGraph 워크플로우 생성 - Agent Mode만 지원"""
        workflow = StateGraph(AgentState)
        
        # 노드 추가
        workflow.add_node("collect_context", self._collect_context_node)
        workflow.add_node("reasoning", self._reasoning_node)
        workflow.add_node("acting", self._acting_node)
        workflow.add_node("reflection", self._reflection_node)
        
        # 엣지 추가
        workflow.set_entry_point("collect_context")
        workflow.add_edge("collect_context", "reasoning")
        workflow.add_edge("reasoning", "acting")
        workflow.add_edge("acting", "reflection")
        
        # Reflection에서 조건부 전이 (자기반복 또는 종료)
        workflow.add_conditional_edges(
            "reflection",
            self._should_continue,
            {
                "reasoning": "reasoning",  # 자기반복
                "end": END  # 종료
            }
        )
        
        return workflow.compile()
    
    def _collect_context_node(self, state: AgentState) -> Dict[str, Any]:
        """컨텍스트 수집 노드"""
        context = self.context_manager.collect_context()
        return {"context": context}
    
    async def _reasoning_node(self, state: AgentState) -> Dict[str, Any]:
        """Reasoning 노드"""
        return await self.react_agent.reasoning_node(state)
    
    async def _acting_node(self, state: AgentState) -> Dict[str, Any]:
        """Acting 노드"""
        return await self.react_agent.acting_node(state)
    
    async def _reflection_node(self, state: AgentState) -> Dict[str, Any]:
        """Reflection 노드 - 최선의 결과 유지 및 자기반복 결정"""
        return await self.react_agent.reflection_node(state)
    
    def _should_continue(self, state: AgentState) -> str:
        """
        다음 단계 결정
        
        Returns:
            "reasoning" (자기반복) 또는 "end" (종료)
        """
        next_action = state.get("next_action", "end")
        should_continue = state.get("should_continue", False)
        
        if next_action == "continue" and should_continue:
            return "reasoning"
        else:
            return "end"
    
    async def invoke(self, user_input: str) -> Dict[str, Any]:
        """
        그래프 실행
        
        Args:
            user_input: 사용자 입력
            
        Returns:
            실행 결과 (최선의 결과 포함)
        """
        initial_state: AgentState = {
            "user_input": user_input,
            "context": {},
            "messages": [],
            "plan": None,
            "selected_tool": None,
            "tool_input": None,
            "tool_output": None,
            "reflection": None,
            "iteration_count": 0,
            "max_iterations": self.react_agent.max_iterations,
            "best_result": None,
            "best_quality": 0.0,
            "current_quality": 0.0,
            "improved": False,
            "history": [],
            "next_action": "continue",
            "should_continue": True,
            "final_output": None,
            "errors": []
        }
        
        result = await self.graph.ainvoke(initial_state)
        
        # 최선의 결과 반환
        return {
            "response": result.get("final_output") or result.get("best_result") or result.get("tool_output", ""),
            "best_result": result.get("best_result"),
            "best_quality": result.get("best_quality", 0.0),
            "iterations": result.get("iteration_count", 0),
            "history": result.get("history", []),
            "reflection": result.get("reflection"),
            "errors": result.get("errors", [])
        }
    
    async def route_request(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        요청 처리 (Agent Mode만 지원)
        
        Args:
            user_input: 사용자 입력
            context: 추가 컨텍스트 (선택사항)
            
        Returns:
            에이전트 응답
        """
        return await self.invoke(user_input)

