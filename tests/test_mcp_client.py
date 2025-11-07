"""Basic tests for MCP Client."""
import pytest
import asyncio
from src.mcp.client import CursorMCPClient


@pytest.mark.asyncio
async def test_mcp_client_initialization():
    """MCP 클라이언트 초기화 테스트"""
    client = CursorMCPClient()
    assert client.servers == {}
    assert client._lock is not None


@pytest.mark.asyncio
async def test_disconnect_all():
    """모든 서버 연결 해제 테스트"""
    client = CursorMCPClient()
    await client.disconnect_all()
    assert len(client.servers) == 0

