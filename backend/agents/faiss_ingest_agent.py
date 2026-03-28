import time
import uuid
from state import BRDState
from faiss_client import FAISSClient

def faiss_ingest_agent(state: BRDState) -> BRDState:
    """
    Learner Agent: Stores every successfully generated BRD back into the FAISS index.
    This allows the system to learn from new projects over time.
    """
    start_time = time.time()
    
    # 1. Build BRD dict from state
    domain = state.get("domain", "software")
    project_name = state.get("project_name", f"Project_{uuid.uuid4().hex[:8]}")
    
    requirements = [r.get("text", "") for r in state.get("functional_reqs", [])]
    nfrs = [r.get("text", "") for r in state.get("nfrs", [])]
    
    # Check domain_sections
    domain_data = state.get("domain_data", {})
    sections = domain_data.get("sections", {})
    
    # 2. Extract compliance info (from domain_data if available)
    compliance_info = []
    if "compliance_check" in domain_data:
        cc = domain_data["compliance_check"]
        if isinstance(cc, dict) and "standard" in cc:
            compliance_info.append(cc["standard"])
            
    # 3. Build standardized BRD object
    brd_dict = {
        "id": str(uuid.uuid4()),
        "domain": domain,
        "project_name": project_name,
        "industry": state.get("analytics", {}).get("industry", ""),
        "requirements": requirements,
        "nfrs": nfrs,
        "domain_sections": sections,
        "compliance": compliance_info,
        "tags": [domain] + state.get("analytics", {}).get("tags", [])
    }
    
    # 4. Quality Check: Don't ingest empty or low-utility drafts
    has_content = len(requirements) > 2 or len(nfrs) > 1 or (isinstance(sections, dict) and len(sections) > 0)
    
    # 5. Add to FAISS
    try:
        if not has_content:
            print(f"[FAISSIngestAgent] Draft for {project_name} has insufficient content. Skipping ingestion.")
            state["analytics"]["faiss_ingest_status"] = "skipped (low quality)"
            return state

        client = FAISSClient()
        new_count = client.add_brd(brd_dict)
        print(f"[FAISSIngestAgent] Stored new BRD: {project_name}. New size: {new_count}")
        state["analytics"]["faiss_ingest_status"] = "success"
    except Exception as e:
        print(f"[FAISSIngestAgent] Failed to store BRD: {e}")
        state["analytics"]["faiss_ingest_status"] = "failed"
        
    state["processing_times"]["faiss_ingest"] = round(time.time() - start_time, 3)
    return state
