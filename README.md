# GMP RAG ChatBot

Ollama + ChromaDB + Streamlit 기반 로컬 RAG 챗봇 실습 프로젝트

---

## 프로젝트 구조

```
GMP_RAG_ChatBot/
├── app.py              # Streamlit UI
├── rag/
│   ├── loader.py       # PDF 로딩 & 청킹
│   ├── vectorstore.py  # ChromaDB 관리
│   └── chain.py        # RAG 체인 (LangChain LCEL)
├── data/               # PDF 원본 보관 (선택)
├── chroma_db/          # 벡터 DB 영구 저장 (자동 생성)
├── requirements.txt
├── setup.bat           # 환경 자동 설치
└── run.bat             # 앱 실행
```

---

## 설치 및 실행

### 사전 요구사항

- Python 3.10 이상 — [python.org](https://python.org)

### 1. setup.bat 실행 (최초 1회)

```
setup.bat
```

아래 과정이 자동으로 진행됩니다.

| 단계 | 내용 |
|------|------|
| Python venv 생성 | `venv/` 폴더에 독립 환경 구성 |
| 패키지 설치 | `requirements.txt` 기반 의존성 설치 |
| Ollama 설치 | 미설치 시 자동 다운로드 및 설치 |
| Ollama 서버 시작 | 미실행 시 백그라운드로 자동 실행 |
| 모델 다운로드 | `llama3.2` (~2GB), `nomic-embed-text` (~270MB) |

### 2. 앱 실행 (매번)

```
run.bat
```

브라우저에서 `http://localhost:8501` 자동 접속

---

## RAG 작동 원리

RAG(Retrieval-Augmented Generation)는 LLM이 학습하지 않은 문서를 실시간으로 검색해 답변 근거로 활용하는 방식입니다.
PDF에 있는 내용은 답하고, 없는 내용은 모른다고 답합니다.

### 1단계 — 문서 인덱싱 (PDF 업로드 시 1회 실행)

```
PDF 업로드
    │
    ▼
[rag/loader.py] PyPDFLoader
    페이지 단위로 텍스트 추출
    │
    ▼
[rag/loader.py] RecursiveCharacterTextSplitter
    지정한 청크 크기(기본 800자) 단위로 분할
    청크 간 오버랩(기본 150자)으로 문맥 유지
    예) 10페이지 PDF → 50~100개 청크
    │
    ▼
[rag/vectorstore.py] OllamaEmbeddings (nomic-embed-text)
    각 청크를 숫자 벡터로 변환
    예) "RAG란 검색 기반 생성이다" → [0.12, -0.45, 0.87, ...]
    │
    ▼
[rag/vectorstore.py] ChromaDB
    벡터 + 원본 텍스트 + 메타데이터(파일명, 페이지번호)를
    chroma_db/ 폴더에 영구 저장
    앱을 재시작해도 데이터 유지, 재인덱싱 불필요
```

> PDF 원본은 임시 파일로 처리된 후 즉시 삭제됩니다. `chroma_db/` 안의 벡터 데이터만 남습니다.

### 2단계 — 질의응답 (질문할 때마다 실행)

```
사용자 질문 입력
    │
    ▼
[rag/chain.py] OllamaEmbeddings (nomic-embed-text)
    질문도 동일한 방식으로 벡터로 변환
    │
    ▼
[rag/chain.py] ChromaDB 유사도 검색
    질문 벡터와 저장된 청크 벡터를 코사인 유사도로 비교
    가장 유사한 top-k개 청크 반환 (기본 4개)
    │
    ▼
[rag/chain.py] 프롬프트 조립
    시스템 프롬프트 + 검색된 청크(context) + 대화 기록 + 질문
    │
    ▼
[rag/chain.py] ChatOllama (llama3.2)
    조립된 프롬프트를 LLM에 전달해 답변 생성
    │
    ▼
[app.py] 화면 출력
    답변 + 참조 문서(파일명, 페이지번호, 청크 내용) 표시
```

### 저장 경로 정리

| 데이터 | 경로 | 유지 여부 |
|--------|------|-----------|
| PDF 원본 | `%TEMP%\*.pdf` | 인덱싱 후 즉시 삭제 |
| 벡터 DB | `chroma_db/` | 영구 보존 |
| Python 환경 | `venv/` | 영구 보존 |

---

## 주요 파라미터 (사이드바에서 조절 가능)

| 파라미터 | 기본값 | 설명 |
|---------|--------|------|
| 청크 크기 | 800자 | 텍스트 분할 단위. 클수록 문맥 풍부, 작을수록 정밀 검색 |
| 청크 오버랩 | 150자 | 청크 간 중복 구간. 경계 부분 문맥 손실 방지 |
| top-k | 4 | 검색할 유사 청크 수. 많을수록 풍부하지만 속도 저하 |
| Ollama 모델 | llama3.2 | 답변 생성 LLM |

---

## 사용 기술 스택

| 역할 | 라이브러리 |
|------|-----------|
| UI | Streamlit |
| LLM | Ollama (llama3.2) |
| 임베딩 | Ollama (nomic-embed-text) |
| 벡터 DB | ChromaDB |
| PDF 파싱 | PyPDF |
| RAG 체인 | LangChain LCEL |
