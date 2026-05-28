"""
RAG 인덱싱 실습 스크립트
------------------------------
data/ 폴더에 있는 PDF 파일을 ChromaDB에 저장합니다.
각 단계에서 어떤 일이 일어나는지 직접 확인할 수 있습니다.

실행 방법:
    venv\\Scripts\\activate
    python index_data.py
"""

import os
import glob

# ─────────────────────────────────────────────
# 설정값 (바꿔보면서 차이를 관찰해보세요)
# ─────────────────────────────────────────────
DATA_DIR    = "./data"       # PDF가 들어있는 폴더
CHUNK_SIZE  = 800            # 청크 하나의 최대 글자 수
CHUNK_OVERLAP = 150          # 앞뒤 청크와 겹치는 글자 수


# ─────────────────────────────────────────────
# STEP 1: data/ 폴더에서 PDF 파일 목록 수집
# ─────────────────────────────────────────────
print("\n" + "="*50)
print("STEP 1: PDF 파일 탐색")
print("="*50)

pdf_files = glob.glob(os.path.join(DATA_DIR, "*.pdf"))

if not pdf_files:
    print(f"[오류] {DATA_DIR}/ 폴더에 PDF 파일이 없습니다.")
    print("PDF 파일을 data/ 폴더에 넣고 다시 실행하세요.")
    exit(1)

print(f"발견된 파일 수: {len(pdf_files)}개")
for f in pdf_files:
    size_kb = os.path.getsize(f) // 1024
    print(f"  - {os.path.basename(f)}  ({size_kb} KB)")


# ─────────────────────────────────────────────
# STEP 2: PDF를 텍스트로 변환 + 청킹
# ─────────────────────────────────────────────
print("\n" + "="*50)
print("STEP 2: PDF 텍스트 추출 및 청킹")
print(f"  청크 크기: {CHUNK_SIZE}자 / 오버랩: {CHUNK_OVERLAP}자")
print("="*50)

from rag.loader import load_and_split

all_chunks = []
for pdf_path in pdf_files:
    filename = os.path.basename(pdf_path)
    chunks = load_and_split(pdf_path, CHUNK_SIZE, CHUNK_OVERLAP)
    all_chunks.extend(chunks)
    print(f"  {filename} → {len(chunks)}개 청크 생성")

print(f"\n전체 청크 수: {len(all_chunks)}개")

# 청크 샘플 출력 (첫 번째 청크)
print("\n[샘플] 첫 번째 청크 내용:")
print("-" * 40)
sample = all_chunks[0]
print(f"출처: {os.path.basename(sample.metadata.get('source', ''))}  "
      f"페이지: {sample.metadata.get('page', 0) + 1}")
print(sample.page_content[:300])
if len(sample.page_content) > 300:
    print("...")
print("-" * 40)


# ─────────────────────────────────────────────
# STEP 3: 텍스트 → 벡터 변환 (임베딩)
# ─────────────────────────────────────────────
print("\n" + "="*50)
print("STEP 3: 임베딩 (텍스트 → 숫자 벡터)")
print("  모델: nomic-embed-text (Ollama)")
print("="*50)

from langchain_ollama import OllamaEmbeddings

embedder = OllamaEmbeddings(model="nomic-embed-text")

# 첫 번째 청크만 직접 벡터로 변환해서 구경하기
sample_text = all_chunks[0].page_content[:100]
print(f"\n입력 텍스트: \"{sample_text[:60]}...\"")

vector = embedder.embed_query(sample_text)
print(f"벡터 차원 수: {len(vector)}개")
print(f"벡터 앞 5개 값: {[round(v, 4) for v in vector[:5]]}")
print("→ 이 숫자 배열로 문장 간 유사도를 계산합니다.")


# ─────────────────────────────────────────────
# STEP 4: ChromaDB에 저장
# ─────────────────────────────────────────────
print("\n" + "="*50)
print("STEP 4: ChromaDB에 저장")
print("  저장 위치: ./chroma_db/")
print("="*50)

from rag.vectorstore import add_documents, get_vectorstore

print(f"\n{len(all_chunks)}개 청크를 저장하는 중...")
add_documents(all_chunks)

vs = get_vectorstore()
total = vs._collection.count()
print(f"저장 완료! DB에 저장된 총 청크 수: {total}개")


# ─────────────────────────────────────────────
# STEP 5: 검색 테스트 (잘 저장됐는지 확인)
# ─────────────────────────────────────────────
print("\n" + "="*50)
print("STEP 5: 검색 테스트")
print("="*50)

test_query = input("\n검색할 키워드나 문장을 입력하세요 (엔터 = 건너뜀): ").strip()

if test_query:
    retriever = vs.as_retriever(search_kwargs={"k": 3})
    results = retriever.invoke(test_query)
    print(f"\n상위 {len(results)}개 검색 결과:")
    for i, doc in enumerate(results, 1):
        fname = os.path.basename(doc.metadata.get("source", ""))
        page  = doc.metadata.get("page", 0) + 1
        print(f"\n[{i}] {fname} - {page}페이지")
        print(doc.page_content[:200])
        if len(doc.page_content) > 200:
            print("...")
else:
    print("검색 테스트를 건너뜁니다.")


print("\n" + "="*50)
print("인덱싱 완료! 이제 run.bat으로 챗봇을 실행하세요.")
print("="*50 + "\n")
