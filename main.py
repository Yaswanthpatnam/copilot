import json
import os
import time
from typing import Dict, Any, List, AsyncGenerator
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from backend.document_parser import DocumentParser, DocumentChunker
from backend.normalizer import TextNormalizer
from backend.retrieval import InvertedIndexRetriever
from backend.llm_client import GroundedLLMClient
from backend.cache import QueryCache


# Initialize FastAPI application
app = FastAPI(
    title="Manufacturing Plant AI Copilot",
    description="Grounded Technical SOP & Maintenance Copilot for Kaveri Precision Components (Hosur Plant)",
    version="2.0.0"
)

# Enable CORS for local network and mobile devices
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup directories
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DOCS_DIR = os.path.join(BASE_DIR, "docs")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

# Setup template engine
templates = Jinja2Templates(directory=TEMPLATES_DIR)


# Global Application State Container
class CopilotState:
    parser: DocumentParser = None
    retriever: InvertedIndexRetriever = None
    normalizer: TextNormalizer = None
    llm_client: GroundedLLMClient = None
    cache: QueryCache = None
    all_chunks: List[Dict[str, Any]] = []

state = CopilotState()


@app.on_event("startup")
def startup_event():
    """
    Initializes document ingestion, builds the BM25 Inverted Index with Porter Stemming,
    populates the normalizer vocabulary, and initializes the in-memory LRU Query Cache.
    """
    print(f"[*] Initializing Manufacturing Plant Copilot from {DOCS_DIR}...")
    state.parser = DocumentParser(docs_dir=DOCS_DIR)
    documents = state.parser.load_documents()

    all_chunks = []
    for doc in documents:
        chunks = DocumentChunker.chunk_document(doc)
        all_chunks.extend(chunks)

    state.all_chunks = all_chunks
    state.retriever = InvertedIndexRetriever()
    state.retriever.build_index(all_chunks)

    vocab = state.retriever.extract_vocabulary()
    state.normalizer = TextNormalizer(vocabulary=vocab)
    state.llm_client = GroundedLLMClient()
    state.cache = QueryCache(capacity=256, ttl_seconds=3600)

    print(f"[+] Loaded {len(documents)} documents, created {len(all_chunks)} chunks, indexed {len(vocab)} terms.")
    print(f"[+] Active document revisions: {state.retriever.latest_revisions}")


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    answer: str
    source_documents: List[str]
    normalized_query: str
    latency_ms: float
    cached: bool = False


@app.get("/", response_class=HTMLResponse)
async def serve_ui(request: Request):
    """Serves the professional slate-gray plant dashboard."""
    return templates.TemplateResponse(request=request, name="index.html")


@app.get("/api/health")
async def health_check():
    """Health check reporting indexed chunks and cache telemetry."""
    return {
        "status": "online",
        "plant": "Kaveri Precision Components Pvt. Ltd. - Hosur Plant",
        "chunks_indexed": len(state.all_chunks),
        "cached_queries": state.cache.size() if state.cache else 0,
        "latest_revisions": {k: v[1] for k, v in state.retriever.latest_revisions.items()}
    }


@app.post("/api/chat", response_model=ChatResponse)
async def chat_endpoint(req: ChatRequest):
    """
    Standard JSON Chat Endpoint:
    1. Checks In-Memory LRU Cache for O(1) instantaneous hit.
    2. Runs Layer 1 Typo Fixer & Normalizer.
    3. Retrieves top verified context passages via BM25 Inverted Index.
    4. Queries Grounded LLM Client with strict zero-hallucination constraint.
    5. Caches the result in memory.
    """
    start_time = time.time()
    raw_query = req.message.strip()

    if not raw_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    # Step 1: Normalization
    normalized_query = state.normalizer.normalize_query(raw_query)

    # Step 2: Check LRU Cache (O(1))
    cached_entry = state.cache.get(normalized_query)
    if cached_entry:
        elapsed_ms = round((time.time() - start_time) * 1000, 2)
        return ChatResponse(
            answer=cached_entry["answer"],
            source_documents=cached_entry["source_documents"],
            normalized_query=normalized_query,
            latency_ms=elapsed_ms,
            cached=True
        )

    # Step 3: BM25 Inverted Index Retrieval with Porter Stemming
    matched_chunks = state.retriever.retrieve(normalized_query, top_k=4)

    # Step 4: Grounded LLM Generation
    result = state.llm_client.generate_response(
        user_query=normalized_query,
        context_chunks=matched_chunks
    )

    elapsed_ms = round((time.time() - start_time) * 1000, 2)

    # Step 5: Save into LRU Cache (ONLY cache valid responses, never errors or timeouts)
    ans = result.get("answer", "")
    if ans and not ans.startswith("System") and not ans.startswith("The upstream AI service"):
        state.cache.put(normalized_query, {
            "answer": result["answer"],
            "source_documents": result["source_documents"]
        })

    return ChatResponse(
        answer=result["answer"],
        source_documents=result["source_documents"],
        normalized_query=normalized_query,
        latency_ms=elapsed_ms,
        cached=False
    )


@app.post("/api/chat/stream")
async def chat_stream_endpoint(req: ChatRequest):
    """
    Streaming Endpoint (Server-Sent Events / SSE):
    Streams generated tokens in real time so the supervisor sees words immediately.
    """
    raw_query = req.message.strip()
    if not raw_query:
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    normalized_query = state.normalizer.normalize_query(raw_query)

    # Check cache first
    cached_entry = state.cache.get(normalized_query)
    if cached_entry:
        async def cached_streamer() -> AsyncGenerator[str, None]:
            data = {
                "token": cached_entry["answer"],
                "done": True,
                "source_documents": cached_entry["source_documents"],
                "cached": True
            }
            yield f"data: {json.dumps(data)}\n\n"
        return StreamingResponse(cached_streamer(), media_type="text/event-stream")

    # Retrieve context
    matched_chunks = state.retriever.retrieve(normalized_query, top_k=4)

    async def event_generator() -> AsyncGenerator[str, None]:
        # Generate full answer from grounded model
        result = state.llm_client.generate_response(normalized_query, matched_chunks)
        full_text = result["answer"]
        sources = result["source_documents"]

        # Cache valid responses only
        if full_text and not full_text.startswith("System") and not full_text.startswith("The upstream"):
            state.cache.put(normalized_query, {
                "answer": full_text,
                "source_documents": sources
            })

        # Stream tokens in chunks to client
        words = full_text.split(" ")
        for i, word in enumerate(words):
            chunk = word + (" " if i < len(words) - 1 else "")
            payload = {
                "token": chunk,
                "done": (i == len(words) - 1),
                "source_documents": sources if i == len(words) - 1 else []
            }
            yield f"data: {json.dumps(payload)}\n\n"

    return StreamingResponse(event_generator(), media_type="text/event-stream")
