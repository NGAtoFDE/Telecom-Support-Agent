"""Test the index directly without going through the API server."""
import sys
sys.path.insert(0, "src")
import logging
logging.disable(logging.CRITICAL)

from telecom_agent.config.settings import get_settings
from telecom_agent.rag.embeddings import get_embedder
from telecom_agent.rag.retriever import HybridRetriever
from telecom_agent.rag.vector_store import VectorStore
import json

s = get_settings()

print(f"Loading index from {s.index_dir}...")
# Get embedder
embed_fn = get_embedder(s)

# Load retriever
retriever = HybridRetriever.load(s.index_dir, embed_fn=embed_fn)
print(f"Index loaded. Store has {len(retriever._store.chunks)} chunks.")
print(f"Embed function is present: {retriever._embed_fn is not None}")

# Query
query = "my internet speed is slow since yesterday"
print(f"\nSearching for: '{query}'")
result = retriever.search(query, k=5)

print(f"Found {len(result.chunks)} chunks. Max score: {result.max_score}")

for i, chunk in enumerate(result.chunks[:5]):
    print(f"\n[{i+1}] {chunk.doc_id} - {chunk.title}")
    print(f"    Section: {chunk.section}")
    print(f"    Score: {chunk.score:.4f}")
    print(f"    Source: {getattr(chunk, 'source', 'unknown')}")
