"""
Multi-Document Processor
========================
Combines multiple documents into a single BRD extraction.

Features:
- Merge requirements from multiple sources
- Deduplicate similar requirements
- Track source document for each requirement
- Aggregate stakeholders and decisions
"""

import re
import hashlib
from typing import Optional
from dataclasses import dataclass, field
from document_parser import ParsedDocument, get_parser


@dataclass
class MultiDocumentInput:
    """Container for multiple documents to process together."""
    documents: list[ParsedDocument] = field(default_factory=list)
    project_name: str = "Untitled Project"
    
    def add_document(self, doc: ParsedDocument):
        """Add a document to the collection."""
        self.documents.append(doc)
    
    def get_combined_text(self) -> str:
        """Get all documents combined into a single text with source markers."""
        parts = []
        for i, doc in enumerate(self.documents, 1):
            parts.append(f"=== DOCUMENT {i}: {doc.filename} ({doc.source_type}) ===\n{doc.text}\n")
        return "\n\n".join(parts)
    
    @property
    def total_word_count(self) -> int:
        return sum(doc.word_count for doc in self.documents)
    
    @property
    def document_count(self) -> int:
        return len(self.documents)


class MultiDocumentProcessor:
    """Process and merge multiple documents into unified BRD output."""
    
    def __init__(self):
        self.parser = get_parser()
    
    def create_input(self, project_name: str = "Untitled Project") -> MultiDocumentInput:
        """Create a new multi-document input container."""
        return MultiDocumentInput(project_name=project_name)
    
    def add_file(self, multi_input: MultiDocumentInput, content: bytes, filename: str):
        """Parse and add a file to the multi-document input."""
        doc = self.parser.parse(content, filename)
        multi_input.add_document(doc)
    
    def add_text(self, multi_input: MultiDocumentInput, text: str, source_name: str = "text_input"):
        """Add raw text as a document."""
        doc = self.parser.parse_string(text, "text")
        doc.filename = source_name
        multi_input.add_document(doc)
    
    def prepare_for_extraction(self, multi_input: MultiDocumentInput) -> dict:
        """
        Prepare multi-document input for the extraction pipeline.
        Returns state dict compatible with the BRD pipeline.
        """
        combined_text = multi_input.get_combined_text()
        
        # Determine primary source type
        source_types = [doc.source_type for doc in multi_input.documents]
        if 'transcript' in source_types:
            primary_type = 'meeting'
        elif 'email' in source_types or any('email' in doc.filename.lower() for doc in multi_input.documents):
            primary_type = 'email'
        else:
            primary_type = 'document'
        
        return {
            "raw_input": combined_text,
            "source_type": primary_type,
            "multi_document": True,
            "document_sources": [
                {
                    "index": i,
                    "filename": doc.filename,
                    "type": doc.source_type,
                    "word_count": doc.word_count,
                }
                for i, doc in enumerate(multi_input.documents, 1)
            ],
            "project_name": multi_input.project_name,
        }
    
    def merge_extractions(self, extractions: list[dict]) -> dict:
        """
        Merge multiple extraction results into a single unified BRD.
        Deduplicates similar requirements.
        
        Args:
            extractions: List of extraction results from multiple documents
            
        Returns:
            Merged extraction with deduplicated requirements
        """
        merged = {
            "functional_reqs": [],
            "nfrs": [],
            "stakeholders": [],
            "decisions": [],
            "scope": {"in_scope": [], "out_of_scope": [], "assumptions": []},
            "timeline": [],
        }
        
        # Track seen items for deduplication
        seen_fr_hashes = set()
        seen_nfr_hashes = set()
        seen_stakeholders = set()
        seen_decisions = set()
        
        fr_counter = 1
        nfr_counter = 1
        dec_counter = 1
        
        for doc_idx, extraction in enumerate(extractions, 1):
            source_label = f"Doc{doc_idx}"
            
            # Merge functional requirements
            for req in extraction.get("functional_reqs", []):
                text_hash = self._text_hash(req.get("text", ""))
                if text_hash not in seen_fr_hashes:
                    seen_fr_hashes.add(text_hash)
                    req["id"] = f"FR-{fr_counter:03d}"
                    req["source_document"] = source_label
                    merged["functional_reqs"].append(req)
                    fr_counter += 1
            
            # Merge NFRs
            for nfr in extraction.get("nfrs", []):
                text_hash = self._text_hash(nfr.get("text", ""))
                if text_hash not in seen_nfr_hashes:
                    seen_nfr_hashes.add(text_hash)
                    nfr["id"] = f"NFR-{nfr_counter:03d}"
                    nfr["source_document"] = source_label
                    merged["nfrs"].append(nfr)
                    nfr_counter += 1
            
            # Merge stakeholders (by name)
            for sh in extraction.get("stakeholders", []):
                name_key = sh.get("name", "").lower().strip()
                if name_key and name_key not in seen_stakeholders:
                    seen_stakeholders.add(name_key)
                    sh["source_document"] = source_label
                    merged["stakeholders"].append(sh)
                elif name_key in seen_stakeholders:
                    # Update mention count for existing stakeholder
                    for existing in merged["stakeholders"]:
                        if existing.get("name", "").lower().strip() == name_key:
                            existing["mentioned_count"] = existing.get("mentioned_count", 1) + sh.get("mentioned_count", 1)
                            break
            
            # Merge decisions
            for dec in extraction.get("decisions", []):
                text_hash = self._text_hash(dec.get("text", ""))
                if text_hash not in seen_decisions:
                    seen_decisions.add(text_hash)
                    dec["id"] = f"DEC-{dec_counter:03d}"
                    dec["source_document"] = source_label
                    merged["decisions"].append(dec)
                    dec_counter += 1
            
            # Merge scope
            scope = extraction.get("scope", {})
            merged["scope"]["in_scope"].extend(scope.get("in_scope", []))
            merged["scope"]["out_of_scope"].extend(scope.get("out_of_scope", []))
            merged["scope"]["assumptions"].extend(scope.get("assumptions", []))
            
            # Merge timeline
            for milestone in extraction.get("timeline", []):
                milestone["source_document"] = source_label
                merged["timeline"].append(milestone)
        
        # Deduplicate scope items
        merged["scope"]["in_scope"] = list(set(merged["scope"]["in_scope"]))
        merged["scope"]["out_of_scope"] = list(set(merged["scope"]["out_of_scope"]))
        merged["scope"]["assumptions"] = list(set(merged["scope"]["assumptions"]))
        
        # Sort timeline by type priority
        type_order = {"kickoff": 0, "sprint": 1, "milestone": 2, "go-live": 3, "deadline": 4}
        merged["timeline"].sort(key=lambda m: type_order.get(m.get("type", "milestone"), 2))
        
        return merged
    
    def _text_hash(self, text: str) -> str:
        """Generate a normalized hash for deduplication."""
        # Normalize: lowercase, remove extra whitespace, remove punctuation
        normalized = re.sub(r'\s+', ' ', text.lower().strip())
        normalized = re.sub(r'[^\w\s]', '', normalized)
        return hashlib.md5(normalized.encode()).hexdigest()[:12]
    
    def calculate_similarity(self, text1: str, text2: str) -> float:
        """Calculate text similarity using Jaccard similarity on words."""
        words1 = set(re.findall(r'\w+', text1.lower()))
        words2 = set(re.findall(r'\w+', text2.lower()))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1 & words2)
        union = len(words1 | words2)
        
        return intersection / union if union > 0 else 0.0


