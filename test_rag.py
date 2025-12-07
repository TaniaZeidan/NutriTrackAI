"""Test script to verify RAG retrieval quality."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.rag import search_recipes

def test_query(query, expected_keywords):
    """Test if RAG retrieves relevant recipes."""
    print(f"\n{'='*60}")
    print(f"Query: '{query}'")
    print(f"{'='*60}")

    results = search_recipes(query, k=5)

    if not results:
        print("❌ No results found!")
        return False

    print(f"\nTop {len(results)} results:")
    relevant_found = False

    for i, res in enumerate(results, 1):
        title = res.document.title
        score = res.score
        print(f"{i}. {title} (score: {score:.3f})")

        # Check if any expected keyword is in the title
        if any(keyword.lower() in title.lower() for keyword in expected_keywords):
            relevant_found = True

    if relevant_found:
        print(f"\n✅ SUCCESS: Found relevant recipes for '{query}'")
    else:
        print(f"\n❌ FAILURE: No relevant recipes found for '{query}'")
        print(f"   Expected keywords: {expected_keywords}")

    return relevant_found

def main():
    print("=" * 60)
    print("Testing RAG Retrieval Quality")
    print("=" * 60)

    test_cases = [
        ("asparagus", ["asparagus", "vegetable", "roasted"]),
        ("chicken high protein", ["chicken", "protein", "breast"]),
        ("salmon", ["salmon", "fish"]),
        ("breakfast", ["breakfast", "yogurt", "oatmeal", "eggs"]),
    ]

    passed = 0
    total = len(test_cases)

    for query, expected in test_cases:
        if test_query(query, expected):
            passed += 1

    print("\n" + "=" * 60)
    print(f"Results: {passed}/{total} tests passed")
    print("=" * 60)

    if passed == total:
        print("\n🎉 All tests passed! Your RAG is working correctly.")
    elif passed > 0:
        print(f"\n⚠️  Some tests failed. RAG quality could be improved.")
    else:
        print("\n❌ All tests failed. RAG may still be using hash embeddings.")
        print("   Run rebuild_index.py again and check for errors.")

if __name__ == "__main__":
    main()
