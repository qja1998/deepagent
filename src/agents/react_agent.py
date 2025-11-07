"""ReAct Agent with Self-Reflection Loop for Best Result Maintenance."""
from typing import Dict, Any, Optional
import os
from langchain_anthropic import ChatAnthropic
from langchain.agents import create_react_agent, AgentExecutor
from langchain.prompts import PromptTemplate
from langchain_core.tools import Tool

from ..mcp.client import CursorMCPClient
from ..context.context_manager import ContextManager
from ..state.graph_state import AgentState


class ReActAgent:
    """ReAct 패턴 기반 자율 에이전트 - Reflection을 통한 자기반복 및 최선의 결과 유지"""
    
    def __init__(
        self,
        mcp_client: Optional[CursorMCPClient] = None,
        context_manager: Optional[ContextManager] = None,
        model: str = "claude-sonnet-4-5",
        max_iterations: int = 5
    ):
        """
        ReAct Agent 초기화
        
        Args:
            mcp_client: MCP 클라이언트 인스턴스
            context_manager: 컨텍스트 매니저 인스턴스
            model: 사용할 LLM 모델 (기본값: claude-sonnet-4-5)
            max_iterations: 최대 반복 횟수
        """
        api_key = os.getenv("ANTHROPIC_API_KEY")
        self.llm = ChatAnthropic(
            model=model,
            temperature=0,
            anthropic_api_key=api_key,
            max_tokens=20_000
        )
        self.mcp_client = mcp_client or CursorMCPClient()
        self.context_manager = context_manager or ContextManager()
        self.max_iterations = max_iterations
        self.tools = []
        self._load_tools()
    
    def _load_tools(self):
        """MCP 도구를 LangChain 도구로 변환"""
        from ..mcp.tools.file_system import FileSystemTools
        import asyncio
        from typing import List
        
        # Async 함수를 동기 함수로 래핑
        def read_file_sync(path: str) -> str:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            return loop.run_until_complete(FileSystemTools.read_file(path))
        
        def write_file_sync(path: str, content: str) -> bool:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            return loop.run_until_complete(FileSystemTools.write_file(path, content))
        
        def list_files_sync(directory: str, pattern: str = "*") -> List[str]:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            return loop.run_until_complete(FileSystemTools.list_files(directory, pattern))
        
        self.tools = [
            Tool(
                name="read_file",
                description="Read content from a file. Input should be a file path string.",
                func=read_file_sync
            ),
            Tool(
                name="write_file",
                description="Write content to a file. Input should be a dictionary with 'path' and 'content' keys, or two separate arguments: path and content.",
                func=lambda path, content: write_file_sync(path, content)
            ),
            Tool(
                name="list_files",
                description="List files in a directory. Input should be a directory path string, optionally with a glob pattern as second argument.",
                func=list_files_sync
            ),
        ]
    
    def _build_react_prompt(self) -> PromptTemplate:
        """ReAct 프롬프트 템플릿 생성"""
        return PromptTemplate.from_template("""You are an autonomous AI coding agent that uses ReAct (Reasoning + Acting) pattern.

Your goal: {user_input}

Available tools:
{tools}

Previous attempts and results:
{history}

Current iteration: {iteration_count}/{max_iterations}

Best result so far (quality: {best_quality}):
{best_result}

Instructions:
1. Think step by step about what needs to be done
2. Use available tools to accomplish the task
3. Reflect on the results and improve if needed
4. Continue until you achieve the best possible result

{agent_scratchpad}
""")
    
    async def reasoning_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Reasoning 노드: 현재 상황을 분석하고 다음 행동을 계획
        
        Args:
            state: 현재 에이전트 상태
            
        Returns:
            상태 업데이트
        """
        # 프롬프트 구성
        prompt = f"""Analyze the current situation and plan the next action.

User Request: {state['user_input']}
Current Context: {state.get('context', {})}
Previous Attempts: {len(state.get('history', []))}
Best Result Quality: {state.get('best_quality', 0)}

