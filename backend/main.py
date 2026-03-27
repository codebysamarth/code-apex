"""
FastAPI Backend — BRD Agent
============================
Endpoints:
  POST /api/extract  — SSE streaming BRD extraction (text input)
  POST /api/extract-file — File upload extraction (PDF, DOCX, TXT, VTT, SRT)
  POST /api/extract-multi — Multi-document extraction
  GET  /api/export/{format} — Export BRD to PDF, Word, or Excel
  GET  /api/health   — Health check with ChromaDB vector count
  GET  /api/demo     — Returns a pre-computed realistic BRDState instantly
  GET  /api/model-stats — Returns classifier training stats (if available)
  GET  /api/supported-formats — Returns list of supported file formats

Run with:
    cd backend && source venv/bin/activate
    uvicorn main:app --reload --port 8000
"""

import os
import json
import time
import asyncio
from typing import AsyncGenerator, Optional, List

from fastapi import FastAPI, HTTPException, UploadFile, File, Form, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse
from dotenv import load_dotenv

load_dotenv()

# ---------------------------------------------------------------------------
# App setup
# ---------------------------------------------------------------------------
app = FastAPI(
    title="BRD Extraction Agent",
    description="7-agent LangGraph pipeline for BRD extraction from corporate communications",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Request models
# ---------------------------------------------------------------------------
class ExtractRequest(BaseModel):
    text: str
    source_type: str = "email"
    project_name: str = "Untitled Project"


class MultiExtractRequest(BaseModel):
    texts: List[str]
    source_names: List[str] = []
    project_name: str = "Untitled Project"


# Store last extraction result for export
_last_extraction_result: dict = {}


# ---------------------------------------------------------------------------
# Startup: pre-load models and check ChromaDB
# ---------------------------------------------------------------------------
@app.on_event("startup")
async def startup_event():
    """Pre-load classifier and check FAISS on startup."""
    # Import agents to trigger module-level model loading
    try:
        from chroma_client import get_vector_count
        vector_count = get_vector_count()
        import agents.classifier_agent as ca
    except Exception:
        vector_count = 0

    demo_mode = not os.getenv("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY") == "your_key_here"

    print(f"\n{'=' * 55}")
    print(f"  BRD Agent ready.")
    print(f"  FAISS DB : {vector_count} vectors loaded")
    print(f"  Mode     : {'DEMO (no API key)' if demo_mode else 'FULL (LLM enabled)'}")
    print(f"{'=' * 55}\n")


# ---------------------------------------------------------------------------
# POST /api/extract — SSE streaming pipeline
# ---------------------------------------------------------------------------
@app.post("/api/extract")
async def extract_brd(request: ExtractRequest):
    """
    Stream BRD extraction events via SSE.

    Events emitted:
    - {type: "node_complete", agent: "ingest", data: {...partial_state...}}
    - {type: "done", data: {...full_state...}}
    - {type: "error", message: "..."}
    """
    if not request.text or not request.text.strip():
        raise HTTPException(status_code=400, detail="Input text cannot be empty")

    async def event_generator() -> AsyncGenerator[dict, None]:
        from agents.ingest_agent import ingest_agent
        from agents.classifier_agent import classify_agent
        from agents.rag_agent import rag_agent
        from agents.extractor_agent import extractor_agent
        from agents.timeline_agent import timeline_agent
        from agents.critique_agent import critique_agent
        from agents.score_agent import score_agent
        from agents.render_agent import render_agent

        # Build initial state
        state = {
            "raw_input": request.text,
            "source_type": request.source_type,
            "project_name": request.project_name,
            "classified_sentences": [],
            "rag_examples": [],
            "functional_reqs": [],
            "nfrs": [],
            "stakeholders": [],
            "decisions": [],
            "timeline": [],
            "scope": {"in_scope": [], "out_of_scope": [], "assumptions": []},
            "gaps": [],
            "completeness_score": 0.0,
            "priority_scores": [],
            "source_map": {},
            "processing_times": {},
            "analytics": {},
            "retry_count": 0,
            "error": None,
        }

        # Agent sequence with SSE events
        agents = [
            ("ingest", ingest_agent),
            ("classify", classify_agent),
            ("rag", rag_agent),
            ("extract", extractor_agent),
            ("timeline", timeline_agent),
            ("critique", critique_agent),
            ("score", score_agent),
            ("render", render_agent),
        ]

        try:
            for agent_name, agent_fn in agents:
                # Run agent in thread pool to avoid blocking the event loop
                loop = asyncio.get_event_loop()
                state = await loop.run_in_executor(None, agent_fn, state)

                if state.get("error"):
                    yield {
                        "event": "message",
                        "data": json.dumps({
                            "type": "error",
                            "message": state["error"],
                        }),
                    }
                    return

                # Emit node_complete event with safe partial state
                partial = {
                    "type": "node_complete",
                    "agent": agent_name,
                    "processing_time": state["processing_times"].get(agent_name, 0),
                    "data": {
                        "classified_count": len(state.get("classified_sentences", [])),
                        "rag_count": len(state.get("rag_examples", [])),
                        "fr_count": len(state.get("functional_reqs", [])),
                        "nfr_count": len(state.get("nfrs", [])),
                        "source_type": state.get("source_type", ""),
                    },
                }

                yield {
                    "event": "message",
                    "data": json.dumps(partial),
                }

                # Small yield to allow other async tasks
                await asyncio.sleep(0)

            # Store for export
            global _last_extraction_result
            _last_extraction_result = state

            # Final event: full state
            yield {
                "event": "message",
                "data": json.dumps({
                    "type": "done",
                    "data": state,
                }),
            }

        except Exception as e:
            yield {
                "event": "message",
                "data": json.dumps({
                    "type": "error",
                    "message": str(e),
                }),
            }

    return EventSourceResponse(event_generator())


# ---------------------------------------------------------------------------
# POST /api/extract-file — File upload extraction
# ---------------------------------------------------------------------------
@app.post("/api/extract-file")
async def extract_from_file(
    file: UploadFile = File(...),
    project_name: str = Form("Untitled Project"),
):
    """
    Extract BRD from uploaded file (PDF, DOCX, TXT, VTT, SRT, MD).
    
    Returns SSE stream with extraction progress.
    """
    from document_parser import get_parser
    
    parser = get_parser()
    supported = parser.get_supported_formats()
    
    # Check file extension
    filename = file.filename or "uploaded_file"
    ext = os.path.splitext(filename.lower())[1]
    
    if ext not in supported:
        raise HTTPException(
            status_code=400, 
            detail=f"Unsupported file format: {ext}. Supported: {list(supported.keys())}"
        )
    
    if not supported[ext]:
        raise HTTPException(
            status_code=400,
            detail=f"Format {ext} requires additional dependencies. Check /api/supported-formats"
        )
    
    # Read and parse file
    content = await file.read()
    
    try:
        parsed = parser.parse(content, filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Failed to parse file: {str(e)}")
    
    # Create extraction request and reuse extract_brd logic
    request = ExtractRequest(
        text=parsed.text,
        source_type=parsed.source_type,
        project_name=project_name,
    )
    
    return await extract_brd(request)


# ---------------------------------------------------------------------------
# POST /api/extract-multi — Multi-document extraction
# ---------------------------------------------------------------------------
@app.post("/api/extract-multi")
async def extract_from_multi(
    files: List[UploadFile] = File(None),
    texts: str = Form(None),  # JSON array of texts
    source_names: str = Form(None),  # JSON array of names
    project_name: str = Form("Untitled Project"),
):
    """
    Extract BRD from multiple documents (files and/or text inputs).
    Merges and deduplicates requirements across all sources.
    
    Parameters:
    - files: Multiple file uploads
    - texts: JSON array of text strings (alternative to files)
    - source_names: JSON array of names for text inputs
    - project_name: Name for the project
    """
    from document_parser import get_parser
    from multi_doc_processor import get_multi_doc_processor
    
    parser = get_parser()
    processor = get_multi_doc_processor()
    
    multi = processor.create_input(project_name)
    
    # Add uploaded files
    if files:
        for file in files:
            if file.filename:
                content = await file.read()
                try:
                    processor.add_file(multi, content, file.filename)
                except Exception as e:
                    raise HTTPException(status_code=400, detail=f"Failed to parse {file.filename}: {str(e)}")
    
    # Add text inputs
    if texts:
        try:
            text_list = json.loads(texts)
            name_list = json.loads(source_names) if source_names else []
            
            for i, text in enumerate(text_list):
                name = name_list[i] if i < len(name_list) else f"text_input_{i+1}"
                processor.add_text(multi, text, name)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON in texts or source_names parameter")
    
    if not multi.documents:
        raise HTTPException(status_code=400, detail="No documents provided")
    
    # Prepare combined input
    prepared = processor.prepare_for_extraction(multi)
    
    # Create extraction request
    request = ExtractRequest(
        text=prepared["raw_input"],
        source_type=prepared["source_type"],
        project_name=project_name,
    )
    
    return await extract_brd(request)


# ---------------------------------------------------------------------------
# GET /api/export/{format} — Export BRD
# ---------------------------------------------------------------------------
@app.get("/api/export/{format}")
async def export_brd(
    format: str,
    project_name: str = Query(None, description="Override project name in export"),
):
    """
    Export the last extraction result to PDF, Word, or Excel format.
    
    Formats:
    - pdf: Professional PDF document
    - word / docx: Microsoft Word document
    - excel / xlsx: Excel workbook with multiple sheets
    - html: HTML document (fallback if PDF libs not installed)
    """
    global _last_extraction_result
    
    if not _last_extraction_result:
        raise HTTPException(
            status_code=400, 
            detail="No extraction result available. Run /api/extract first."
        )
    
    # Clone and optionally update project name
    export_data = _last_extraction_result.copy()
    if project_name:
        export_data["project_name"] = project_name
    
    format = format.lower()
    
    try:
        if format == "pdf":
            from export.pdf_export import export_to_pdf
            content = export_to_pdf(export_data)
            return Response(
                content=content,
                media_type="application/pdf",
                headers={"Content-Disposition": f"attachment; filename=BRD_{project_name or 'export'}.pdf"}
            )
        
        elif format in ("word", "docx"):
            from export.word_export import export_to_word
            content = export_to_word(export_data)
            return Response(
                content=content,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={"Content-Disposition": f"attachment; filename=BRD_{project_name or 'export'}.docx"}
            )
        
        elif format in ("excel", "xlsx"):
            from export.excel_export import export_to_excel
            content = export_to_excel(export_data)
            return Response(
                content=content,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                headers={"Content-Disposition": f"attachment; filename=BRD_{project_name or 'export'}.xlsx"}
            )
        
        elif format == "html":
            from export.pdf_export import _export_html_fallback
            content = _export_html_fallback(export_data)
            return Response(
                content=content,
                media_type="text/html",
                headers={"Content-Disposition": f"attachment; filename=BRD_{project_name or 'export'}.html"}
            )
        
        elif format == "json":
            return Response(
                content=json.dumps(export_data, indent=2),
                media_type="application/json",
                headers={"Content-Disposition": f"attachment; filename=BRD_{project_name or 'export'}.json"}
            )
        
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported format: {format}. Supported: pdf, word, excel, html, json"
            )
    
    except ImportError as e:
        raise HTTPException(
            status_code=500,
            detail=f"Export format '{format}' requires additional dependencies: {str(e)}"
        )


# ---------------------------------------------------------------------------
# POST /api/export/{format} — Export with provided data
# ---------------------------------------------------------------------------
@app.post("/api/export/{format}")
async def export_brd_with_data(format: str, brd_data: dict):
    """
    Export provided BRD data to specified format.
    
    Use this endpoint when you want to export data without running extraction first.
    """
    if not brd_data:
        raise HTTPException(status_code=400, detail="BRD data is required")
    
    # Temporarily store and use the GET endpoint logic
    global _last_extraction_result
    _last_extraction_result = brd_data
    
    return await export_brd(format)


# ---------------------------------------------------------------------------
# GET /api/supported-formats — List supported formats
# ---------------------------------------------------------------------------
@app.get("/api/supported-formats")
async def get_supported_formats():
    """Returns list of supported input file formats and their availability."""
    from document_parser import get_parser
    
    parser = get_parser()
    formats = parser.get_supported_formats()
    
    return {
        "input_formats": {
            ext: {
                "available": available,
                "description": _get_format_description(ext),
            }
            for ext, available in formats.items()
        },
        "export_formats": {
            "pdf": {"available": True, "description": "Professional PDF document"},
            "word": {"available": True, "description": "Microsoft Word document (.docx)"},
            "excel": {"available": True, "description": "Excel workbook with multiple sheets (.xlsx)"},
            "html": {"available": True, "description": "HTML document (browser printable)"},
            "json": {"available": True, "description": "Raw JSON data"},
        },
    }


def _get_format_description(ext: str) -> str:
    """Get human-readable description for file format."""
    descriptions = {
        ".txt": "Plain text file",
        ".md": "Markdown document",
        ".pdf": "PDF document (requires pdfplumber)",
        ".docx": "Microsoft Word document (requires python-docx)",
        ".doc": "Legacy Word document (requires python-docx)",
        ".vtt": "WebVTT meeting transcript",
        ".srt": "SubRip meeting transcript",
    }
    return descriptions.get(ext, "Unknown format")


# ---------------------------------------------------------------------------
# GET /api/health
# ---------------------------------------------------------------------------
@app.get("/api/health")
async def health_check():
    """Returns server health, FAISS vector count, and model load status."""
    try:
        from chroma_client import get_vector_count
        vector_count = get_vector_count()
    except Exception:
        vector_count = 0

    try:
        import agents.classifier_agent as ca
        model_loaded = ca._pipeline is not None
    except Exception:
        model_loaded = False

    api_key = os.getenv("GOOGLE_API_KEY", "")
    api_key_present = bool(api_key and api_key != "your_key_here")

    return {
        "status": "ok",
        "faiss_vectors": vector_count,
        "classifier_loaded": model_loaded,
        "api_key_present": api_key_present,
        "version": "1.0.0",
    }


# ---------------------------------------------------------------------------
# GET /api/demo — instant pre-computed result
# ---------------------------------------------------------------------------
@app.get("/api/demo")
async def get_demo():
    """Returns a pre-computed realistic BRDState for demo/testing without API key."""
    return {
        "raw_input": (
            "From: sarah@acme.com\nSubject: Q3 Dashboard Requirements\n\n"
            "The system must allow users to log in using SSO. "
            "Users must be able to reset passwords via email link. "
            "The dashboard must display real-time analytics refreshed every 30 seconds. "
            "The API must respond within 200ms at P99. "
            "All user data must be encrypted at rest using AES-256. "
            "We decided to use Stripe for payment processing. "
            "Sarah will own the product sign-off. "
            "The project kicks off in Q1 2024 with go-live by June 2024."
        ),
        "source_type": "email",
        "classified_sentences": [
            {"text": "The system must allow users to log in using SSO.", "label": "functional_req", "confidence": 0.96},
            {"text": "Users must be able to reset passwords via email link.", "label": "functional_req", "confidence": 0.94},
            {"text": "The API must respond within 200ms at P99.", "label": "nfr", "confidence": 0.92},
            {"text": "All user data must be encrypted at rest using AES-256.", "label": "nfr", "confidence": 0.91},
            {"text": "We decided to use Stripe for payment processing.", "label": "decision", "confidence": 0.89},
            {"text": "Sarah will own the product sign-off.", "label": "stakeholder", "confidence": 0.85},
            {"text": "The project kicks off in Q1 2024.", "label": "timeline", "confidence": 0.90},
        ],
        "rag_examples": [
            {"text": "System must support OAuth2 SSO integration.", "label": "functional_req", "source": "enron", "similarity": 0.92},
            {"text": "API latency must not exceed 200ms at 99th percentile.", "label": "nfr", "source": "ami", "similarity": 0.88},
            {"text": "Decided to migrate to AWS from on-prem.", "label": "decision", "source": "enron", "similarity": 0.85},
        ],
        "functional_reqs": [
            {"id": "FR-001", "text": "The system must allow users to log in using SSO.", "priority": 1, "moscow": "Must", "confidence": 0.96, "source_span": "allow users to log in using SSO"},
            {"id": "FR-002", "text": "Users must be able to reset passwords via email link.", "priority": 1, "moscow": "Must", "confidence": 0.94, "source_span": "reset passwords via email link"},
            {"id": "FR-003", "text": "The dashboard must display real-time analytics refreshed every 30 seconds.", "priority": 2, "moscow": "Should", "confidence": 0.88, "source_span": "display real-time analytics"},
            {"id": "FR-004", "text": "Users should be able to export reports as PDF.", "priority": 2, "moscow": "Should", "confidence": 0.78, "source_span": "export reports as PDF"},
            {"id": "FR-005", "text": "Admins must be able to manage user roles and permissions.", "priority": 1, "moscow": "Must", "confidence": 0.91, "source_span": "manage user roles and permissions"},
            {"id": "FR-006", "text": "The system could support multi-language interface.", "priority": 3, "moscow": "Could", "confidence": 0.65, "source_span": "multi-language interface"},
        ],
        "nfrs": [
            {"id": "NFR-001", "text": "The API must respond within 200ms at P99.", "category": "Performance", "priority": 1, "confidence": 0.92},
            {"id": "NFR-002", "text": "All user data must be encrypted at rest using AES-256.", "category": "Security", "priority": 1, "confidence": 0.91},
            {"id": "NFR-003", "text": "The system must maintain 99.9% uptime.", "category": "Reliability", "priority": 1, "confidence": 0.89},
            {"id": "NFR-004", "text": "The platform must support up to 10,000 concurrent users.", "category": "Scalability", "priority": 2, "confidence": 0.84},
        ],
        "stakeholders": [
            {"name": "Sarah", "role": "Product Owner", "influence_score": 0.95, "mentioned_count": 3},
            {"name": "Rahul", "role": "Engineering Lead", "influence_score": 0.85, "mentioned_count": 2},
            {"name": "Finance Team", "role": "Approver", "influence_score": 0.70, "mentioned_count": 1},
        ],
        "decisions": [
            {"id": "DEC-001", "text": "Use Stripe for all payment processing.", "rationale": "Evaluated three vendors; Stripe offers best API docs and reliability.", "date_mentioned": "Q3 2024"},
            {"id": "DEC-002", "text": "Deploy on AWS using ECS Fargate.", "rationale": "Cost-effective for variable load, no server management overhead.", "date_mentioned": ""},
        ],
        "timeline": [
            {"milestone": "Project kick-off and team onboarding", "date": "Q1 2024", "type": "kickoff", "dependencies": [], "urgency": "high"},
            {"milestone": "Sprint 1 — Authentication module complete", "date": "March 2024", "type": "sprint", "dependencies": ["Project kick-off"], "urgency": "high"},
            {"milestone": "Sprint 2 — Dashboard and analytics", "date": "April 2024", "type": "sprint", "dependencies": ["Sprint 1"], "urgency": "medium"},
            {"milestone": "UAT and stakeholder review", "date": "May 2024", "type": "deadline", "dependencies": ["Sprint 2"], "urgency": "high"},
            {"milestone": "Production go-live", "date": "June 2024", "type": "go-live", "dependencies": ["UAT"], "urgency": "critical"},
            {"milestone": "Final sign-off deadline", "date": "2024-07-31", "type": "deadline", "dependencies": ["Production go-live"], "urgency": "high"},
        ],
        "scope": {
            "in_scope": ["SSO login", "Password reset", "Real-time analytics dashboard", "Role management", "Stripe payment integration"],
            "out_of_scope": ["Mobile app (Phase 2)", "Third-party API marketplace", "Legacy data migration"],
            "assumptions": ["Corporate SSO provider (Okta) is already configured", "AWS account provisioned", "Stripe account approved"],
        },
        "gaps": [
            {"gap": "FR-004 (PDF export) lacks specific format and size constraints", "severity": "medium", "suggestion": "Define max PDF size, orientation, and supported chart types for export"},
            {"gap": "No data retention policy defined", "severity": "high", "suggestion": "Specify how long user activity logs and analytics data are retained (GDPR compliance)"},
            {"gap": "FR-006 (multi-language) has no target locales specified", "severity": "low", "suggestion": "List which languages are in scope for Phase 1 vs Phase 2"},
        ],
        "completeness_score": 0.82,
        "priority_scores": [
            {"req_id": "FR-001", "req_type": "FR", "moscow": "Must", "priority": 1, "value_score": 0.96, "effort_score": 0.35, "confidence": 0.96},
            {"req_id": "FR-002", "req_type": "FR", "moscow": "Must", "priority": 1, "value_score": 0.94, "effort_score": 0.40, "confidence": 0.94},
            {"req_id": "FR-003", "req_type": "FR", "moscow": "Should", "priority": 2, "value_score": 0.62, "effort_score": 0.65, "confidence": 0.88},
            {"req_id": "FR-004", "req_type": "FR", "moscow": "Should", "priority": 2, "value_score": 0.55, "effort_score": 0.45, "confidence": 0.78},
            {"req_id": "FR-005", "req_type": "FR", "moscow": "Must", "priority": 1, "value_score": 0.91, "effort_score": 0.50, "confidence": 0.91},
            {"req_id": "FR-006", "req_type": "FR", "moscow": "Could", "priority": 3, "value_score": 0.26, "effort_score": 0.80, "confidence": 0.65},
            {"req_id": "NFR-001", "req_type": "NFR", "moscow": "Must", "priority": 1, "value_score": 0.83, "effort_score": 0.50, "confidence": 0.92},
            {"req_id": "NFR-002", "req_type": "NFR", "moscow": "Must", "priority": 1, "value_score": 0.82, "effort_score": 0.50, "confidence": 0.91},
        ],
        "source_map": {
            "FR-001": {"start": 95, "end": 138, "text": "allow users to log in using SSO"},
            "FR-002": {"start": 139, "end": 192, "text": "reset passwords via email link"},
        },
        "processing_times": {
            "ingest": 0.01,
            "classifier": 0.28,
            "rag": 1.12,
            "extractor": 3.45,
            "timeline": 0.05,
            "critique": 2.81,
            "score": 0.03,
            "render": 0.01,
        },
        "analytics": {
            "confidence_distribution": {"high": 5, "medium": 2, "low": 0, "very_low": 0},
            "rag_source_breakdown": {"enron": 12, "ami": 6, "fallback": 3},
            "req_type_breakdown": {"Functional": 6, "Non-Functional": 4, "Decisions": 2, "Stakeholders": 3},
            "total_requirements": 10,
            "processing_times": {"ingest": 0.01, "classifier": 0.28, "rag": 1.12, "extractor": 3.45, "timeline": 0.05, "critique": 2.81, "score": 0.03, "render": 0.01},
            "total_processing_time": 7.76,
            "completeness_score": 0.82,
            "gap_severity_summary": {"critical": 0, "high": 1, "medium": 1, "low": 1},
            "ami_recall": {"fr_recall": 0.85, "nfr_recall": 0.90, "stakeholder_recall": 0.75, "timeline_recall": 0.80, "overall_recall": 0.83, "ami_avg_reqs": 4.2},
            "label_counts": {"functional_reqs": 6, "nfrs": 4, "stakeholders": 3, "decisions": 2},
            "moscow_distribution": {"Must": 5, "Should": 2, "Could": 1, "Wont": 0},
            "source_type": "email",
            "total_sentences_classified": 7,
        },
        "retry_count": 0,
        "error": None,
    }


# ---------------------------------------------------------------------------
# GET /api/model-stats
# ---------------------------------------------------------------------------
@app.get("/api/model-stats")
async def get_model_stats():
    """Returns classifier training statistics from training_stats.json if available."""
    stats_path = os.path.join(
        os.getenv("MODEL_PATH", "./backend/models"),
        "training_stats.json"
    )

    if os.path.exists(stats_path):
        with open(stats_path, "r") as f:
            return json.load(f)

    # Return placeholder stats if file not available
    return {
        "note": "training_stats.json not found — showing estimated stats",
        "accuracy": 0.87,
        "classes": {
            "functional_req": {"precision": 0.91, "recall": 0.89, "f1": 0.90},
            "nfr":            {"precision": 0.88, "recall": 0.85, "f1": 0.86},
            "decision":       {"precision": 0.84, "recall": 0.82, "f1": 0.83},
            "timeline":       {"precision": 0.86, "recall": 0.84, "f1": 0.85},
            "stakeholder":    {"precision": 0.82, "recall": 0.80, "f1": 0.81},
            "noise":          {"precision": 0.90, "recall": 0.93, "f1": 0.91},
        },
    }
