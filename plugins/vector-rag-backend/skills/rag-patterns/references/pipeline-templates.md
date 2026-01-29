# RAG Pipeline Templates

RAG 파이프라인 코드 템플릿 모음

## Basic RAG

가장 기본적인 RAG 구현.

```python
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Chroma
from langchain.chains import RetrievalQA

# 컴포넌트 초기화
embeddings = OpenAIEmbeddings()
llm = ChatOpenAI(model="gpt-3.5-turbo")

# 벡터 저장소 생성
vectorstore = Chroma.from_documents(
    documents,
    embedding=embeddings,
    persist_directory="./chroma_db"
)

# RAG 체인
qa_chain = RetrievalQA.from_chain_type(
    llm=llm,
    chain_type="stuff",
    retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
    return_source_documents=True,
)

# 실행
result = qa_chain({"query": "What is machine learning?"})
print(result["result"])
print(result["source_documents"])
```

## Advanced RAG with Reranking

리랭킹이 포함된 고급 RAG.

```python
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langchain_community.vectorstores import Qdrant
from langchain.retrievers import ContextualCompressionRetriever
from langchain_cohere import CohereRerank
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser

# 컴포넌트
embeddings = OpenAIEmbeddings()
llm = ChatOpenAI(model="gpt-4")

# 벡터 저장소
vectorstore = Qdrant.from_documents(
    documents,
    embeddings,
    location=":memory:",
)

# 리랭킹 Retriever
base_retriever = vectorstore.as_retriever(search_kwargs={"k": 20})
reranker = CohereRerank(model="rerank-english-v3.0", top_n=5)
retriever = ContextualCompressionRetriever(
    base_compressor=reranker,
    base_retriever=base_retriever,
)

# 프롬프트
prompt = ChatPromptTemplate.from_template("""
Answer the question based only on the following context:

{context}

Question: {question}

Answer:
""")

# LCEL 체인
chain = (
    {"context": retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)

# 실행
answer = chain.invoke("What is machine learning?")
```

## Hybrid RAG (BM25 + Vector)

키워드와 시맨틱 검색 결합.

```python
from langchain.retrievers import EnsembleRetriever
from langchain_community.retrievers import BM25Retriever
from langchain_community.vectorstores import FAISS

# BM25 Retriever
bm25_retriever = BM25Retriever.from_documents(documents)
bm25_retriever.k = 10

# Vector Retriever
vectorstore = FAISS.from_documents(documents, embeddings)
vector_retriever = vectorstore.as_retriever(search_kwargs={"k": 10})

# 앙상블
ensemble_retriever = EnsembleRetriever(
    retrievers=[bm25_retriever, vector_retriever],
    weights=[0.3, 0.7],  # BM25 30%, Vector 70%
)

# RAG 체인
chain = (
    {"context": ensemble_retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)
```

## Multi-Query RAG

다중 쿼리로 검색 범위 확장.

```python
from langchain.retrievers.multi_query import MultiQueryRetriever

# Multi-Query Retriever
multi_retriever = MultiQueryRetriever.from_llm(
    retriever=vectorstore.as_retriever(search_kwargs={"k": 5}),
    llm=llm,
    include_original=True,
)

# 체인
chain = (
    {"context": multi_retriever, "question": RunnablePassthrough()}
    | prompt
    | llm
    | StrOutputParser()
)
```

## Conversational RAG

대화 히스토리를 유지하는 RAG.

```python
from langchain.chains import ConversationalRetrievalChain
from langchain.memory import ConversationBufferMemory

# 메모리 설정
memory = ConversationBufferMemory(
    memory_key="chat_history",
    return_messages=True,
    output_key="answer"
)

# 대화형 RAG 체인
conv_chain = ConversationalRetrievalChain.from_llm(
    llm=llm,
    retriever=retriever,
    memory=memory,
    return_source_documents=True,
    verbose=True,
)

# 대화
result1 = conv_chain({"question": "What is Python?"})
result2 = conv_chain({"question": "What are its main features?"})  # 컨텍스트 유지
```

## Parent Document RAG

작은 청크로 검색, 큰 청크로 응답.

```python
from langchain.retrievers import ParentDocumentRetriever
from langchain.storage import InMemoryStore
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 청크 분할기
parent_splitter = RecursiveCharacterTextSplitter(chunk_size=2000)
child_splitter = RecursiveCharacterTextSplitter(chunk_size=400)

# 저장소
vectorstore = Chroma(embedding_function=embeddings)
store = InMemoryStore()

# Parent Document Retriever
parent_retriever = ParentDocumentRetriever(
    vectorstore=vectorstore,
    docstore=store,
    child_splitter=child_splitter,
    parent_splitter=parent_splitter,
)

# 문서 추가
parent_retriever.add_documents(documents)

# 검색 (child로 검색, parent 반환)
docs = parent_retriever.get_relevant_documents("query")
```

## Self-Query RAG

쿼리에서 자동으로 필터 추출.

```python
from langchain.retrievers.self_query.base import SelfQueryRetriever
from langchain.chains.query_constructor.base import AttributeInfo

# 메타데이터 필드 정의
metadata_field_info = [
    AttributeInfo(
        name="category",
        description="The document category (e.g., 'tech', 'science')",
        type="string",
    ),
    AttributeInfo(
        name="year",
        description="The publication year",
        type="integer",
    ),
    AttributeInfo(
        name="author",
        description="The author name",
        type="string",
    ),
]

# Self-Query Retriever
self_query_retriever = SelfQueryRetriever.from_llm(
    llm=llm,
    vectorstore=vectorstore,
    document_contents="Technical articles about software and AI",
    metadata_field_info=metadata_field_info,
)

# 자동 필터 추출
# "Python articles from 2024" → filter: {category: "tech", year: 2024}
docs = self_query_retriever.get_relevant_documents("Python articles from 2024")
```

