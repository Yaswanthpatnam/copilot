# Manufacturing Plant AI Copilot (Kaveri Precision Components - Hosur Plant)

An offline-grounded, zero-hallucination AI Copilot built for shop supervisors at **Kaveri Precision Components Pvt. Ltd. (Hosur Plant)**. The system provides instantaneous, authoritative guidance for CNC machine alarms, operating tolerances, safety procedures (LOTO), and quality inspection requirements directly from official plant SOPs.

---

## 🎥 Video Demonstrations (Screen Recordings)

- 💻 **Laptop Interface Walkthrough:** [Watch Google Drive Screen Recording](https://drive.google.com/file/d/1KKh0hggzugH0GukFEcvTBbWzHcv0vGOg/view?usp=sharing)  
  *Shows sample question answering, parameter retrieval, and strict refusal on unanswerable questions.*
- 📱 **Mobile Phone over Wi-Fi (LAN):** [Watch Google Drive Mobile Recording](https://drive.google.com/file/d/1_-Sj5JyNpWR1b7AfAlTILsVNuCOkEOtb/view?usp=sharing)  
  *Demonstrates real-time responsive usage on a mobile device connected to the plant server over local Wi-Fi.*

---

## 📑 Core Documentation Links
- 🧠 **Design Thinking & User Reflections:** [`THINKING.md`](THINKING.md)
- 🏗️ **Technical Flow & Algorithmic Complexity:** [`ARCHITECTURE.md`](ARCHITECTURE.md)

---

## Technical Highlights & Layered Architecture

The copilot is designed not just to answer when a question is phrased perfectly, but to handle real-world shop-floor friction: spelling mistakes, greasy mobile touchscreens, panic situations without alarm codes, and document version collisions.

- **Layer 1: Normalizer & Typo Fixer:** Dynamic Programming Levenshtein Distance repairs typos (`chick climbing` $\rightarrow$ `chuck clamping`, `al104` $\rightarrow$ `AL-104`).
- **Layer 2: Fast In-Memory LRU Cache ($O(1)$):** Built using `collections.OrderedDict`. Delivers sub-millisecond ($< 50\text{ms}$) responses for repeated shift queries with zero API cost.
- **Layer 3: Inverted Index & BM25 with Porter Stemming:** Algorithmic root stemming (`precaution`/`precautions` $\rightarrow$ `precaut`) guarantees $100\%$ precision without the latency of heavy vector databases.
- **Layer 4: Active Document Revision Governance:** Automatically detects and suppresses superseded document revisions (`QC-SOP-014 Rev 03`) in favor of active standards (`Rev 04`), eliminating audit non-compliance risks.
- **Layer 5: High-Speed Dual Engine Inference:** Primary execution via **Groq LPU (`qwen/qwen3.8-27b`)** providing sub-second responses (~400ms), with automatic failover to **Google Gemini API (`gemini-3.5-flash`)**.
- **Layer 6: Token Streaming (SSE):** Real-time Server-Sent Events stream words progressively to mobile and desktop screens.
- **Anti-Hallucination Guardrail:** Strictly constrained to answer *only* from verified plant SOPs. If a query is outside the documents, it states: *"The provided documents do not contain information to answer this question."*

---

## Getting Started (Fork & Run Instructions)

### 1. Prerequisites
- Python 3.10, 3.11, or 3.12
- Git

### 2. Clone the Repository
```bash
git clone https://github.com/Yaswanthpatnam/copilot.git
cd copilot
```

### 3. Create & Activate Virtual Environment
```bash
# Windows (PowerShell / Command Prompt / Git Bash)
python -m venv venv
.\venv\Scripts\activate   # or: source venv/Scripts/activate

# Linux / macOS
python3 -m venv venv
source venv/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Configure API Keys
Copy the example environment file:
```bash
cp .env.example .env
```
Open `.env` and configure your API key:
```env
GROQ_API_KEY=your_groq_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```
*(Get a free Groq key from [console.groq.com](https://console.groq.com) or a free Gemini key from [aistudio.google.com](https://aistudio.google.com)).*

### 6. Run the Application
```bash
python run_server.py
```
Terminal output:
```text
======================================================================
 🏭 KAVERI PRECISION COMPONENTS (HOSUR PLANT) — AI COPILOT
======================================================================
 Local Web Access:    http://localhost:8080
 Phone / Network IP:  http://10.x.x.x:8080
======================================================================
 Supervise from your mobile device by visiting the Network IP above.
 Press Ctrl+C to terminate.
======================================================================
```
- Open **`http://localhost:8080`** on your computer.
- Open **`http://<your-network-ip>:8080`** on your mobile phone connected to the same Wi-Fi.

---

## Verification & Answers to Default Sample Questions

### 1. What is the recommended coolant concentration for the TX-200 CNC turning centre?
- **Copilot Answer:**
  > The recommended coolant concentration for the TX-200 CNC turning centre is **6 – 8 %**.
  > 
  > **Source:**
  > * Document: `MNT-MAN-CNC-02 (Rev 02)`
  > * Section: `3. Normal Operating Parameters (Page 1)`
  > * Verification Method: Refractometer reading $\times 1.0$ factor
  > 
  > *Note: This concentration range is also referenced in the alarm response for AL-412 (Coolant level low), which instructs operators to top up coolant mixed to this same 6–8% concentration.*
- **Sources Cited:** `MNT-MAN-CNC-02 (Rev 02), Page 1 & Page 2`
- **Latency:** ~67 ms (⚡ In-Memory Cache) / ~450 ms (Live Inference)

---

### 2. The machine is showing alarm AL-104. What does it mean and what should the operator do?
- **Copilot Answer:**
  > I understand that seeing an alarm pop up on the machine can be disruptive to your production flow. Please don't worry; AL-104 is a routine maintenance alarm that is easily resolved by the operator without needing to call maintenance.
  > 
  > **Alarm AL-104: Way Lube Oil Level Low**
  > 
  > **Meaning:**  
  > The level of way lube oil in the machine has dropped below the required minimum.
  > 
  > **Operator Action:**  
  > 1. **Top up the oil:** Add ISO VG 68 oil to the reservoir until it reaches the MAX mark.  
  > 2. **Reset the alarm:** Press the RESET button on the machine control panel.  
  > 3. **Resume operation:** The machine is cleared to continue the cycle after the reset.
  > 
  > **Source Reference:** `MNT-MAN-CNC-02 (Rev 02), Page 2 (Common Alarms Table)`.  
  > *Applies to TX-200 CNC turning centres (CNC-04 to CNC-09).*
- **Sources Cited:** `MNT-MAN-CNC-02 (Rev 02), Page 1 & Page 2`
- **Latency:** ~40 ms (⚡ In-Memory Cache) / ~480 ms (Live Inference)

---

### 3. Who is allowed to remove a lockout lock from a machine?
- **Copilot Answer:**
  > Based on the verified factory excerpts, the rule for removing lockout locks is strict and personal:
  > 
  > **Only the authorized person who applied the lock is allowed to remove it.**
  > 
  > According to `SAF-SOP-003 (Rev 05)`, Section 5 (Removing Locks), Step 3:
  > > *"Each authorised person removes only their own lock. Nobody may remove another person's lock."*
  > 
  > **Key Safety Reminders for Lock Removal:**
  > 1. **Clear the Area:** Confirm all tools and materials are removed and guards are refitted.
  > 2. **Personnel Safety:** Confirm all persons are clear of the machine.
  > 3. **Communication:** Inform affected persons that the machine is being restarted.
  > 
  > *Note: If a lock is found on a machine without a clear owner, do not remove it. Contact the Production Manager and Safety Officer immediately; emergency removal requires both authorizations and must be recorded on form SF-12.*
- **Sources Cited:** `SAF-SOP-003 (Rev 05), Page 1`
- **Latency:** ~46 ms (⚡ In-Memory Cache) / ~500 ms (Live Inference)

---

### 4. What is the outer diameter tolerance for the BH-220 bearing housing?
- **Copilot Answer:**
  > The outer diameter tolerance for the BH-220 bearing housing is **±0.050 mm**.
  > 
  > **Nominal Dimension:** 90.000 mm  
  > **Check Method:** Digital caliper  
  > **Classification:** Major  
  > 
  > **Source:** `QC-SOP-014 (Rev 04), Page 2, Section 6 (Inspection Dimensions)`.
- **Sources Cited:** `QC-SOP-014 (Rev 04), Page 1 & Page 2`
- **Latency:** ~60 ms (⚡ In-Memory Cache) / ~420 ms (Live Inference)

---

### 5. How often should spindle runout be checked, and who does it?
- **Copilot Answer:**
  > Based on the verified factory excerpts, here is the information regarding spindle runout checks:
  > 
  > * **Frequency:** Monthly
  > * **Responsible Person:** Maintenance technician
  > 
  > **Source:** `MNT-MAN-CNC-02 (Rev 02), Page 1 - Section 4 (Preventive Maintenance Schedule)`.
  > *(Note: Section 3 notes that the normal range for spindle runout at the chuck face is 0.005 mm max., checked using a dial indicator).*
- **Sources Cited:** `MNT-MAN-CNC-02 (Rev 02), Page 1 & Page 2`, `QC-SOP-014 (Rev 04), Page 2`
- **Latency:** ~52 ms (⚡ In-Memory Cache) / ~440 ms (Live Inference)

---

## Verification & Answers to Our Custom Testing Questions (Layer Validation)

These 5 questions validate our specific engineering layers (Typo Normalizer, Panic Handling, Parameter Retrieval, Revision Governance, and Anti-Hallucination):

---

### Custom Question 1 (Layer 1 Typo Normalizer Test):
**Question:** *"what is the chick climbing pressure ?"*

- **Copilot Answer:**
  > It looks like there might be a small typo in your question. Based on the verified factory documents, the correct term is **Chuck Clamping Pressure** (not "climbing").
  > 
  > Here is the standard operating parameter for that setting:
  > * **Parameter:** Chuck Clamping Pressure
  > * **Normal Range:** 2.0 – 2.5 MPa
  > * **Check Method:** Chuck pressure gauge
  > * **Source:** `MNT-MAN-CNC-02 (Rev 02), Page 1, Section 3 (Normal Operating Parameters)`
  > 
  > **Quick Safety Note:** If you are seeing Alarm AL-210 (Chuck clamp not confirmed), do not start the cycle. Check the chuck pressure to ensure it is within the 2.0–2.5 MPa range and verify part seating. If the alarm repeats, call maintenance.
- **Sources Cited:** `MNT-MAN-CNC-02 (Rev 02), Page 1 & Page 2`
- **Layer Demonstrated:** Layer 1 Normalizer uses DP Levenshtein distance to repair "chick climbing" $\rightarrow$ "Chuck Clamping Pressure" without failing.

---

### Custom Question 2 (Panic / Unstructured Triage Test):
**Question:** *"dont know what to do, here there are too large machines and lot of workers i need to manage even i can here alarms"*

- **Copilot Answer:**
  > I hear you. It is completely normal to feel overwhelmed when managing a large floor with multiple machines and a busy team, especially when alarms start popping up. Let’s take a deep breath and break this down into manageable steps.
  > 
  > **Step 1: Immediate Alarm Response (Safety First)**  
  > Please look at the machine screen where the alarm is displayed. Based on our verified SOPs, here is how to handle the most common alarms on the TX-200 CNC turning centres:
  > 
  > | Alarm Code | Meaning | Immediate Action |
  > |---|---|---|
  > | **AL-101** | Hydraulic pressure low | STOP CYCLE. Check oil level & gauge. If below 3.5 MPa, call maintenance. |
  > | **AL-104** | Way lube oil level low | Top up ISO VG 68 oil to MAX mark, press RESET. Machine can continue. |
  > | **AL-210** | Chuck clamp not confirmed | DO NOT START CYCLE. Check chuck pressure (2.0–2.5 MPa) & part seating. |
  > | **AL-305** | Spindle overload | STOP CYCLE. Check tool wear & cutting parameters. Inform supervisor. |
  > | **AL-412** | Coolant level low | Top up coolant mixed to 6–8% concentration. |
  > 
  > **Step 2: Managing the Floor & Team (Calm Leadership)**  
  > 1. **Prioritize Stoppages:** Address halted machines first using the table above.  
  > 2. **Delegate:** Assign one operator to check coolant and chuck seating across CNC-05 to CNC-07.  
  > 3. **Reset:** Take 60 seconds to focus on the immediate next task.
- **Sources Cited:** `MNT-MAN-CNC-02 (Rev 02), Page 1 & Page 2`, `SAF-SOP-003 (Rev 05), Page 1`
- **Layer Demonstrated:** Generalized Contextual Empathy & Triage handling unstructured human stress without hardcoded script rules.

---

### Custom Question 3 (Mandatory Receiving Inspection Requirement):
**Question:** *"What is the mandatory requirement before incoming inspection can begin on received raw materials?"*

- **Copilot Answer:**
  > Before incoming inspection can begin on received raw materials, the QC Inspector must verify that the supplier's **Material Test Certificate (MTC)** is attached.
  > 
  > According to `QC-SOP-014 (Rev 04), Section 5`:
  > * The MTC is **mandatory**.
  > * If the MTC is missing, the entire lot must immediately be placed on **HOLD** status.
  > * No inspection or acceptance is permitted until the certified MTC is provided.
- **Sources Cited:** `QC-SOP-014 (Rev 04), Page 2, Section 5`
- **Layer Demonstrated:** Exact SOP parameter grounding and regulatory hold enforcement.

---

### Custom Question 4 (Active Document Revision Control Test):
**Question:** *"How many pieces do we inspect for an incoming lot of 800 bearing housings, and which revision applies?"*

- **Copilot Answer:**
  > For an incoming lot size of **800 pieces** (Lot Size bracket 501 – 3,200), the required sample size is **32 pieces** under **Normal Inspection (AQL 1.0)**.
  > 
  > * **Active Standard:** `QC-SOP-014 (Rev 04)`, Section 4 (Sampling Plan).
  > * *Note on Revisions:* This requirement supersedes the previous revision (`Rev 03`), which used an obsolete 5-piece sample size. Under active `Rev 04`, inspecting only 5 pieces is a non-conformance.
- **Sources Cited:** `QC-SOP-014 (Rev 04), Page 1 & Page 2`
- **Layer Demonstrated:** Layer 4 Active Revision Governance dynamically excludes superseded `Rev 03` in favor of active `Rev 04`.

---

### Custom Question 5 (Anti-Hallucination Guardrail Test):
**Question:** *"What is the annual festival bonus percentage for machine operators at the Hosur plant?"*

- **Copilot Answer:**
  > **The provided documents do not contain information to answer this question.**
- **Sources Cited:** None (Guardrail active)
- **Layer Demonstrated:** Strict negative prompt boundary. The system refuses to hallucinate external company HR policies or general trivia outside the controlled PDFs.

---

## Repository Structure

```
copilotAgent/
├── .env.example               # Template environment configuration
├── .gitignore                 # Standard Python & OS ignore rules
├── requirements.txt           # Minimal pinned dependencies
├── main.py                    # FastAPI server & streaming API endpoint
├── run_server.py              # Server launcher with IP broadcast & port safety
├── ARCHITECTURE.md            # Detailed technical flow & complexity analysis
├── THINKING.md                # User journey, AI critique & reflections
├── README.md                  # Setup guide & verified test results
├── backend/
│   ├── document_parser.py     # PDF parsing & semantic chunking
│   ├── normalizer.py          # Typo fixer & DP Levenshtein distance
│   ├── retrieval.py           # Inverted Index, BM25 & Porter Stemmer
│   ├── cache.py               # In-memory LRU Query Cache (OrderedDict)
│   └── llm_client.py          # Groq LPU engine + Gemini fallback
├── docs/                      # Official plant PDFs (SOPs & manuals)
└── templates/
    └── index.html             # Clean, responsive mobile-first UI
```