# Singleton instance
_processor = None

def get_multi_doc_processor() -> MultiDocumentProcessor:
    """Get singleton multi-document processor instance."""
    global _processor
    if _processor is None:
        _processor = MultiDocumentProcessor()
    return _processor


if __name__ == "__main__":
    # Test multi-document processing
    processor = MultiDocumentProcessor()
    
    # Create test documents
    doc1_text = """
    Email from John (PM):
    The system must support credit card payments.
    We need to launch by Q2 2025.
    """
    
    doc2_text = """
    Meeting notes with Sarah (Tech Lead):
    The API should respond within 500ms.
    We decided to use Stripe for payments.
    The system must also support PayPal.
    """
    
    # Create multi-document input
    multi = processor.create_input("Payment System Project")
    processor.add_text(multi, doc1_text, "email_from_john.txt")
    processor.add_text(multi, doc2_text, "meeting_notes.txt")
    
    print(f"Project: {multi.project_name}")
    print(f"Documents: {multi.document_count}")
    print(f"Total words: {multi.total_word_count}")
    print(f"\nCombined text preview:")
    print(multi.get_combined_text()[:500])
    
    # Test deduplication
    extraction1 = {
        "functional_reqs": [
            {"text": "Support credit card payments", "confidence": 0.9},
            {"text": "Support PayPal", "confidence": 0.85},
        ],
        "stakeholders": [{"name": "John", "role": "PM", "mentioned_count": 2}],
    }
    
    extraction2 = {
        "functional_reqs": [
            {"text": "Support credit card payments", "confidence": 0.88},  # Duplicate
            {"text": "Support Apple Pay", "confidence": 0.8},
        ],
        "stakeholders": [
            {"name": "John", "role": "Product Manager", "mentioned_count": 1},  # Same person
            {"name": "Sarah", "role": "Tech Lead", "mentioned_count": 3},
        ],
    }
    
    merged = processor.merge_extractions([extraction1, extraction2])
    print(f"\nMerged FRs: {len(merged['functional_reqs'])} (should be 3, not 4)")
    print(f"Merged stakeholders: {len(merged['stakeholders'])} (should be 2)")
    for sh in merged['stakeholders']:
        print(f"  - {sh['name']}: mentioned {sh.get('mentioned_count', 1)} times")
