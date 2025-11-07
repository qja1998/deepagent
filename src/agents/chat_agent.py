"""Basic Chat Agent implementation."""
from typing import Dict, Any, Optional, List
from langchain_openai import ChatOpenAI
from langchain.agents import create_openai_tools_agent, AgentExecutor
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.tools import Tool

from ..mcp.client import CursorMCPClient
from ..context.context_manager import ContextManager


class ChatAgent:
    """기본 대화형 에이전트"""
    
    def __init__(
        self,
        mcp_client: Optional[CursorMCPClient] = None,
        context_manager: Optional[ContextManager] = None,
        model: str = "gpt-4-turbo-preview"
    ):
        """
        Chat Agent 초기화
        
        Args:
            mcp_client: MCP 클라이언트 인스턴스
            context_manager: 컨텍스트 매니저 인스턴스
            model: 사용할 LLM 모델
        """
        self.llm = ChatOpenAI(model=model, temperature=0)
        self.mcp_client = mcp_client or CursorMCPClient()
        self.context_manager = context_manager or ContextManager()
        self.tools = []
        self.agent_executor: Optional[AgentExecutor] = None
    
    def _load_tools(self):
        """MCP 도구를 LangChain 도구로 변환"""
        # File System 도구 로드
        from ..mcp.tools.file_system import FileSystemTools
        import asyncio
        
        # Async 함수를 동기 함수로 래핑
        def read_file_sync(path: str) -> str:
            """Read content from a file (synchronous wrapper)"""
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            return loop.run_until_complete(FileSystemTools.read_file(path))
        
        def write_file_sync(path: str, content: str) -> bool:
            """Write content to a file (synchronous wrapper)"""
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
            return loop.run_until_complete(FileSystemTools.write_file(path, content))
        
        def list_files_sync(directory: str, pattern: str = "*") -> List[str]:
            """List files in a directory (synchronous wrapper)"""
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
    
    def _build_prompt(self) -> ChatPromptTemplate:
        """프롬프트 템플릿 생성"""
        return ChatPromptTemplate.from_messages([
            ("system", """You are an expert AI coding assistant integrated into an IDE.

Your capabilities:
- Explain code clearly and concisely
- Identify bugs and suggest fixes
- Recommend improvements and best practices
- Answer questions about the codebase

Current Context:
- Project Root: {project_root}
- Current File: {current_file}
- Selection: {selection}

{file_content}

Guidelines:
1. Be concise and specific
2. Reference line numbers when discussing code
3. Provide code examples when suggesting changes
4. Explain your reasoning
"""),
            ("user", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
    
    async def process(
        self,
        user_input: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        사용자 입력 처리
        
        Args:
            user_input: 사용자 입력
            context: 추가 컨텍스트
            
        Returns:
            에이전트 응답
        """
        # 컨텍스트 수집
        if context is None:
            context = self.context_manager.collect_context()
        
        # 도구 로드
        self._load_tools()
        
        # 프롬프트 생성
        prompt = self._build_prompt()
        
        # Agent 생성
        agent = create_openai_tools_agent(
            llm=self.llm,
            tools=self.tools,
            prompt=prompt
        )
        
        # Agent Executor 생성
        self.agent_executor = AgentExecutor(
            agent=agent,
            tools=self.tools,
            verbose=True
        )
        
        # 컨텍스트 포맷팅
        file_content = ""
        if context.get("current_file_content"):
            file_content = f"```\n{context['current_file_content']}\n```"
        
        selection_info = "None"
        if context.get("selection"):
            sel = context["selection"]
            selection_info = f"Lines {sel['start_line']}-{sel['end_line']}"
        
        # 실행
        result = await self.agent_executor.ainvoke({
            "input": user_input,
            "project_root": context.get("project_root", ""),
            "current_file": context.get("current_file", "None"),
            "selection": selection_info,
            "file_content": file_content
        })
        
        return {
            "response": result.get("output", ""),
            "intermediate_steps": result.get("intermediate_steps", []),
            "context_used": context
        }

