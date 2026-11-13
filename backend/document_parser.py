import os
import re
from typing import List, Dict, Any
from pypdf import PdfReader


class DocumentParser:
    """
    Dynamically parses PDF manuals, SOPs, and technical procedures from disk.
    Extracts text, metadata (Document No, Revision, Effective Date), and creates
    structured text chunks with document attribution.
    """

    def __init__(self, docs_dir: str):
        self.docs_dir = docs_dir

    def load_documents(self) -> List[Dict[str, Any]]:
        documents = []
        if not os.path.exists(self.docs_dir):
            raise FileNotFoundError(f"Documents directory not found: {self.docs_dir}")

        for fname in os.listdir(self.docs_dir):
            if not fname.lower().endswith(".pdf"):
                continue
            if "sample_questions" in fname.lower():
                continue

            fpath = os.path.join(self.docs_dir, fname)
            doc_data = self._parse_single_pdf(fpath, fname)
            if doc_data:
                documents.append(doc_data)

        return documents

    def _parse_single_pdf(self, file_path: str, filename: str) -> Dict[str, Any]:
        try:
            reader = PdfReader(file_path)
            pages_text = []
            for idx, page in enumerate(reader.pages):
                extracted = page.extract_text() or ""
                cleaned = re.sub(r"[ \t]+", " ", extracted).strip()
                pages_text.append({
                    "page_number": idx + 1,
                    "text": cleaned
                })

            full_text = "\n\n".join([p["text"] for p in pages_text])
            
            doc_no_match = re.search(r"Document No\.?\s*[:\-]?\s*([A-Z0-9\-]+)", full_text, re.IGNORECASE)
            rev_match = re.search(r"Revision\s*[:\-]?\s*([0-9]+|Rev\s*[0-9]+)", full_text, re.IGNORECASE)
            
            doc_no = doc_no_match.group(1).strip() if doc_no_match else filename.split("_")[0]
            revision = rev_match.group(1).strip() if rev_match else "01"
            if not revision.lower().startswith("rev"):
                revision = f"Rev {revision}"

            # Document title from the first lines
            title_match = re.search(r"(?:Manual|Procedure|Standard Operating Procedure)\s*-\s*([^\n]+)", full_text, re.IGNORECASE)
            doc_title = title_match.group(0).strip() if title_match else filename.replace(".pdf", "")

            return {
                "filename": filename,
                "filepath": file_path,
                "doc_no": doc_no,
                "revision": revision,
                "title": doc_title,
                "pages": pages_text,
                "full_text": full_text
            }
        except Exception as e:
            print(f"Error parsing PDF {filename}: {e}")
            return None


class DocumentChunker:
    """
    Dynamically breaks down parsed documents into coherent semantic sections.
    Preserves document title and context on every section chunk.
    """

    @staticmethod
    def chunk_document(doc: Dict[str, Any]) -> List[Dict[str, Any]]:
        chunks = []
        for page in doc["pages"]:
            page_text = page["text"]
            # Split dynamically on section numbers like "1. ", "2. ", "4. "
            section_splits = re.split(r"\n(?=[0-9]+\.\s+[A-Z])", page_text)
            
            for sec_idx, section in enumerate(section_splits):
                cleaned_sec = section.strip()
                if not cleaned_sec:
                    continue

                # Strip redundant repeated header/footer lines from the text chunk
                cleaned_lines = []
                for line in cleaned_sec.split("\n"):
                    l_lower = line.lower()
                    if "uncontrolled copy when printed" in l_lower or "kaveri precision components" in l_lower or l_lower.startswith("page "):
                        continue
                    cleaned_lines.append(line)
                cleaned_sec = "\n".join(cleaned_lines).strip()
                if not cleaned_sec:
                    continue

                heading_match = re.match(r"^([0-9]+\.\s+[^\n]+)", cleaned_sec)
                heading = heading_match.group(1) if heading_match else f"General on Page {page['page_number']}"

                # Embed document context into chunk text so section-level queries match document scope
                context_prefix = f"[{doc['doc_no']} ({doc['revision']}) - {doc['title']}, Page {page['page_number']}]"

                chunks.append({
                    "doc_no": doc["doc_no"],
                    "revision": doc["revision"],
                    "doc_title": doc["title"],
                    "filename": doc["filename"],
                    "page_number": page["page_number"],
                    "heading": heading,
                    "text": cleaned_sec,
                    "context_prefix": context_prefix,
                    "chunk_id": f"{doc['doc_no']}_{doc['revision']}_p{page['page_number']}_s{sec_idx}"
                })
        return chunks
