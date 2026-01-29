# Chunking Strategies

문서 청킹 전략 - 시맨틱, 적응형, 계층적 청킹

## 청킹의 중요성

청킹은 RAG 성능에 가장 큰 영향을 미치는 요소입니다.

**연구 결과:**
- Fixed-length chunking: 50% accuracy (baseline)
- Semantic chunking: **87% accuracy** (+37%)
- 잘못된 청킹 = 관련 정보 누락 또는 노이즈 증가

## 청킹 전략 비교

| 전략 | 정확도 | 구현 복잡도 | 적합한 문서 |
|------|--------|------------|------------|
| Fixed-length | 50% | 쉬움 | 균일한 텍스트 |
| Recursive | 65% | 쉬움 | 일반 문서 |
| Semantic | 87% | 중간 | 기술 문서, 논문 |
| Adaptive | 85-90% | 높음 | 다양한 구조 |
| Hierarchical | 80-85% | 높음 | 계층적 문서 |

## Fixed-Length Chunking

가장 단순한 방식. 일정 길이로 분할.

```python
from langchain.text_splitter import CharacterTextSplitter

# 기본 고정 길이
splitter = CharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separator="\n"
)
chunks = splitter.split_text(document)
```

### 한계
- 의미 단위 무시
- 문장/단락 중간에서 잘림
- 컨텍스트 손실

## Recursive Character Splitting

구분자 계층을 따라 재귀적 분할.

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=200,
    separators=[
        "\n\n",     # 단락
        "\n",       # 줄
        ". ",       # 문장
        ", ",       # 절
        " ",        # 단어
        ""          # 문자
    ]
)
chunks = splitter.split_text(document)
```

### Markdown 문서용

```python
from langchain.text_splitter import MarkdownHeaderTextSplitter

headers_to_split_on = [
    ("#", "Header 1"),
    ("##", "Header 2"),
    ("###", "Header 3"),
]

splitter = MarkdownHeaderTextSplitter(
    headers_to_split_on=headers_to_split_on
)
chunks = splitter.split_text(markdown_document)
```

## Semantic Chunking

임베딩 유사도 기반으로 의미 경계 감지.

```python
from langchain_experimental.text_splitter import SemanticChunker
from langchain_openai import OpenAIEmbeddings

embeddings = OpenAIEmbeddings()

# 퍼센타일 기반 (권장)
semantic_chunker = SemanticChunker(
    embeddings=embeddings,
    breakpoint_threshold_type="percentile",
    breakpoint_threshold_amount=95,  # 상위 5%에서 분할
)

# 표준편차 기반
semantic_chunker = SemanticChunker(
    embeddings=embeddings,
    breakpoint_threshold_type="standard_deviation",
    breakpoint_threshold_amount=3,  # 3 표준편차
)

chunks = semantic_chunker.split_text(document)
```

### 작동 원리

```
문장 1 ─┐
문장 2 ─┼─ 유사도 높음 → 같은 청크
문장 3 ─┘
        ↓ 유사도 급락 (breakpoint)
문장 4 ─┐
문장 5 ─┼─ 유사도 높음 → 새 청크
문장 6 ─┘
```

## Adaptive Chunking

문서 구조에 따라 동적으로 청킹 전략 선택.

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

def adaptive_chunk(document: str, doc_type: str) -> list:
    """문서 타입에 따른 적응형 청킹"""

    if doc_type == "markdown":
        separators = ["\n## ", "\n### ", "\n\n", "\n", ". "]
        chunk_size = 1000
    elif doc_type == "code":
        separators = ["\nclass ", "\ndef ", "\n\n", "\n"]
        chunk_size = 500
    elif doc_type == "legal":
        separators = ["\nArticle ", "\nSection ", "\n\n", ". "]
        chunk_size = 500
    elif doc_type == "chat":
        separators = ["\n\n", "\n"]
        chunk_size = 2000  # 대화는 더 큰 컨텍스트
    else:
        separators = ["\n\n", "\n", ". ", " "]
        chunk_size = 1000

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size,
        chunk_overlap=int(chunk_size * 0.15),
        separators=separators
    )
    return splitter.split_text(document)
```

### AST 기반 코드 청킹

```python
import ast

def chunk_python_code(code: str) -> list:
    """Python 코드를 AST 기반으로 청킹"""
    tree = ast.parse(code)
    chunks = []

    for node in ast.iter_child_nodes(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            chunk = ast.get_source_segment(code, node)
            chunks.append({
                "type": type(node).__name__,
                "name": node.name,
                "content": chunk,
                "line_start": node.lineno,
                "line_end": node.end_lineno,
            })

    return chunks
```

## Hierarchical Chunking (Parent-Child)

작은 청크로 검색하고, 큰 컨텍스트로 응답.

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Parent chunker (큰 단위)
parent_splitter = RecursiveCharacterTextSplitter(
    chunk_size=2000,
    chunk_overlap=0,
)

# Child chunker (작은 단위)
child_splitter = RecursiveCharacterTextSplitter(
    chunk_size=400,
    chunk_overlap=50,
)

