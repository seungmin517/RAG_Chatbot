from langchain_ollama import OllamaEmbeddings
from langchain_chroma import Chroma
from langchain_core.documents import Document

PERSIST_DIR = "./chroma_db"
COLLECTION_NAME = "rag_docs"
EMBED_MODEL = "nomic-embed-text"


def _get_embeddings() -> OllamaEmbeddings:
    return OllamaEmbeddings(model=EMBED_MODEL)


def get_vectorstore() -> Chroma:
    """ChromaDB 인스턴스를 반환한다 (로컬 파일에 영구 저장)."""
    return Chroma(
        collection_name=COLLECTION_NAME,
        embedding_function=_get_embeddings(),
        persist_directory=PERSIST_DIR,
    )


def add_documents(docs: list[Document]) -> int:
    """문서 청크를 벡터 DB에 추가하고 저장된 청크 수를 반환한다."""
    vs = get_vectorstore()
    vs.add_documents(docs)
    return len(docs)


def reset_vectorstore() -> None:
    """컬렉션을 초기화한다."""
    vs = get_vectorstore()
    vs.reset_collection()
