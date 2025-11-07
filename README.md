# Cursor Clone Agent

LangChain DeepAgent와 MCP를 기반으로 한 Cursor IDE 클론 에이전트

## 프로젝트 구조

```
deepagent/
├── src/
│   ├── mcp/              # MCP 도구 및 서버
│   │   ├── tools/        # MCP 도구 구현
│   │   └── servers/      # MCP 서버 구현
│   ├── agents/           # 에이전트 구현
│   ├── context/          # 컨텍스트 관리
│   ├── indexing/         # 코드 인덱싱
│   ├── state/            # 상태 관리
│   └── utils/            # 유틸리티
├── tests/                # 테스트
├── examples/             # 예제 코드
└── configs/              # 설정 파일
```

## 설치

### 1. 의존성 설치

```bash
cd deepagent
uv sync
# 또는
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 API 키를 설정합니다:

```bash
# .env 파일 생성
cat > .env << EOF
ANTHROPIC_API_KEY=your_anthropic_api_key_here
# OpenAI API 키는 선택사항 (기본 모델은 Claude 사용)
OPENAI_API_KEY=your_openai_api_key_here
EOF
```

## 실행 방법

### 방법 1: 간단한 실행 스크립트 (추천)

```bash
# 기본 질문으로 실행
uv run python run.py

# 질문과 함께 실행
uv run python run.py "이 프로젝트의 구조를 설명해줘"
```

### 방법 2: 메인 모듈 실행 (CLI)

```bash
# Chat 모드로 실행
uv run python -m src.main "코드를 설명해줘" chat

# Composer 모드로 실행 (멀티파일 편집)
uv run python -m src.main "모든 파일에 에러 핸들링 추가" composer

# Agent 모드로 실행 (자율 실행)
uv run python -m src.main "새로운 기능 구현" agent
```

### 방법 3: Python 스크립트로 실행

```python
# examples/basic_chat.py 참고
import asyncio
from src.orchestrator import CursorAgentOrchestrator

async def main():
    orchestrator = CursorAgentOrchestrator(project_root=".")
    result = await orchestrator.route_request(
        "이 함수가 무엇을 하는지 설명해줘",
        mode="chat"
    )
    print(result["response"])

asyncio.run(main())
```

### 방법 4: LangGraph Studio에서 실행

```bash
# LangGraph Studio 시작
langgraph dev

# 브라우저에서 http://localhost:8123 접속
# studio_graph.py의 그래프를 시각화하고 테스트할 수 있습니다
```

### 방법 5: 개별 에이전트 직접 사용

```python
from src.agents.chat_agent import ChatAgent
from src.mcp.client import CursorMCPClient
from src.context.context_manager import ContextManager

# 에이전트 초기화
mcp_client = CursorMCPClient()
context_manager = ContextManager(project_root=".")
chat_agent = ChatAgent(
    mcp_client=mcp_client,
    context_manager=context_manager
)

# 사용
result = await chat_agent.process("코드를 설명해줘")
print(result["response"])
```

## 실행 예제

### 기본 Chat 에이전트 사용

```bash
# 예제 스크립트 실행
uv run python examples/basic_chat.py
```

### LangGraph 워크플로우 실행

```python
from src.orchestrator import CursorAgentOrchestrator

orchestrator = CursorAgentOrchestrator(project_root=".")
result = await orchestrator.invoke(
    user_input="이 프로젝트의 구조를 설명해줘",
    mode="chat"
)
```

## 모드 설명

- **chat**: 기본 대화형 에이전트 (코드 설명, 질문 답변)
- **composer**: 멀티파일 편집 모드 (여러 파일 동시 수정)
- **agent**: 자율 실행 모드 (복잡한 작업 자동 수행)

## 문제 해결

### Import 오류가 발생하는 경우

```bash
# 가상환경 확인
uv run python --version

# 의존성 재설치
uv sync --reinstall
```

### API 키 오류가 발생하는 경우

`.env` 파일이 올바른 위치에 있고, API 키가 올바르게 설정되었는지 확인하세요.

```bash
# .env 파일 확인
cat .env
```
