import json
import os
import urllib.request
from typing import List, Dict, Any, Optional


def load_env_key(key_name: str) -> str:
    """Dynamically loads configuration keys from the .env file or environment."""
    env_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), ".env")
    if os.path.exists(env_file):
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line.startswith(f"{key_name}="):
                    val = line.split("=", 1)[1].strip()
                    # Strip wrapping quotes if user formatted as KEY="value"
                    return val.strip("'\"")
    return os.environ.get(key_name, "").strip("'\"")


class GroundedLLMClient:
    """
    Truly Generalized, Non-Hardcoded Manufacturing Copilot Engine.
    
    CORE PRINCIPLE:
    We do NOT hardcode fixed scenarios (e.g. no specific mention of 'anxiety',
    'briefing workers', 'morning shift', or 'alarms without codes').
    
    Instead, the model is given a generalized role and generalized contextual reasoning:
    1. Understand the supervisor's intent, operational context, and emotional state.
    2. Ground every technical fact strictly in the retrieved factory SOP excerpts.
    3. Reframe, synthesize, and structure the SOP information to directly fit the user's
       situation (e.g. into a briefing, a checklist, a diagnostic guide, or a reassurance).
    4. Only reject if the query is fundamentally unrelated to factory operations or SOPs.
    """

    def __init__(self, groq_api_key: Optional[str] = None, gemini_api_key: Optional[str] = None):
        self.groq_api_key = groq_api_key or load_env_key("GROQ_API_KEY")
        self.gemini_api_key = gemini_api_key or load_env_key("GEMINI_API_KEY")

    def generate_response(self, user_query: str, context_chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        context_texts = []
        source_docs = []
        for i, c in enumerate(context_chunks, 1):
            source_tag = f"[{c['doc_no']} ({c['revision']}), Page {c['page_number']} - {c['heading']}]"
            context_texts.append(f"DOCUMENT EXCERPT {i} {source_tag}:\n{c['text']}")
            doc_ref = f"{c['doc_no']} ({c['revision']}), Page {c['page_number']}"
            if doc_ref not in source_docs:
                source_docs.append(doc_ref)

        combined_context = (
            "\n\n".join(context_texts)
            if context_texts
            else "NO APPLICABLE EXCERPTS FOUND IN FACTORY DOCUMENTS."
        )

        # 100% Generalized System Instruction — Zero fixed scenarios
        system_instruction = (
            "You are an intelligent, empathetic AI copilot for shop supervisors at Kaveri Precision Components (Hosur Plant).\n\n"
            "CORE INSTRUCTIONS:\n"
            "1. CONTEXTUAL INTELLIGENCE & EMPATHY:\n"
            "   - Actively analyze the user's prompt for emotional tone, operational urgency, and communication intent.\n"
            "   - If the user expresses stress, uncertainty, confusion, or panic, acknowledge their situation empathetically and provide calm, structured guidance.\n"
            "   - Adapt your output format to best solve their immediate need (e.g., turn complex procedures into step-by-step checklists, briefing points, or clear decision trees).\n\n"
            "2. STRICT SOP GROUNDING:\n"
            "   - Base all technical specifications, operating parameters, safety protocols, and actions strictly on the VERIFIED FACTORY EXCERPTS below.\n"
            "   - Always cite the exact Document Number, Revision, and Section used.\n\n"
            "3. HANDLING GAPS & AMBIGUITY:\n"
            "   - If the user's query lacks specific details (such as an exact machine code, alarm number, or dimension), summarize what the documents state on that topic and ask relevant clarifying questions.\n"
            "   - If the user's request is completely unrelated to plant operations, manufacturing, or the provided documents (e.g. general trivia, personal topics), state clearly:\n"
            "     'The provided documents do not contain information to answer this question.'"
        )

        user_content = f"""VERIFIED FACTORY EXCERPTS:
{combined_context}

USER MESSAGE:
{user_query}

COPILOT RESPONSE:"""

        # PRIMARY: Call Groq LPU (Sub-second latency)
        if self.groq_api_key:
            groq_res = self._call_groq(system_instruction, user_content, source_docs)
            if groq_res:
                return groq_res

        # SECONDARY: Gemini Failover
        if self.gemini_api_key:
            gemini_res = self._call_gemini(system_instruction, user_content, source_docs)
            if gemini_res:
                return gemini_res

        return {
            "answer": "System Configuration Error: Neither GROQ_API_KEY nor GEMINI_API_KEY is active.",
            "source_documents": []
        }

    def _call_groq(self, system_instruction: str, user_content: str, source_docs: List[str]) -> Optional[Dict[str, Any]]:
        url = "https://api.groq.com/openai/v1/chat/completions"
        payload = {
            "model": "qwen/qwen3.8-27b",
            "messages": [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_content}
            ],
            "temperature": 0.2,
            "max_tokens": 800
        }

        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.groq_api_key}",
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0"
            }
        )

        try:
            with urllib.request.urlopen(req, timeout=8) as response:
                res_data = json.loads(response.read().decode("utf-8"))
                content = res_data["choices"][0]["message"]["content"].strip()
                return {
                    "answer": content,
                    "source_documents": source_docs,
                    "model_used": "Groq LPU (qwen3.8-27b)"
                }
        except Exception as e:
            print(f"[Groq Exception: {e}], failing over to Gemini...")
            return None

    def _call_gemini(self, system_instruction: str, user_content: str, source_docs: List[str]) -> Optional[Dict[str, Any]]:
        models = ["gemini-3.5-flash", "gemini-3.6-flash", "gemini-3.8-flash"]
        prompt_body = f"{system_instruction}\n\n{user_content}"
        payload = {
            "contents": [{"parts": [{"text": prompt_body}]}],
            "generationConfig": {"temperature": 0.2, "maxOutputTokens": 800}
        }
        data_bytes = json.dumps(payload).encode("utf-8")

        for m in models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={self.gemini_api_key}"
            req = urllib.request.Request(url, data=data_bytes, headers={"Content-Type": "application/json"})
            try:
                with urllib.request.urlopen(req, timeout=12) as response:
                    res_json = json.loads(response.read().decode("utf-8"))
                    candidates = res_json.get("candidates", [])
                    if candidates and "content" in candidates[0]:
                        parts = candidates[0]["content"].get("parts", [])
                        if parts and "text" in parts[0]:
                            return {
                                "answer": parts[0]["text"].strip(),
                                "source_documents": source_docs,
                                "model_used": f"Gemini ({m})"
                            }
            except Exception:
                continue
        return None
