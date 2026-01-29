# Tutorial 01: Basic RAG 구축하기

처음부터 끝까지 기본 RAG 시스템 구축 실습

## 목표

- PDF 문서를 로드하고 청킹
- Qdrant에 벡터 저장
- 간단한 Q&A 구현

## 사전 요구사항

```bash
pip install langchain langchain-openai langchain-community
pip install qdrant-client
pip install pypdf
```

## 환경 설정

```python
import os
from dotenv import load_dotenv

load_dotenv()

# OpenAI API 키 설정
os.environ["OPENAI_API_KEY"] = "your-api-key"
```

## Step 1: 문서 로딩

```python
from langchain_community.document_loaders import PyPDFLoader

# PDF 로드
loader = PyPDFLoader("your_document.pdf")
documents = loader.load()

print(f"Loaded {len(documents)} pages")
print(f"First page preview: {documents[0].page_content[:200]}")
```

**여러 파일 로드:**

```python
from langchain_community.document_loaders import DirectoryLoader

loader = DirectoryLoader(
    "./docs/",
    glob="**/*.pdf",
    loader_cls=PyPDFLoader
)
documents = loader.load()
```

## Step 2: 텍스트 청킹

```python
from langchain.text_splitter import RecursiveCharacterTextSplitter

splitter = RecursiveCharacterTextSplitter(
    chunk_size=1000,      # 청크 크기 (문자 수)
    chunk_overlap=200,    # 오버랩 (컨텍스트 유지)
    separators=["\n\n", "\n", ". ", " ", ""]
)

chunks = splitter.split_documents(documents)

print(f"Created {len(chunks)} chunks")
print(f"Sample chunk: {chunks[0].page_content[:200]}")
```

**청킹 품질 확인:**

```python
# 청크 크기 분포 확인
lengths = [len(chunk.page_content) for chunk in chunks]
print(f"Min: {min(lengths)}, Max: {max(lengths)}, Avg: {sum(lengths)/len(lengths):.0f}")
```

## Step 3: 임베딩 및 벡터 저장

```python
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import Qdrant

# 임베딩 모델
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")

# Qdrant에 저장 (로컬 메모리 모드)
vectorstore = Qdrant.from_documents(
    documents=chunks,
    embedding=embeddings,
    location=":memory:",  # 테스트용 메모리 모드
    collection_name="my_documents",
)

print("Vector store created!")
```

**영구 저장 (Docker Qdrant):**

```python
# 먼저 Docker로 Qdrant 실행
# docker run -p 6333:6333 qdrant/qdrant

vectorstore = Qdrant.from_documents(
    documents=chunks,
    embedding=embeddings,
    url="http://localhost:6333",
    collection_name="my_documents",
)
```

## Step 4: Retriever 생성

```python
# 기본 Retriever
retriever = vectorstore.as_retriever(
    search_type="similarity",
    search_kwargs={"k": 5}  # 상위 5개 검색
)

# 테스트
query = "What is the main topic?"
docs = retriever.get_relevant_documents(query)

print(f"Found {len(docs)} documents")
for i, doc in enumerate(docs, 1):
    print(f"\n[{i}] {doc.page_content[:150]}...")
```

## Step 5: RAG 체인 구성

```python
from langchain_openai import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser

# LLM
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

# 프롬프트
prompt = ChatPromptTemplate.from_template("""
Answer the question based only on the following context.
If you cannot answer from the context, say "I don't know."

Context:
{context}

Question: {question}

Answer:
""")

# 컨텍스트 포맷팅
def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

# RAG 체인
rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)
```

## Step 6: 질문하기

```python
# 질문
question = "What is the main topic of this document?"
answer = rag_chain.invoke(question)

print(f"Q: {question}")
print(f"A: {answer}")
```

**소스 문서 포함:**

```python
from langchain.chains import RetrievalQA

qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=retriever,
    return_source_documents=True,
)

result = qa_chain({"query": question})

print(f"Answer: {result['result']}")
print(f"\nSources:")
for doc in result['source_documents']:
    print(f"- {doc.metadata.get('source', 'Unknown')}: {doc.page_content[:100]}...")
```

## 전체 코드

```python
import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Qdrant
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser

# 1. 환경 설정
os.environ["OPENAI_API_KEY"] = "your-api-key"

# 2. 문서 로드
loader = PyPDFLoader("document.pdf")
documents = loader.load()

# 3. 청킹
splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
chunks = splitter.split_documents(documents)

# 4. 벡터 저장
embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
vectorstore = Qdrant.from_documents(
    chunks, embeddings,
    location=":memory:",
    collection_name="docs"
)

# 5. RAG 체인
retriever = vectorstore.as_retriever(search_kwargs={"k": 5})
llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)

prompt = ChatPromptTemplate.from_template("""
Answer based on the context. If unsure, say "I don't know."

Context: {context}
Question: {question}
Answer:
""")

def format_docs(docs):
    return "\n\n".join(doc.page_content for doc in docs)

rag_chain = (
    {"context": retriever | format_docs, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# 6. 질문
answer = rag_chain.invoke("What is this document about?")
print(answer)
```

## 다음 단계

- [Tutorial 02: 리랭킹 추가하기](02-advanced-rag-with-reranking.md)
- [Tutorial 03: 하이브리드 검색](03-hybrid-search.md)

## 체크리스트

- [ ] PDF 로드 성공
- [ ] 청크 생성 (500-1500 문자)
- [ ] 벡터 저장소 생성
- [ ] 검색 테스트 통과
- [ ] RAG 응답 확인
