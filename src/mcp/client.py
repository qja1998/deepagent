"""MCP Client for Cursor Clone Agent."""
from typing import Dict, Any, Optional
import asyncio
from langchain_mcp_adapters.client import (
    ClientSession,
    StdioConnection,
    WebsocketConnection,
    MultiServerMCPClient
)


class CursorMCPClient:
    """MCP 클라이언트 - MCP 서버와의 통신 관리"""
    
    def __init__(self):
        self.servers: Dict[str, ClientSession] = {}
        self._lock = asyncio.Lock()
    
    async def connect_to_server(
        self,
        server_name: str,
        transport_config: Dict[str, Any]
    ) -> ClientSession:
        """
        MCP 서버에 연결
        
        Args:
            server_name: 서버 식별자
            transport_config: 전송 설정 (stdio 또는 websocket)
                - stdio: {"type": "stdio", "command": "cmd", "args": [...]}
                - websocket: {"type": "websocket", "url": "ws://..."}
            
        Returns:
            ClientSession 인스턴스
        """
        async with self._lock:
            if server_name in self.servers:
                return self.servers[server_name]
            
            # 전송 타입에 따라 연결 생성
            transport_type = transport_config.get("type", "stdio")
            
            if transport_type == "stdio":
                connection = StdioConnection(
                    command=transport_config["command"],
                    args=transport_config.get("args", [])
                )
            elif transport_type == "websocket":
                connection = WebsocketConnection(
                    url=transport_config["url"]
                )
            else:
                raise ValueError(f"Unsupported transport type: {transport_type}")
            
            # ClientSession 생성 및 연결
            session = ClientSession(connection=connection)
            await session.__aenter__()
            self.servers[server_name] = session
            return session
    
    async def disconnect_server(self, server_name: str) -> bool:
        """서버 연결 해제"""
        async with self._lock:
            if server_name in self.servers:
                session = self.servers[server_name]
                await session.__aexit__(None, None, None)
                del self.servers[server_name]
                return True
            return False
    
    async def call_tool(
        self,
        server_name: str,
        tool_name: str,
        args: Dict[str, Any]
    ) -> Any:
        """
        MCP 도구 호출
        
        Args:
            server_name: 서버 식별자
            tool_name: 도구 이름
            args: 도구 인자
            
        Returns:
            도구 실행 결과
        """
        if server_name not in self.servers:
            raise ValueError(f"Server {server_name} not connected")
        
        session = self.servers[server_name]
        # ClientSession의 call_tool 메서드 사용
        result = await session.call_tool(tool_name, args)
        return result
    
    async def list_tools(self, server_name: str) -> list:
        """서버에서 제공하는 도구 목록 조회"""
        if server_name not in self.servers:
            raise ValueError(f"Server {server_name} not connected")
        
        session = self.servers[server_name]
        # ClientSession의 list_tools 메서드 사용
        tools = await session.list_tools()
        return tools
    
    async def disconnect_all(self):
        """모든 서버 연결 해제"""
        async with self._lock:
            for server_name in list(self.servers.keys()):
                await self.disconnect_server(server_name)

