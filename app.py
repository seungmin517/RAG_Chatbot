import os
import subprocess
import tempfile
import streamlit as st

from rag.loader import load_and_split
from rag.vectorstore import get_vectorstore, add_documents, reset_vectorstore
from rag.chain import build_chain, format_history


DEFAULT_MODEL = "llama3.2"


def get_installed_ollama_models() -> list[str]:
    """Return locally installed Ollama model names, falling back to the class model."""
    try:
        result = subprocess.run(
            ["ollama", "list"],
            capture_output=True,
            text=True,
            check=True,
            encoding="utf-8",
            errors="ignore",
        )
    except (FileNotFoundError, subprocess.SubprocessError):
        return [DEFAULT_MODEL]

    models = []
    for line in result.stdout.splitlines()[1:]:
        parts = line.split()
        if parts:
            models.append(parts[0])

    return models or [DEFAULT_MODEL]


# ── 페이지 설정 ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="RAG 챗봇", page_icon="📚", layout="wide")
st.title("📚 RAG 챗봇 (Ollama + ChromaDB)")

# ── 세션 상태 초기화 ──────────────────────────────────────────────────────────
if "messages" not in st.session_state:
    st.session_state.messages = []
if "indexed_files" not in st.session_state:
    st.session_state.indexed_files = []

# ── 사이드바 ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ 모델 설정")

    installed_models = get_installed_ollama_models()
    model_name = st.selectbox(
        "Ollama 모델",
        installed_models,
        index=installed_models.index(DEFAULT_MODEL) if DEFAULT_MODEL in installed_models else 0,
        help="ollama list 명령으로 설치된 모델을 확인하세요.",
    )
    top_k = st.slider("검색할 청크 수 (top-k)", 1, 10, 4)

    st.divider()
    st.header("📄 문서 인덱싱")

    chunk_size = st.slider("청크 크기 (글자)", 300, 2000, 800, 100)
    chunk_overlap = st.slider("청크 오버랩", 0, 400, 150, 50)

    uploaded_files = st.file_uploader(
        "PDF 파일 업로드 (복수 선택 가능)",
        type="pdf",
        accept_multiple_files=True,
    )

    col1, col2 = st.columns(2)
    with col1:
        if st.button("인덱싱", use_container_width=True, type="primary"):
            if not uploaded_files:
                st.warning("PDF 파일을 먼저 선택하세요.")
            else:
                with st.spinner("문서 처리 중..."):
                    total_chunks = 0
                    skipped_files = []
                    for uf in uploaded_files:
                        if uf.name in st.session_state.indexed_files:
                            skipped_files.append(uf.name)
                            continue

                        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
                            tmp.write(uf.read())
                            tmp_path = tmp.name
                        try:
                            docs = load_and_split(tmp_path, chunk_size, chunk_overlap)
                            for doc in docs:
                                doc.metadata["source"] = uf.name
                            add_documents(docs)
                            total_chunks += len(docs)
                            st.session_state.indexed_files.append(uf.name)
                        finally:
                            os.unlink(tmp_path)
                st.success(f"완료! 총 {total_chunks}개 청크 저장됨")
                if skipped_files:
                    st.info("이미 인덱싱된 파일은 건너뛰었습니다: " + ", ".join(skipped_files))

    with col2:
        if st.button("DB 초기화", use_container_width=True):
            reset_vectorstore()
            st.session_state.indexed_files = []
            st.session_state.messages = []
            st.success("초기화 완료")

    if st.session_state.indexed_files:
        st.divider()
        st.caption("인덱싱된 파일")
        for fname in st.session_state.indexed_files:
            st.caption(f"✅ {fname}")

# ── 메인 채팅 영역 ────────────────────────────────────────────────────────────
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("문서에 대해 질문하세요..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        vectorstore = get_vectorstore()

        # 인덱싱된 문서가 있는지 확인
        if vectorstore._collection.count() == 0:
            answer = "아직 인덱싱된 문서가 없습니다. 사이드바에서 PDF를 업로드하고 인덱싱해 주세요."
            st.warning(answer)
        else:
            chain = build_chain(vectorstore, model_name, top_k)
            chat_history = format_history(st.session_state.messages[:-1])

            # 스트리밍 응답
            answer_placeholder = st.empty()
            full_answer = ""
            source_docs = []

            with st.spinner(""):
                result = chain.invoke({
                    "input": prompt,
                    "chat_history": chat_history,
                })

            full_answer = result["answer"]
            source_docs = result.get("context_docs", [])
            answer_placeholder.markdown(full_answer)

            # 참조 문서 표시
            if source_docs:
                with st.expander(f"📎 참조 문서 ({len(source_docs)}개)"):
                    for i, doc in enumerate(source_docs, 1):
                        page = doc.metadata.get("page", "?")
                        source = doc.metadata.get("source", "")
                        filename = os.path.basename(source) if source else "알 수 없음"
                        st.markdown(f"**[{i}] {filename} — 페이지 {page + 1}**")
                        st.text(doc.page_content[:300] + ("..." if len(doc.page_content) > 300 else ""))
                        if i < len(source_docs):
                            st.divider()

        st.session_state.messages.append({"role": "assistant", "content": full_answer if vectorstore._collection.count() > 0 else answer})

# ── 대화 초기화 버튼 ──────────────────────────────────────────────────────────
if st.session_state.messages:
    if st.button("대화 초기화", use_container_width=False):
        st.session_state.messages = []
        st.rerun()
