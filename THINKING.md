# THINKING.md — Manufacturing Plant AI Copilot

Strategic thinking, user modeling, AI adversarial critique, layered engineering decisions, and final reflections for the **Manufacturing Plant AI Copilot** developed for **Kaveri Precision Components Pvt. Ltd. (Hosur Plant)**.

---

## 🎥 Video Demonstrations (Screen Recordings)
- 💻 **Laptop Interface Walkthrough:** [Watch Google Drive Screen Recording](https://drive.google.com/file/d/1KKh0hggzugH0GukFEcvTBbWzHcv0vGOg/view?usp=sharing)
- 📱 **Mobile Phone over Wi-Fi (LAN):** [Watch Google Drive Mobile Recording](https://drive.google.com/file/d/1_-Sj5JyNpWR1b7AfAlTILsVNuCOkEOtb/view?usp=sharing)

---

## 1. Understand the User

### Who is the Supervisor?
A shop-floor supervisor at a precision automotive manufacturing plant like Kaveri Precision Components carries immense, multifaceted responsibility. They are not sitting at a quiet desk—they are constantly on their feet in a loud, chaotic environment managing:
1. **Worker Management & Attendance:** Tracking workers as they arrive at the plant, taking morning shift attendance, managing shift rotations, and overseeing pay cycles.
2. **Work Direction & Daily Precautions:** Briefing operators at the start of each shift on what to do, what *not* to do, the required production pace, and mandatory safety precautions.
3. **Machine & Process Mastery:** To guide workers and enforce precautions, the supervisor must know how every machine operates—the CNC turning centres (`TX-200`, `CNC-04` through `CNC-09`), mechanical presses, and hydraulic power packs. They need to understand what each machine does and the exact parameters required to run them safely.
4. **Learning & Enforcing SOP Manuals:** Memorizing and consulting voluminous Standard Operating Procedures across machine maintenance (`MNT-MAN-CNC-02`), safety/LOTO (`SAF-SOP-003`), and quality inspection (`QC-SOP-014`).
5. **Quality Inspection & Defect Prevention:** Inspecting manufactured components (such as the `BH-220` bearing housing) and raw materials to make quick pass/fail calls before parts move down the line.

### What Frustrates Them Today?
The supervisor lives a **chaotic experience**. Juggling workers, machine breakdowns, attendance, and quality inspections simultaneously creates cognitive overload. 

When an unexpected alarm triggers or a supplier delivers raw materials, they don't have time to walk across the factory floor, flip through a 40-page printed PDF manual in a binder, or squint at tiny PDF text on a mobile phone. Under this high pressure, supervisors are often forced to make snap decisions based on memory or assumptions—which can lead to scrapped production lots, machine damage, or serious worker injuries.

---

## 2. User Journey

### Why an AI Copilot?
Developing an AI copilot to assist the shop-floor supervisor is an intelligent way to provide constant support, verified knowledge, and operational assurance. When managing multiple crises at once, having a tool that instantly surfaces the right procedure eliminates guesswork and prevents costly mistakes.

### What Could Go Wrong?
Deploying an AI assistant on a live manufacturing floor carries serious operational risks if not built with strict guardrails:
- **Hallucinations & Bad Data:** If the AI is not constrained by verified plant SOPs, it could fabricate an incorrect chemical concentration, wrong hydraulic pressure, or unsafe clearance instruction—leading to equipment disaster or worker injury.
- **Obsolete Document Usage:** Manufacturing procedures evolve constantly. If the system references superseded revisions (e.g., using `QC-SOP-014 Rev 03`'s old 5-sample rule instead of active `Rev 04`'s 32-sample rule), the plant will fail critical customer quality audits (IATF 16949 / ISO 9001).
- **Communication & Input Friction:** Supervisors on a noisy shop floor may type with dirty fingers, use casual phrasing, or make spelling errors (`al104`, `chick climbing pressure`). If the tool only accepts textbook queries, it fails when needed most.
- **Panic & High Stress Situations:** When an alarm siren goes off, the supervisor might not even know what the alarm is or have the code handy. They may just hear the siren or feel overwhelmed. The AI must be capable of de-escalating panic, presenting common alarm characteristics, and guiding the user step-by-step.

### Step-by-Step User Journey

```
[06:30 AM — Morning Shift Kickoff]
Supervisor arrives at Hosur Plant. 20 operators assemble.
  │
  ▼
Supervisor opens AI Copilot on mobile phone:
"Workers are coming. It is morning shift. What precautions should I tell them?"
  │
  ▼
Copilot synthesizes daily pre-start checks from MNT-MAN-CNC-02 (pressures, lube, chips)
and LOTO reminders from SAF-SOP-003 into an instant 4-point briefing.
Supervisor conducts the toolbox talk in 2 minutes with complete confidence.
  │
  ▼
[10:15 AM — Sudden Machine Breakdown & High Anxiety]
Machine stops with a loud warning siren. Operator panics. Supervisor feels overwhelmed:
"dont know what to do, here there are too large machines and lot of workers i need to manage even i can here alarms"
  │
  ▼
Copilot detects the panic, offers calm leadership guidance, provides a structured table
of all 5 known CNC alarms (AL-101, AL-104, AL-210, AL-305, AL-412) with immediate actions,
and asks clarifying questions to narrow down the specific machine.
  │
  ▼
[10:18 AM — Typo / Casual Language Handling]
Supervisor checks the panel and types casually with a typo:
"what is the chick climbing pressure ?"
  │
  ▼
Layer 1 Normalizer detects "chick climbing" as a typo for "Chuck Clamping Pressure".
Copilot returns 2.0 – 2.5 MPa with the safety check for AL-210.
Issue resolved in 90 seconds.
  │
  ▼
[02:00 PM — Incoming Material Inspection]
Subcontractor delivers 800 machined BH-220 bearing housings.
Inspector asks for the outer diameter tolerance and sample size.
  │
  ▼
Supervisor asks Copilot: "What is the outer diameter tolerance for the BH-220 bearing housing?"
  │
  ▼
Active Revision Filter ensures obsolete Rev 03 is excluded and pulls active Rev 04:
"Outer diameter tolerance is ±0.050 mm (Nominal: 90.000 mm, Digital Caliper).
 Lot size 501–3200 requires 32 samples (Normal Inspection, AQL 1.0)."
Shipment inspected with 100% compliance.
```

---

## 3. AI Challenge (Skeptical Product Manager & Plant Manager Critique)

To test the robustness of this user journey, we had an AI persona act as a skeptical **Automotive Plant Quality & Safety Manager** to challenge our thinking.

### Key Excerpts from the Adversarial Challenge:

> **Skeptical Plant Manager:**  
> *"Your user journey assumes the supervisor behaves like an office worker asking textbook questions. In our plant, supervisors type on grease-smudged phone screens, make typos like 'chick climbing pressure' instead of 'chuck clamping', or type 'AL104' without hyphens. If your system depends on exact keyword matching, it's going to fail right when machines are down."*

> **Our Response:**  
> *"That's why we built Layer 1: Normalizer & Typo Fixer using Dynamic Programming Levenshtein Distance and domain vocabulary matching. If a user types 'what is the chick climbing pressure ?', the system automatically repairs it to 'Chuck Clamping Pressure', retrieves the verified 2.0–2.5 MPa parameter, and answers accurately in under 1.2 seconds."*

> **Skeptical Plant Manager:**  
> *"What if an alarm is wailing and the supervisor doesn't even know the code? In panic situations, people type fragmented sentences like 'dont know what to do, machines are loud and workers are waiting'. A standard RAG pipeline will return 0 results because there is no matching keyword."*

> **Our Response:**  
> *"We eliminated rigid keyword prompt scripting. When a user expresses confusion or hears alarms without a code, our contextual reasoning layer empathetically reassures the supervisor, lays out the 5 standard TX-200 alarm codes in a clear triage table (AL-101 through AL-412), offers 3 actionable floor management steps, and asks targeted clarifying questions."*

> **Skeptical Plant Manager:**  
> *"In our plant folder, we have QC-SOP-014 Rev 03 and Rev 04 sitting side by side. Rev 03 specifies inspecting 5 samples, while active Rev 04 mandates 32 samples. If an AI retrieves the old Rev 03, we ship defective automotive parts and fail customer quality audits. How do you prevent that?"*

> **Our Response:**  
> *"We designed an Active Document Revision Filter inside the Inverted Index. During PDF parsing, our system extracts document IDs and revision numbers. It dynamically tracks the latest active revision (`QC-SOP-014 Rev 04`) and suppresses obsolete chunks from `Rev 03` before ranking, preventing regulatory non-compliance."*

### Reflection on the Critique:
- **What We Agreed With:** The critique was right that real shop-floor interactions are messy, typo-ridden, and emotionally tense, and that vector databases frequently mix old and new SOP revisions.
- **What We Disagreed With:** The belief that we needed hardcoded `if/else` scripts for every scenario. Hardcoding breaks as soon as phrasing changes. A generalized contextual prompt grounded strictly in verified excerpts is far more resilient.
- **What We Changed:**
  1. Added the **DP Levenshtein Normalizer** (`backend/normalizer.py`) to handle spelling slips.
  2. Implemented the **Porter Stemming Algorithm** (`backend/retrieval.py`) so word roots (`precaution` / `precautions`) match automatically.
  3. Integrated **Active Document Revision Filtering** to automatically suppress superseded revisions.

---

## 4. The Improvement Added & Why We Chose It

### The Chosen Improvement: **Multi-Layered Shop-Floor Architecture (Normalization + Stemmed Inverted Index + Active Revision Governance)**

#### Why We Chose It:
1. **The Copilot Must Not Be Fragile:**  
   Most naive AI agents only generate answers when the question is phrased perfectly. On the shop floor, supervisors make spelling mistakes, misspell alarm codes, and communicate casually under stress. Layer 1 Normalization ensures that imperfect inputs still produce accurate, grounded answers.
2. **Audit Compliance (Zero Toleration for Superseded SOPs):**  
   In precision engineering (ISO 9001 / IATF 16949), inspecting components using obsolete standards is a major non-conformance. Our Active Revision Filter guarantees that superseded documents like `QC-SOP-014 Rev 03` are never surfaced when `Rev 04` is active.
3. **Linguistic Precision Without Embedding Bloat:**  
   The Porter Stemming algorithm ensures that morphological variants (`precautions`, `inspecting`, `checked`) map to common linguistic roots without the heavy compute or latency of dense vector embeddings.

---

## 5. Final Reflection

### The System Layers We Built (Simple Brief):
1. **Layer 1: Normalizer & Typo Fixer:** Cleans inputs, standardizes machine codes (`AL104` $\rightarrow$ `AL-104`), and uses DP Levenshtein distance to fix typos (`chick climbing` $\rightarrow$ `chuck clamping`).
2. **Layer 2: Fast-Path In-Memory Cache:** Built on `collections.OrderedDict` with LRU eviction ($O(1)$). Delivers repeated answers in **$< 50\text{ms}$** with zero API cost.
3. **Layer 3: Inverted Index & BM25 with Porter Stemming:** Fast keyword retrieval with root stemming and active document revision filtering.
4. **Layer 4: Dual-Engine Grounded Inference:** Primary Groq LPU (`qwen/qwen3.8-27b`) for sub-second answers (~400ms); Google Gemini (`gemini-3.5-flash`) as automatic failover.
5. **Layer 5: Server-Sent Events (SSE) Token Streamer:** Streams tokens progressively to the mobile/desktop UI.

### Why We Used a Cloud Model:
Running large local LLMs (like 7B+ models) locally was not feasible because my laptop hardware and RAM constraints couldn't bear the resource load. Using a fast, lightweight cloud API—specifically **Groq's LPU**—gave us instant inference without heating up the laptop or consuming system memory.

### Difficult Challenges Faced & How We Handled Them:
1. **API Rate Limiting & Latency Bottlenecks:**  
   Initially, testing with Google Gemini free tier hit frequent `429 Too Many Requests` errors and took **56+ seconds** for a single response.  
   *Fix:* Switched primary inference to **Groq LPU (`qwen/qwen3.8-27b`)**, dropping latency from 56,000ms down to **~400ms**. Kept Gemini strictly as a secondary fallback.
2. **Eliminating Hardcoded `if/else` Logic:**  
   Early prototypes tried hardcoding answers for specific alarm questions. This was brittle. We completely eliminated hardcoding and replaced it with a generalized operational prompt that understands user urgency and formats answers dynamically while staying strictly grounded in verified excerpts.
3. **Cache Invalidation & Error Contamination:**  
   Early testing showed that temporary network timeout errors were accidentally getting stored in the in-memory cache.  
   *Fix:* Added strict negative cache guards in `main.py`—only valid, verified SOP answers are cached.
4. **Local Network & Port Conflicts:**  
   Encountered `[WinError 10048]` socket errors when testing repeatedly.  
   *Fix:* Built auto-port fallback in `run_server.py` and implemented UDP socket LAN discovery so mobile devices on the same Wi-Fi connect instantly.

### What We'd Build Next:
- Hands-free voice speech-to-text (Whisper) for noisy shop-floor conditions.
- Direct SCADA/PLC connector (OPC-UA) to auto-detect alarm codes directly from the CNC machines.
- WhatsApp / Telegram bot interface for supervisors who prefer messaging apps on the move.

### What We'd Ask the Customer:
- Are machine alarms logged digitally in an MES or written on manual shift logs?
- Which alarms can operators clear independently, and which strictly require a maintenance technician?
