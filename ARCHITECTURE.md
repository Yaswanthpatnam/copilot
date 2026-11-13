# System Architecture & Technical Flow

Detailed technical architecture, execution flow, data structure analysis, and reviewer verification guide for the **Manufacturing Plant AI Copilot**.

---

## 1. High-Level Architecture (The Big Picture)

```
[ Supervisor (Mobile Phone / Desktop Browser) ]
                       │
                       │ HTTP / WebSocket (fetch streaming)
                       ▼
[ Presentation Layer: FastAPI Static / Jinja2 Web UI ]
                       │
                       │ JSON Payload: {"message": "..."}
                       ▼
         [ Layer 1: Normalizer & Typo Fixer ]
         • Trims whitespace & formatting
         • Normalizes codes (e.g. 'al104' -> 'AL-104')
         • DP Levenshtein Distance for minor slips
                       │
                       ▼
             [ Layer 2: In-Memory LRU Cache ] ──(Cache Hit < 1ms)──► Return Instant Answer
                       │
                       │ (Cache Miss)
                       ▼
     [ Layer 3: Inverted Index & BM25 with Porter Stemming ]
     • Tokenizes query into morphological root stems
     • Instant O(1) Hash Map candidate lookup (No linear text scan)
     • Active Revision Filter: Suppresses superseded Rev 03
     • BM25 Probabilistic Ranking + Term-Coverage multiplier
                       │
                       │ Top 3-4 Verified Document Chunks
                       ▼
     [ Layer 4: Grounded LLM Client (Dual-Engine) ]
     • Primary: Groq LPU (qwen3.8-27b) -> 300ms–500ms latency
     • Fallback: Gemini API (gemini-3.5-flash / 3.6-flash)
     • Generalized Operational Prompt: Strict grounding + Anti-Hallucination
                       │
                       ▼
  [ Layer 5: Server-Sent Events (SSE) Token Streamer ]
  • Streams tokens word-by-word into client UI
  • Updates in-memory LRU Cache with verified response
```

---

## 2. In-Detail Step-by-Step Execution Flow

### Step 1: User Query Submission
- **Component:** `templates/index.html` (Client Browser)
- The supervisor types a question (e.g., *"What is the coolant concentration for the TX-200 CNC?"*) or taps a quick action button.
- JavaScript executes `fetch("/api/chat/stream", { method: "POST", body: JSON.stringify({ message: queryText }) })`.
- Initializes an asynchronous `ReadableStream` reader to receive live tokens.

### Step 2: Request Entry & Fast-Path In-Memory Cache Check ($O(1)$)
- **Component:** `main.py` (`chat_stream_endpoint`) & `backend/cache.py` (`QueryCache`)
- `QueryCache` is built using Python's `collections.OrderedDict` (a hybrid Hash Map + Doubly Linked List).
- **Time Complexity:** Average **$O(1)$** lookup.
- If the normalized query exists and has not expired (TTL = 1 hour), the endpoint immediately yields the cached response in **$< 1\text{ms}$** with zero network or LLM compute overhead.

### Step 3: Layer 1 Typo Correction & Normalization
- **Component:** `backend/normalizer.py` (`TextNormalizer`)
- Standardizes hyphenation for technical codes: `al104` $\rightarrow$ `AL-104`, `tx200` $\rightarrow$ `TX-200`, `bh220` $\rightarrow$ `BH-220`.
- Executes Dynamic Programming Levenshtein Distance:
  $$\text{dp}[i][j] = \min(\text{delete}, \text{insert}, \text{replace})$$
  Compares query tokens against dynamically indexed domain vocabulary. Minor keyboard slips are repaired before search.

### Step 4: Tokenization & Porter Stemming
- **Component:** `backend/retrieval.py` (`PorterStemmer` & `InvertedIndexRetriever.tokenize`)
- Query text is broken into lowercase tokens, filtering common grammatical stopwords (`and`, `the`, `is`, `for`).
- Runs the Porter Stemmer algorithm:
  - `"cooling"` $\rightarrow$ `"cool"`
  - `"running"` $\rightarrow$ `"run"`
  - `"inspected"` $\rightarrow$ `"inspect"`
  - Suffix stripping enables true semantic root matching without fuzzy false-positives.