## Agentic RAG

에이전트가 검색 여부를 판단.

```python
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.tools.retriever import create_retriever_tool

# Retriever Tool 생성
retriever_tool = create_retriever_tool(
    retriever,
    name="document_search",
    description="Search for information in the document database"
)

# 에이전트 생성
agent = create_openai_functions_agent(
    llm=llm,
    tools=[retriever_tool],
    prompt=agent_prompt,
)

agent_executor = AgentExecutor(
    agent=agent,
    tools=[retriever_tool],
    verbose=True,
)

# 실행 (에이전트가 필요시 검색)
result = agent_executor.invoke({"input": "What is the company policy on vacation?"})
```

## Streaming RAG

스트리밍 응답.

```python
from langchain.callbacks.streaming_stdout import StreamingStdOutCallbackHandler

# 스트리밍 LLM
streaming_llm = ChatOpenAI(
    model="gpt-4",
    streaming=True,
    callbacks=[StreamingStdOutCallbackHandler()]
)

# 스트리밍 체인
async def stream_rag(question: str):
    context = retriever.get_relevant_documents(question)
    context_text = "\n".join([doc.page_content for doc in context])

    async for chunk in streaming_llm.astream(
        prompt.format(context=context_text, question=question)
    ):
        yield chunk.content
```

## Production RAG Template

프로덕션용 완전한 템플릿.

```python
from typing import List, Dict, Any
import logging

class ProductionRAG:
    def __init__(
        self,
        vectorstore,
        reranker,
        llm,
        embedding_model,
        config: dict = None
    ):
        self.vectorstore = vectorstore
        self.reranker = reranker
        self.llm = llm
        self.embeddings = embedding_model
        self.config = config or {
            "retrieval_k": 20,
            "rerank_top_n": 5,
            "similarity_threshold": 0.7,
        }
        self.logger = logging.getLogger(__name__)

    def query(
        self,
        question: str,
        filters: dict = None,
        include_sources: bool = True
    ) -> Dict[str, Any]:
        """RAG 쿼리 실행"""
        try:
            # 1. 검색
            self.logger.info(f"Retrieving for: {question[:50]}...")
            docs = self._retrieve(question, filters)

            if not docs:
                return {"answer": "No relevant information found.", "sources": []}

            # 2. 리랭킹
            self.logger.info(f"Reranking {len(docs)} documents...")
            reranked = self._rerank(question, docs)

            # 3. 컨텍스트 구성
            context = self._build_context(reranked)

            # 4. 생성
            self.logger.info("Generating answer...")
            answer = self._generate(question, context)

            # 5. 결과 구성
            result = {"answer": answer}
            if include_sources:
                result["sources"] = [
                    {"content": d.page_content[:200], "metadata": d.metadata}
                    for d in reranked
                ]

            return result

        except Exception as e:
            self.logger.error(f"RAG query failed: {e}")
            raise

    def _retrieve(self, question: str, filters: dict) -> List:
        """문서 검색"""
        search_kwargs = {"k": self.config["retrieval_k"]}
        if filters:
            search_kwargs["filter"] = filters

        return self.vectorstore.similarity_search(
            question, **search_kwargs
        )

    def _rerank(self, question: str, docs: List) -> List:
        """문서 리랭킹"""
        if not self.reranker:
            return docs[:self.config["rerank_top_n"]]

        return self.reranker.rerank(
            question, docs, top_k=self.config["rerank_top_n"]
        )

    def _build_context(self, docs: List) -> str:
        """컨텍스트 구성 (sides 전략)"""
        # Repacking: sides strategy
        reordered = []
        for i, doc in enumerate(docs):
            if i % 2 == 0:
                reordered.insert(0, doc)
            else:
                reordered.append(doc)

        return "\n\n---\n\n".join([
            f"[{i+1}] {doc.page_content}"
            for i, doc in enumerate(reordered)
        ])

    def _generate(self, question: str, context: str) -> str:
        """답변 생성"""
        prompt = f"""Based on the following context, answer the question.
Cite sources using [1], [2], etc.

Context:
{context}

Question: {question}

Answer:"""

        return self.llm.invoke(prompt).content

# 사용
rag = ProductionRAG(
    vectorstore=vectorstore,
    reranker=reranker,
    llm=llm,
    embedding_model=embeddings
)

result = rag.query("What is machine learning?")
print(result["answer"])
```

## LangGraph RAG

상태 기반 RAG 워크플로우.

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List

class RAGState(TypedDict):
    question: str
    documents: List
    answer: str

def retrieve(state: RAGState) -> RAGState:
    docs = retriever.get_relevant_documents(state["question"])
    return {"documents": docs}

def generate(state: RAGState) -> RAGState:
    context = "\n".join([d.page_content for d in state["documents"]])
    answer = llm.invoke(f"Context: {context}\nQuestion: {state['question']}")
    return {"answer": answer.content}

# 그래프 구성
workflow = StateGraph(RAGState)
workflow.add_node("retrieve", retrieve)
workflow.add_node("generate", generate)
workflow.set_entry_point("retrieve")
workflow.add_edge("retrieve", "generate")
workflow.add_edge("generate", END)

app = workflow.compile()

# 실행
result = app.invoke({"question": "What is RAG?"})
```