Available Tools: {[tool.name for tool in self.tools]}

1. Analyze what needs to be done
2. Select the best tool to use
3. Plan the specific action

Respond in format:
PLAN: <your plan>
TOOL: <tool name>
INPUT: <tool input as JSON>
"""
        
        # LLM 호출
        response = self.llm.invoke(prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # 응답 파싱
        plan = self._extract_plan(response_text)
        selected_tool = self._extract_tool(response_text)
        tool_input = self._extract_tool_input(response_text)
        
        return {
            "plan": plan,
            "selected_tool": selected_tool,
            "tool_input": tool_input,
            "iteration_count": state.get("iteration_count", 0) + 1
        }
    
    async def acting_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Acting 노드: 선택된 도구를 실행하고 결과를 관찰
        
        Args:
            state: 현재 에이전트 상태
            
        Returns:
            상태 업데이트
        """
        selected_tool = state.get("selected_tool")
        tool_input = state.get("tool_input", {})
        
        tool_output = ""
        error = None
        
        try:
            # 도구 찾기 및 실행
            tool = next((t for t in self.tools if t.name == selected_tool), None)
            if tool:
                if isinstance(tool_input, dict):
                    # 도구에 따라 입력 처리
                    if selected_tool == "read_file":
                        tool_output = tool.func(tool_input.get("path", ""))
                    elif selected_tool == "write_file":
                        tool_output = str(tool.func(
                            tool_input.get("path", ""),
                            tool_input.get("content", "")
                        ))
                    elif selected_tool == "list_files":
                        tool_output = str(tool.func(
                            tool_input.get("directory", ""),
                            tool_input.get("pattern", "*")
                        ))
                    else:
                        tool_output = str(tool.func(**tool_input))
                else:
                    tool_output = str(tool.func(tool_input))
            else:
                error = f"Tool '{selected_tool}' not found"
                tool_output = error
        except Exception as e:
            error = str(e)
            tool_output = f"Error: {error}"
        
        # 이력에 추가
        history = state.get("history", [])
        history.append({
            "iteration": state.get("iteration_count", 0),
            "tool": selected_tool,
            "input": tool_input,
            "output": tool_output,
            "error": error
        })
        
        return {
            "tool_output": tool_output,
            "history": history,
            "errors": state.get("errors", []) + ([error] if error else [])
        }
    
    async def reflection_node(self, state: AgentState) -> Dict[str, Any]:
        """
        Reflection 노드: 실행 결과를 평가하고 최선의 결과를 유지하며 다음 단계 결정
        
        Args:
            state: 현재 에이전트 상태
            
        Returns:
            상태 업데이트 (next_action 포함)
        """
        # 결과 품질 평가
        current_quality = self._evaluate_quality(state)
        
        # 최선의 결과 업데이트
        best_result = state.get("best_result")
        best_quality = state.get("best_quality", 0.0)
        improved = current_quality > best_quality
        
        if improved or best_result is None:
            best_result = state.get("tool_output", "")
            best_quality = current_quality
        
        # Reflection 프롬프트
        reflection_prompt = f"""Evaluate the execution result and decide the next step.

User Request: {state['user_input']}
Current Plan: {state.get('plan', '')}
Tool Used: {state.get('selected_tool', '')}
Tool Output: {state.get('tool_output', '')}
Current Quality Score: {current_quality}
Previous Best Quality: {best_quality}
Iteration: {state.get('iteration_count', 0)}/{state.get('max_iterations', self.max_iterations)}

Previous Best Result:
{best_result if best_result else 'None'}

1. Evaluate if the goal is achieved
2. Compare current result with previous best
3. Determine if improvement is needed
4. Decide next action: 'continue' to improve or 'complete' if satisfied

Respond in format:
EVALUATION: <your evaluation>
IMPROVED: <yes/no>
NEXT_ACTION: <continue/complete>
REASONING: <your reasoning>
"""
        
        # LLM 호출
        response = self.llm.invoke(reflection_prompt)
        response_text = response.content if hasattr(response, 'content') else str(response)
        
        # 응답 파싱
        reflection = self._extract_evaluation(response_text)
        next_action = self._extract_next_action(response_text)
        
        # 종료 조건 확인
        iteration_count = state.get("iteration_count", 0)
        max_iterations = state.get("max_iterations", self.max_iterations)
        
        if iteration_count >= max_iterations:
            next_action = "complete"
        
        if not improved and iteration_count > 1:
            # 개선이 없고 이미 한 번 이상 시도했다면 종료 고려
            if "complete" in response_text.lower() or "satisfied" in response_text.lower():
                next_action = "complete"
        
        # 최종 출력 설정
        final_output = best_result if next_action == "complete" else None
        
        return {
            "reflection": reflection,
            "current_quality": current_quality,
            "best_result": best_result,
            "best_quality": best_quality,
            "improved": improved,
            "next_action": next_action,
            "should_continue": next_action == "continue",
            "final_output": final_output
        }
    
    def _evaluate_quality(self, state: AgentState) -> float:
        """
        결과 품질 평가 (0-100 점수)
        
        Args:
            state: 현재 에이전트 상태
            
        Returns:
            품질 점수 (0.0 - 100.0)
        """
        tool_output = state.get("tool_output", "")
        user_input = state.get("user_input", "")
        
        if not tool_output:
            return 0.0
        
        # 간단한 품질 평가 (향후 LLM 기반 평가로 확장 가능)
        # 1. 에러가 없으면 기본 점수
        if "Error:" in tool_output or "error" in tool_output.lower():
            return 20.0
        
        # 2. 출력 길이 기반 점수
        length_score = min(len(tool_output) / 100, 1.0) * 30
        
        # 3. 사용자 요청과의 관련성 (간단한 키워드 매칭)
        relevance_score = 0.0
        user_keywords = user_input.lower().split()
        output_lower = tool_output.lower()
        matched_keywords = sum(1 for kw in user_keywords if kw in output_lower)
        if user_keywords:
            relevance_score = (matched_keywords / len(user_keywords)) * 50
        
        total_score = length_score + relevance_score + 20  # 기본 점수
        
        return min(total_score, 100.0)
    
    def _extract_plan(self, text: str) -> str:
        """프롬프트 응답에서 계획 추출"""
        if "PLAN:" in text:
            return text.split("PLAN:")[1].split("\n")[0].strip()
        return text[:200]  # 기본값
    
    def _extract_tool(self, text: str) -> str:
        """프롬프트 응답에서 도구 이름 추출"""
        if "TOOL:" in text:
            tool_name = text.split("TOOL:")[1].split("\n")[0].strip()
            # 사용 가능한 도구인지 확인
            if any(t.name == tool_name for t in self.tools):
                return tool_name
        # 기본값: 첫 번째 도구
        return self.tools[0].name if self.tools else ""
    
    def _extract_tool_input(self, text: str) -> Dict[str, Any]:
        """프롬프트 응답에서 도구 입력 추출"""
        if "INPUT:" in text:
            import json
            try:
                input_text = text.split("INPUT:")[1].strip()
                return json.loads(input_text)
            except:
                return {"input": input_text}
        return {}
    
    def _extract_evaluation(self, text: str) -> str:
        """프롬프트 응답에서 평가 추출"""
        if "EVALUATION:" in text:
            return text.split("EVALUATION:")[1].split("\n")[0].strip()
        return text[:300]
    
    def _extract_next_action(self, text: str) -> str:
        """프롬프트 응답에서 다음 액션 추출"""
        if "NEXT_ACTION:" in text:
            action = text.split("NEXT_ACTION:")[1].split("\n")[0].strip().lower()
            if "complete" in action:
                return "complete"
        return "continue"

