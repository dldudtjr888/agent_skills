# Memory Store

3-tier 메모리 시스템을 설계하고 구현하는 가이드.
Cache, Session, Long-term 메모리 계층, Context Assembly, Memory Promotion 전문.

## Core Responsibilities

1. **Tier Design** - 3-tier 메모리 아키텍처 설계
2. **Store Implementation** - 각 계층별 저장소 구현
3. **Context Assembly** - 대화 컨텍스트 조합
4. **Memory Promotion** - 중요 메모리 승격
5. **Adapter Pattern** - 에이전트 통합 어댑터

---

## 3-Tier 메모리 아키텍처

```
┌─────────────────────────────────────────────────────┐
│                    Agent/Handler                     │
│                         │                            │
│                    MemoryAdapter                     │
│                         │                            │
├─────────────────────────────────────────────────────┤
│                   MemoryManager                      │
│         ┌───────────┬───────────┬───────────┐       │
│         │   Cache   │  Session  │ Long-term │       │
│         │  (Redis)  │  (MySQL)  │ (Vector)  │       │
│         │   TTL     │ Messages  │ Embeddings│       │
│         │   Fast    │  Context  │ Semantic  │       │
│         └───────────┴───────────┴───────────┘       │
└─────────────────────────────────────────────────────┘
```

### 계층별 역할

| Tier | 저장소 | TTL | 용도 |
|------|--------|-----|------|
| Cache | Redis/In-memory | 5~60분 | 빈번한 조회, 임시 데이터 |
| Session | MySQL/SQLite | 세션 종료 | 대화 히스토리, 세션 컨텍스트 |
| Long-term | Vector DB | 영구 | 지식, 중요 메모리, 시맨틱 검색 |

---

## 메모리 스키마

### 기본 스키마

```python
from enum import Enum
from typing import TypedDict, Optional, Any
from datetime import datetime

class MemoryType(str, Enum):
    """메모리 유형"""
    CONVERSATION = "conversation"
    KNOWLEDGE = "knowledge"
    TASK = "task"
    PREFERENCE = "preference"

class MemoryPriority(str, Enum):
    """메모리 우선순위"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class MemoryEntry(TypedDict):
    """메모리 엔트리"""
    id: str
    content: str
    memory_type: MemoryType
    priority: MemoryPriority
    user_id: str
    agent_id: Optional[str]
    session_id: Optional[str]
    metadata: dict[str, Any]
    created_at: datetime
    accessed_at: datetime
    access_count: int
    embedding: Optional[list[float]]

class GetContextResult(TypedDict):
    """컨텍스트 조회 결과"""
    memories: list[dict[str, Any]]
    count: int
    sources: dict[str, bool]
    error: Optional[str]
```

---

## Memory Manager 구현

### 핵심 클래스

```python
from abc import ABC, abstractmethod
from typing import Optional, Any

class MemoryStore(ABC):
    """메모리 저장소 추상 클래스"""

    @abstractmethod
    async def save(self, entry: MemoryEntry) -> str:
        """메모리 저장"""
        ...

    @abstractmethod
    async def get(self, memory_id: str) -> Optional[MemoryEntry]:
        """메모리 조회"""
        ...

    @abstractmethod
    async def search(
        self,
        query: str,
        user_id: str,
        limit: int = 10,
    ) -> list[MemoryEntry]:
        """메모리 검색"""
        ...

    @abstractmethod
    async def delete(self, memory_id: str) -> bool:
        """메모리 삭제"""
        ...


class MemoryManager:
    """3-tier 메모리 관리자"""

    def __init__(
        self,
        cache_store: Optional[MemoryStore] = None,
        session_store: Optional[MemoryStore] = None,
        longterm_store: Optional[MemoryStore] = None,
    ):
        self.cache = cache_store
        self.session = session_store
        self.longterm = longterm_store

    async def save_conversation(
        self,
        user_input: str,
        agent_output: str,
        user_id: str,
        session_id: str,
        agent_id: Optional[str] = None,
        priority: MemoryPriority = MemoryPriority.MEDIUM,
        metadata: Optional[dict] = None,
    ) -> str:
        """대화 저장 (Session tier)"""
        entry = MemoryEntry(
            id=generate_id(),
            content=f"User: {user_input}\nAssistant: {agent_output}",
            memory_type=MemoryType.CONVERSATION,
            priority=priority,
            user_id=user_id,
            agent_id=agent_id,
            session_id=session_id,
            metadata=metadata or {},
            created_at=datetime.now(),
            accessed_at=datetime.now(),
            access_count=0,
            embedding=None,
        )

        if self.session:
            return await self.session.save(entry)
        return ""

    async def save_important(
        self,
        content: str,
        user_id: str,
        memory_type: MemoryType = MemoryType.KNOWLEDGE,
        priority: MemoryPriority = MemoryPriority.HIGH,
        metadata: Optional[dict] = None,
    ) -> str:
        """중요 정보 저장 (Long-term tier)"""
        entry = MemoryEntry(
            id=generate_id(),
            content=content,
            memory_type=memory_type,
            priority=priority,
            user_id=user_id,
            agent_id=None,
            session_id=None,
            metadata=metadata or {},
            created_at=datetime.now(),
            accessed_at=datetime.now(),
            access_count=0,
            embedding=None,
        )

        if self.longterm:
            return await self.longterm.save(entry)
        return ""

    async def get_context(
        self,
        query: str,
        user_id: str,
        include_cache: bool = True,
        include_session: bool = True,
        include_longterm: bool = True,
        limit: int = 20,
    ) -> GetContextResult:
        """통합 컨텍스트 조회"""
        memories = []
        sources = {}

        if include_cache and self.cache:
            try:
                cache_results = await self.cache.search(query, user_id, limit=5)
                memories.extend(cache_results)
                sources["cache"] = True
            except Exception:
                sources["cache"] = False

        if include_session and self.session:
            try:
                session_results = await self.session.search(query, user_id, limit=10)
                memories.extend(session_results)
                sources["session"] = True
            except Exception:
                sources["session"] = False

        if include_longterm and self.longterm:
            try:
                longterm_results = await self.longterm.search(query, user_id, limit=5)
                memories.extend(longterm_results)
                sources["longterm"] = True
            except Exception:
                sources["longterm"] = False

        unique_memories = self._deduplicate(memories)
        sorted_memories = self._sort_by_relevance(unique_memories, query)

        return GetContextResult(
            memories=sorted_memories[:limit],
            count=len(sorted_memories),
            sources=sources,
            error=None,
        )

    def _deduplicate(self, memories: list) -> list:
        """중복 제거"""
        seen = set()
        unique = []
        for m in memories:
            if m["id"] not in seen:
                seen.add(m["id"])
                unique.append(m)
        return unique

    def _sort_by_relevance(self, memories: list, query: str) -> list:
        """관련성으로 정렬"""
        def score(m):
            priority_scores = {"critical": 4, "high": 3, "medium": 2, "low": 1}
            return (
                priority_scores.get(m.get("priority", "medium"), 2),
                m.get("accessed_at", datetime.min),
            )
        return sorted(memories, key=score, reverse=True)
```