def create_hierarchical_chunks(document: str):
    """계층적 청크 생성"""
    chunks = []
    parent_chunks = parent_splitter.split_text(document)

    for i, parent in enumerate(parent_chunks):
        child_chunks = child_splitter.split_text(parent)

        for j, child in enumerate(child_chunks):
            chunks.append({
                "id": f"parent_{i}_child_{j}",
                "parent_id": f"parent_{i}",
                "parent_content": parent,
                "child_content": child,
                "position": j,
            })

    return chunks

# 검색 시: child_content로 검색
# 응답 시: parent_content를 LLM에 전달
```

### LangChain ParentDocumentRetriever

```python
from langchain.retrievers import ParentDocumentRetriever
from langchain.storage import InMemoryStore
from langchain_community.vectorstores import Chroma

# 부모 문서 저장소
store = InMemoryStore()

# 자식 청크 벡터 저장소
vectorstore = Chroma(embedding_function=embeddings)

retriever = ParentDocumentRetriever(
    vectorstore=vectorstore,
    docstore=store,
    child_splitter=child_splitter,
    parent_splitter=parent_splitter,
)

# 문서 추가
retriever.add_documents(documents)

# 검색: child로 검색하지만 parent 반환
relevant_docs = retriever.get_relevant_documents("query")
```

## 청크 크기 가이드라인

### 검색 최적화

| 목적 | 청크 크기 | 오버랩 | 참고 |
|------|----------|--------|------|
| 정밀 검색 | 300-500 | 50-100 | 구체적 질문 |
| 일반 검색 | 500-1000 | 100-200 | 대부분의 경우 |
| 요약/개요 | 1000-2000 | 200-400 | 넓은 컨텍스트 |

### 문서 타입별

| 문서 타입 | 청크 크기 | 청킹 전략 |
|----------|----------|----------|
| 기술 문서 | 500-1000 | Semantic |
| 법률 문서 | 300-500 | Adaptive (Section) |
| 코드 | 함수/클래스 단위 | AST 기반 |
| 채팅 로그 | 10-20 메시지 | 시간/화자 기반 |
| 논문 | 500-800 | Section 기반 |

## 오버랩 전략

```python
# 오버랩 비율 권장: 10-20%

# 문장 단위 오버랩 (권장)
def overlap_by_sentences(chunks: list, overlap_sentences: int = 2):
    """문장 단위로 오버랩"""
    result = []
    for i, chunk in enumerate(chunks):
        sentences = chunk.split('. ')

        if i > 0:
            # 이전 청크의 마지막 N 문장 추가
            prev_sentences = chunks[i-1].split('. ')
            prefix = '. '.join(prev_sentences[-overlap_sentences:]) + '. '
            chunk = prefix + chunk

        result.append(chunk)
    return result
```

## 메타데이터 추가

```python
def chunk_with_metadata(document: dict) -> list:
    """청크에 메타데이터 추가"""
    chunks = splitter.split_text(document["content"])

    return [
        {
            "content": chunk,
            "metadata": {
                "doc_id": document["id"],
                "source": document["source"],
                "chunk_index": i,
                "total_chunks": len(chunks),
                "created_at": document.get("created_at"),
                "section": extract_section(chunk),  # 섹션 추출
            }
        }
        for i, chunk in enumerate(chunks)
    ]
```

## 청킹 품질 검증

```python
def validate_chunks(chunks: list) -> dict:
    """청크 품질 검증"""
    stats = {
        "total_chunks": len(chunks),
        "avg_length": sum(len(c) for c in chunks) / len(chunks),
        "min_length": min(len(c) for c in chunks),
        "max_length": max(len(c) for c in chunks),
        "empty_chunks": sum(1 for c in chunks if not c.strip()),
        "short_chunks": sum(1 for c in chunks if len(c) < 100),
    }

    # 경고 조건
    warnings = []
    if stats["empty_chunks"] > 0:
        warnings.append(f"Empty chunks: {stats['empty_chunks']}")
    if stats["short_chunks"] > len(chunks) * 0.1:
        warnings.append(f"Too many short chunks: {stats['short_chunks']}")
    if stats["max_length"] > 3 * stats["avg_length"]:
        warnings.append("High variance in chunk sizes")

    stats["warnings"] = warnings
    return stats
```

## Anti-Patterns

### ❌ 고정 크기만 사용

```python
# BAD: 의미 단위 무시
chunks = [text[i:i+1000] for i in range(0, len(text), 1000)]
```

### ❌ 오버랩 없음

```python
# BAD: 문맥 손실
splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,
    chunk_overlap=0  # 오버랩 없음
)
```

### ❌ 구조 무시

```python
# BAD: HTML 태그 중간에서 잘림
chunks = splitter.split_text(html_content)  # <table> 깨짐
```

### ✅ 권장

```python
# GOOD: 문서 구조 존중
from langchain.document_loaders import BSHTMLLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter

# HTML 파싱 후 청킹
loader = BSHTMLLoader("page.html")
docs = loader.load()
chunks = splitter.split_documents(docs)
```
