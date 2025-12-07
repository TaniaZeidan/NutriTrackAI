"""Simple rebuild script without emojis for Windows compatibility."""
import sys
import json
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.embeddings import (
    _load_raw_documents,
    _get_embeddings,
    FAISS_INDEX_DIR,
    INDEX_FILE,
    META_FILE,
    VECTORS_FILE,
)

try:
    import faiss
    import numpy as np
except ImportError:
    print("Warning: faiss not installed, using fallback")
    faiss = None
    np = None

def main():
    print("="*60)
    print("Rebuilding FAISS Index with Gemini Embeddings")
    print("="*60)

    # Load documents
    print("\nLoading recipe documents...")
    documents = _load_raw_documents()
    print(f"Loaded {len(documents)} recipes")

    # Get embeddings
    print(f"\nGenerating Gemini embeddings for {len(documents)} recipes...")
    print("This will take a few minutes. Please wait...")

    texts = [doc.text for doc in documents]
    vectors, backend = _get_embeddings(texts)

    print(f"\nEmbeddings generated!")
    print(f"  Backend: {backend}")
    print(f"  Dimension: {len(vectors[0]) if vectors else 0}")
    print(f"  Total recipes: {len(vectors)}")

    if backend != "gemini":
        print(f"\nERROR: Using {backend} instead of Gemini!")
        return False

    # Save index
    print("\nSaving FAISS index...")
    FAISS_INDEX_DIR.mkdir(parents=True, exist_ok=True)

    if faiss and np is not None:
        array = np.array(vectors, dtype="float32")
        index = faiss.IndexFlatIP(array.shape[1])
        faiss.normalize_L2(array)
        index.add(array)
        faiss.write_index(index, str(INDEX_FILE))
        print("FAISS index saved")

    # Save metadata
    with open(META_FILE, "w", encoding="utf-8") as f:
        json.dump([doc.model_dump() for doc in documents], f)
    print("Metadata saved")

    # Save vectors
    with open(VECTORS_FILE, "w", encoding="utf-8") as f:
        json.dump({"backend": backend, "vectors": vectors}, f)
    print("Vectors saved")

    print("\n" + "="*60)
    print("SUCCESS! Index rebuilt with Gemini embeddings")
    print("="*60)
    print(f"\nIndexed {len(documents):,} recipes")
    print("\nNext step: Test your RAG")
    print("  python test_rag.py")

    return True

if __name__ == "__main__":
    main()