---

## Session Store (MySQL)

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Text, DateTime, Integer, JSON
from datetime import datetime

class Base(DeclarativeBase):
    pass

class Message(Base):
    """세션 메시지 모델"""
    __tablename__ = "messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)
    session_id: Mapped[str] = mapped_column(String(36), index=True)
    user_id: Mapped[str] = mapped_column(String(36), index=True)
    role: Mapped[str] = mapped_column(String(20))
    content: Mapped[str] = mapped_column(Text)
    metadata: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    token_count: Mapped[int] = mapped_column(Integer, default=0)


class SessionStore(MemoryStore):
    """MySQL 기반 세션 저장소"""

    def __init__(self, database_url: str):
        self.engine = create_async_engine(database_url)
        self._session_factory = async_sessionmaker(self.engine)

    async def save(self, entry: MemoryEntry) -> str:
        async with self._session_factory() as session:
            message = Message(
                id=entry["id"],
                session_id=entry["session_id"],
                user_id=entry["user_id"],
                role=entry["metadata"].get("role", "user"),
                content=entry["content"],
                metadata=entry["metadata"],
                created_at=entry["created_at"],
            )
            session.add(message)
            await session.commit()
            return entry["id"]

    async def get_messages(
        self,
        session_id: str,
        limit: int = 50,
    ) -> list[dict]:
        """세션의 최근 메시지 조회"""
        async with self._session_factory() as session:
            result = await session.execute(
                select(Message)
                .where(Message.session_id == session_id)
                .order_by(Message.created_at.desc())
                .limit(limit)
            )
            messages = result.scalars().all()

            return [
                {
                    "role": m.role,
                    "content": m.content,
                    "metadata": m.metadata,
                }
                for m in reversed(messages)
            ]
```

---

## Long-term Store (Vector DB)

```python
from openai import AsyncOpenAI

class VectorStore(MemoryStore):
    """벡터 DB 기반 장기 저장소"""

    def __init__(
        self,
        collection_name: str = "memories",
        embedding_model: str = "text-embedding-3-small",
    ):
        self.client = AsyncOpenAI()
        self.embedding_model = embedding_model

    async def _get_embedding(self, text: str) -> list[float]:
        """텍스트 임베딩 생성"""
        response = await self.client.embeddings.create(
            input=text,
            model=self.embedding_model,
        )
        return response.data[0].embedding

    async def save(self, entry: MemoryEntry) -> str:
        embedding = await self._get_embedding(entry["content"])

        self.collection.add(
            ids=[entry["id"]],
            embeddings=[embedding],
            documents=[entry["content"]],
            metadatas=[{
                "user_id": entry["user_id"],
                "memory_type": entry["memory_type"],
                "priority": entry["priority"],
                "created_at": entry["created_at"].isoformat(),
            }],
        )

        return entry["id"]

    async def search(
        self,
        query: str,
        user_id: str,
        limit: int = 10,
    ) -> list[MemoryEntry]:
        """시맨틱 검색"""
        query_embedding = await self._get_embedding(query)

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=limit,
            where={"user_id": user_id},
        )

        return [
            {
                "id": id_,
                "content": doc,
                "metadata": meta,
            }
            for id_, doc, meta in zip(
                results["ids"][0],
                results["documents"][0],
                results["metadatas"][0],
            )
        ]