### Step 5: Inverted Index Candidate Retrieval & BM25 Scoring
- **Component:** `backend/retrieval.py` (`InvertedIndexRetriever.retrieve`)
- **Data Structure:** An Inverted Index Hash Map (`self.index: Dict[stem, List[Tuple[chunk_idx, tf]]]`).
- **Algorithm:** For each stemmed query token, Python hashes the token string in $O(1)$ time to fetch its postings list.
- **Active Document Revision Governance:** Automatically checks document metadata. Chunks from `QC-SOP-014 Rev 03` are excluded because `Rev 04` is detected as the active revision.
- **Scoring (BM25):**
  $$\text{Score}(D, Q) = \sum_{t \in Q} \text{IDF}(t) \cdot \frac{\text{TF}(t, D) \cdot (k_1 + 1)}{\text{TF}(t, D) + k_1 \cdot \left(1 - b + b \cdot \frac{|D|}{\text{avgdl}}\right)} \times \left(1 + \frac{\text{matching\_terms}}{|Q|}\right)$$
- The top 3–4 chunks with the highest scores are passed to the prompt generator.

### Step 6: Grounded Prompt Assembly & LLM Generation
- **Component:** `backend/llm_client.py` (`GroundedLLMClient`)
- Combines the user query with the retrieved document excerpts into a strictly grounded context.
- **Zero Hardcoded Scenarios:** The model prompt contains no pre-scripted alarm numbers or emotion rules. It operates under generalized technical reasoning:
  - If information is in the excerpts: Provide clear, actionable instructions with citations.
  - If the user expresses anxiety or asks for briefing guidelines: Synthesize the excerpts into clear, calm worker briefing steps.
  - If information is completely outside plant operations: State strictly: *"The provided documents do not contain information to answer this question."*
- **Primary Engine (Groq LPU):** Calls `https://api.groq.com/openai/v1/chat/completions` using model `qwen/qwen3.8-27b`. Generates response in **~300ms to 500ms**.
- **Failover Engine (Gemini API):** If Groq encounters network issues, automatically fails over to `gemini-3.5-flash`.

### Step 7: Streaming Response Delivery & Cache Storage
- **Component:** `main.py` (`chat_stream_endpoint`) & `templates/index.html`
- Uses `StreamingResponse(media_type="text/event-stream")` to yield tokens word-by-word.
- The supervisor's screen renders text in real time.
- When generation finishes, valid answers are saved to `QueryCache` so repeated queries return in $< 1\text{ms}$.

---

## 3. Data Structures & Algorithmic Complexity

| Subsystem | Data Structure Used | Search Time Complexity | Space Complexity | Why This Choice |
|---|---|---|---|---|
| **In-Memory Cache** | `collections.OrderedDict` (Hash Map + Doubly Linked List) | $O(1)$ average | $O(C)$ ($C = 256$ entries) | Immediate response on repeated questions; $O(1)$ LRU eviction. |
| **Inverted Index** | `defaultdict(list)` (Hash Map of Postings Lists) | $O(1)$ per query term | $O(V + N)$ ($V = \text{vocabulary}$, $N = \text{postings}$) | Avoids $O(N)$ linear scans across documents; searches candidate chunks instantly. |
| **Typo Repair** | 2D Dynamic Programming Array (`dp[m][n]`) | $O(|s_1| \times |s_2|)$ | $O(|s_1| \times |s_2|)$ | Solves keyboard slips and code typos with minimum edit distance. |
| **Morphological Stemmer** | Algorithmic State Machine (Porter Stemmer) | $O(L)$ where $L$ is word length | $O(1)$ auxiliary | Unifies word variants (e.g. `precaution`/`precautions`) with zero external library overhead. |
| **Document Chunker** | Linear Regex Partitioning | $O(T)$ where $T$ is text length | $O(T)$ | Divides PDFs at official section boundaries (`1. Purpose`, `4. Schedule`). |
