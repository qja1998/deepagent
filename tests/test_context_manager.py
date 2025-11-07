"""Tests for Context Manager."""
import pytest
import tempfile
import subprocess
from pathlib import Path
from src.context.context_manager import ContextManager


def test_context_manager_initialization():
    """Context Manager 초기화 테스트"""
    cm = ContextManager()
    assert cm.project_root is not None
    assert cm.current_file is None
    assert cm.selection is None


def test_set_current_file():
    """현재 파일 설정 테스트"""
    cm = ContextManager()
    cm.set_current_file("test.py")
    assert cm.current_file == "test.py"


def test_set_selection():
    """선택 영역 설정 테스트"""
    cm = ContextManager()
    cm.set_selection(start_line=10, end_line=20)
    assert cm.selection["start_line"] == 10
    assert cm.selection["end_line"] == 20


def test_get_project_structure():
    """프로젝트 구조 파악 테스트"""
    with tempfile.TemporaryDirectory() as temp_dir:
        cm = ContextManager(project_root=temp_dir)
        structure = cm.get_project_structure()
        
        assert structure["root"] == temp_dir
        assert "files" in structure
        assert "directories" in structure


def test_collect_context():
    """컨텍스트 수집 테스트"""
    with tempfile.TemporaryDirectory() as temp_dir:
        cm = ContextManager(project_root=temp_dir)
        cm.set_current_file("test.py")
        cm.set_selection(start_line=1, end_line=5)
        
        context = cm.collect_context()
        
        assert context["current_file"] == "test.py"
        assert context["selection"] is not None
        assert context["project_root"] == temp_dir

