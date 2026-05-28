from langchain_ollama import ChatOllama
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_core.messages import HumanMessage, AIMessage
from langchain_chroma import Chroma

SYSTEM_PROMPT = """당신은 업로드된 문서를 기반으로 질문에 답하는 AI 어시스턴트입니다.
아래의 컨텍스트를 활용하여 정확하고 간결하게 답변하세요.
컨텍스트에서 답을 찾을 수 없는 경우에는 모른다고 솔직하게 말하세요.

컨텍스트:
{context}"""


def build_chain(vectorstore: Chroma, model_name: str = "llama3.2", top_k: int = 4):
    """RAG 체인을 생성한다 (LCEL 방식)."""
    llm = ChatOllama(model=model_name, temperature=0)
    retriever = vectorstore.as_retriever(search_kwargs={"k": top_k})

    prompt = ChatPromptTemplate.from_messages([
        ("system", SYSTEM_PROMPT),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])

    def format_docs(docs):
        return "\n\n".join(doc.page_content for doc in docs)

    chain = (
        RunnablePassthrough.assign(
            context_docs=lambda x: retriever.invoke(x["input"])
        )
        | RunnablePassthrough.assign(
            context=lambda x: format_docs(x["context_docs"])
        )
        | RunnablePassthrough.assign(
            answer=prompt | llm | StrOutputParser()
        )
    )
    return chain


def format_history(messages: list[dict]) -> list:
    """Streamlit 메시지 목록을 LangChain 메시지 형식으로 변환한다."""
    history = []
    for msg in messages:
        if msg["role"] == "user":
            history.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            history.append(AIMessage(content=msg["content"]))
    return history
