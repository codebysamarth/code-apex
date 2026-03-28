import os
import json
import sys
from faiss_client import FAISSClient

def build_index(rebuild=False):
    client = FAISSClient()
    
    # Check if index already has data
    stats = client.get_stats()
    
    # Support command line flag
    if "--rebuild" in sys.argv:
        rebuild = True

    if stats['total_brds'] > 0 and not rebuild:
        print(f"FAISS index already has {stats['total_brds']} entries.")
        print("Run with --rebuild flag to delete and rebuild.")
        return

    if rebuild:
        print("Rebuilding index...")
        client.rebuild()

    # Load from consolidated master file
    master_path = os.path.join(os.path.dirname(__file__), "data", "seed_brds_master.json")
    if not os.path.exists(master_path):
        print(f"ERROR: Seed data not found at {master_path}")
        return
        
    print(f"Full index rebuild from {master_path}...")
    with open(master_path, "r") as f:
        brds = json.load(f)
            
    total_indexed = 0
    for brd in brds:
        print(f"  Adding project: {brd.get('project_name')}...")
        client.add_brd(brd)
        total_indexed += 1
            
    print(f"\nFinal Statistics:")
    print(json.dumps(client.get_stats(), indent=2))
    print(f"\nSuccessfully indexed {total_indexed} BRDs.")

if __name__ == "__main__":
    rebuild_flag = "--rebuild" in sys.argv
    build_index(rebuild=rebuild_flag)
