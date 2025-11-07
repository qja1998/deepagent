"""Tests for File System Tools."""
import pytest
import tempfile
import os
from pathlib import Path
from src.mcp.tools.file_system import FileSystemTools


@pytest.mark.asyncio
async def test_read_file():
    """파일 읽기 테스트"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        f.write("Hello, World!")
        temp_path = f.name
    
    try:
        content = await FileSystemTools.read_file(temp_path)
        assert content == "Hello, World!"
    finally:
        os.unlink(temp_path)


@pytest.mark.asyncio
async def test_write_file():
    """파일 쓰기 테스트"""
    with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
        temp_path = f.name
    
    try:
        result = await FileSystemTools.write_file(temp_path, "Test content")
        assert result is True
        
        with open(temp_path, 'r') as f:
            assert f.read() == "Test content"
    finally:
        os.unlink(temp_path)


@pytest.mark.asyncio
async def test_list_files():
    """파일 목록 조회 테스트"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # 테스트 파일 생성
        test_files = ["file1.txt", "file2.py", "subdir/file3.txt"]
        for file_path in test_files:
            full_path = Path(temp_dir) / file_path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.write_text("test")
        
        # 파일 목록 조회
        files = await FileSystemTools.list_files(temp_dir, "*", recursive=True)
        assert len(files) >= 3