```

---

## Agent Memory Adapter

```python
class AgentMemoryAdapter:
    """에이전트-메모리 통합 어댑터

    기능:
    - 자동 컨텍스트 주입 (prepare_input)
    - 자동 출력 저장 (save_output)
    - 자동 승격 (auto_promote)
    """

    def __init__(
        self,
        memory_manager: MemoryManager,
        user_id: str,
        agent_id: Optional[str] = None,
        session_id: Optional[str] = None,
        auto_promote: bool = True,
        promotion_threshold: int = 5,
    ):
        self.manager = memory_manager
        self.user_id = user_id
        self.agent_id = agent_id
        self.session_id = session_id
        self.auto_promote = auto_promote
        self.promotion_threshold = promotion_threshold
        self._interaction_count = 0

    async def prepare_input(
        self,
        user_input: str,
        include_recent: int = 10,
        include_relevant: int = 5,
    ) -> str:
        """컨텍스트가 포함된 입력 준비"""

        recent_messages = []
        if self.manager.session and self.session_id:
            recent_messages = await self.manager.session.get_messages(
                self.session_id,
                limit=include_recent,
            )

        relevant_context = await self.manager.get_context(
            query=user_input,
            user_id=self.user_id,
            include_cache=True,
            include_session=False,
            include_longterm=True,
            limit=include_relevant,
        )

        context_parts = []

        if relevant_context["memories"]:
            context_parts.append("Relevant context:")
            for m in relevant_context["memories"]:
                context_parts.append(f"- {m['content']}")
            context_parts.append("")

        if recent_messages:
            context_parts.append("Recent conversation:")
            for m in recent_messages:
                context_parts.append(f"{m['role']}: {m['content']}")
            context_parts.append("")

        context_parts.append(f"User: {user_input}")

        return "\n".join(context_parts)

    async def save_output(
        self,
        user_input: str,
        agent_output: str,
        priority: MemoryPriority = MemoryPriority.MEDIUM,
        metadata: Optional[dict] = None,
    ) -> None:
        """에이전트 출력 저장"""
        await self.manager.save_conversation(
            user_input=user_input,
            agent_output=agent_output,
            user_id=self.user_id,
            session_id=self.session_id or "default",
            agent_id=self.agent_id,
            priority=priority,
            metadata=metadata,
        )

        self._interaction_count += 1

        if self.auto_promote and self._interaction_count >= self.promotion_threshold:
            await self._trigger_promotion()
            self._interaction_count = 0
```

---

## Context Assembler

```python
class ContextAssembler:
    """대화 컨텍스트 조합기"""

    def __init__(
        self,
        session_store: SessionStore,
        memory_manager: MemoryManager,
        max_tokens: int = 4000,
    ):
        self.session_store = session_store
        self.memory_manager = memory_manager
        self.max_tokens = max_tokens

    async def assemble(
        self,
        user_id: str,
        session_id: str,
        current_input: str,
        include_history: bool = True,
        include_longterm: bool = True,
    ) -> dict:
        """컨텍스트 조합"""

        context = {
            "history": [],
            "relevant_memories": [],
            "system_additions": [],
        }

        token_count = 0

        if include_history:
            messages = await self.session_store.get_messages(session_id, limit=20)

            for msg in reversed(messages):
                msg_tokens = estimate_tokens(msg["content"])
                if token_count + msg_tokens > self.max_tokens * 0.6:
                    break
                context["history"].insert(0, msg)
                token_count += msg_tokens

        if include_longterm:
            result = await self.memory_manager.get_context(
                query=current_input,
                user_id=user_id,
                include_cache=False,
                include_session=False,
                include_longterm=True,
                limit=5,
            )

            for memory in result["memories"]:
                mem_tokens = estimate_tokens(memory["content"])
                if token_count + mem_tokens > self.max_tokens * 0.8:
                    break
                context["relevant_memories"].append(memory)
                token_count += mem_tokens

        return context
```

---

## 검증 체크리스트

| 항목 | 확인 |
|------|------|
| 3-tier 분리 | Cache/Session/Long-term 역할 구분 |
| TTL 관리 | Cache tier 만료 처리 |
| 시맨틱 검색 | 임베딩 기반 검색 |
| 토큰 제한 | 컨텍스트 크기 관리 |
| 자동 승격 | 중요 메모리 장기 저장 |
| 중복 제거 | 동일 메모리 필터링 |

**Remember**: Session tier는 대화 히스토리, Long-term tier는 지식과 중요 메모리를 저장합니다.
