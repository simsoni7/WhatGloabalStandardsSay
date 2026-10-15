"""Required local publication gate; no model approvals or autonomous collection."""
import json,os,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];node=os.environ.get('WGSS_NODE_BIN','node')
def run(*args):subprocess.run(args,cwd=R,check=True)
run(sys.executable,'scripts/build_page_entries.py')
run(sys.executable,'scripts/check_product_sources.py')
run(sys.executable,'scripts/build_operations.py')
run(sys.executable,'scripts/check_mece_closure.py')
if (R/'data/mece-v22-root-dispositions.json').exists():
    run(os.environ.get('WGSS_BROWSER_PYTHON',sys.executable),'tests/source_census_v22.py')
run(sys.executable,'scripts/build_backbone.py')
run(sys.executable,'scripts/check_completion_dispositions.py')
run(node,'scripts/product_query_gate.js','--write')
run(sys.executable,'scripts/build_backbone.py')
run(node,'tests/product_semantics.js')
run(sys.executable,'tests/mece_closure.py')
run(node,'tests/financial_backbone.js')
run(sys.executable,'tests/operations.py')
run(sys.executable,'tests/reference_override.py')
if (R/'data/bank-ui-root-decisions.json').exists():
    run(sys.executable,'scripts/build_bank_ui.py')
    run(os.environ.get('WGSS_BROWSER_PYTHON',sys.executable),'tests/bank_customer_scope.py')
    if (R/'data/bank-ui-collection-v24-decisions.json').exists():
        run(os.environ.get('WGSS_BROWSER_PYTHON',sys.executable),'tests/bank_collection_evidence.py')
    if (R/'data/bank-ui-collection-v25-decisions.json').exists():
        run(os.environ.get('WGSS_BROWSER_PYTHON',sys.executable),'tests/bank_priority_evidence.py')
if (R/'data/bank-ui-collection-v26-decisions.json').exists():
    run(os.environ.get('WGSS_BROWSER_PYTHON',sys.executable),'tests/bank_priority_v26.py')
if (R/'data/bank-ui-collection-v27-decisions.json').exists():
    run(os.environ.get('WGSS_BROWSER_PYTHON',sys.executable),'tests/bank_priority_v27.py')
if (R/'data/bank-ui-collection-v28-decisions.json').exists():
    run(os.environ.get('WGSS_BROWSER_PYTHON',sys.executable),'tests/bank_breadth_v28.py')
if (R/'data/bank-ui-collection-v29-decisions.json').exists():
    run(os.environ.get('WGSS_BROWSER_PYTHON',sys.executable),'tests/bank_expansion_v29.py')
if (R/'data/bank-ui-collection-v30-decisions.json').exists():
    run(os.environ.get('WGSS_BROWSER_PYTHON',sys.executable),'tests/bank_gaps_v30.py')
if (R/'data/bank-ui-collection-v31-decisions.json').exists():
    run(os.environ.get('WGSS_BROWSER_PYTHON',sys.executable),'tests/bank_collection_v31.py')
    run(os.environ.get('WGSS_BROWSER_PYTHON',sys.executable),'tests/local_session_capture.py')
if (R/'data/bank-ui-collection-v32-decisions.json').exists():
    run(os.environ.get('WGSS_BROWSER_PYTHON',sys.executable),'tests/bank_collection_v32.py')
if (R/'data/bank-ui-collection-v33-decisions.json').exists():
    run(os.environ.get('WGSS_BROWSER_PYTHON',sys.executable),'tests/bank_collection_v33.py')
if (R/'data/bank-ui-reference-quality-v34-decisions.json').exists():
    run(os.environ.get('WGSS_BROWSER_PYTHON',sys.executable),'tests/bank_reference_quality_v34.py')
if (R/'data/bank-ui-supporting-task-flow-v35-decisions.json').exists():
    run(os.environ.get('WGSS_BROWSER_PYTHON',sys.executable),'tests/bank_supporting_task_flow_v35.py')
run(sys.executable,'scripts/build_coverage.py')
run(os.environ.get('WGSS_BROWSER_PYTHON',sys.executable),'tests/browser_products.py')
if (R/'tests/browser_canonical_search_v36.py').exists():
    run(os.environ.get('WGSS_BROWSER_PYTHON',sys.executable),'tests/browser_canonical_search_v36.py')
if (R/'tests/browser_capture_comparison_v37.py').exists():
    run(os.environ.get('WGSS_BROWSER_PYTHON',sys.executable),'tests/browser_capture_comparison_v37.py')
if (R/'tests/browser_practitioner_v38.py').exists():
    run(os.environ.get('WGSS_BROWSER_PYTHON',sys.executable),'tests/browser_practitioner_v38.py')
    run(os.environ.get('WGSS_BROWSER_PYTHON',sys.executable),'tests/browser_interview_v38.py')
if (R/'tests/browser_public_assets_v39.py').exists():
    run(os.environ.get('WGSS_BROWSER_PYTHON',sys.executable),'tests/browser_public_assets_v39.py')
if (R/'tests/browser_direct_entries_v40.py').exists():
    run(os.environ.get('WGSS_BROWSER_PYTHON',sys.executable),'tests/browser_direct_entries_v40.py')
if (R/'tests/browser_reference_workspace_v44.py').exists():
    run(os.environ.get('WGSS_BROWSER_PYTHON',sys.executable),'tests/public_flow_evidence_v44.py')
    run(os.environ.get('WGSS_BROWSER_PYTHON',sys.executable),'tests/browser_reference_workspace_v44.py')
else:
    run(os.environ.get('WGSS_BROWSER_PYTHON',sys.executable),'tests/browser_reference_workspace_v42.py')
    run(os.environ.get('WGSS_BROWSER_PYTHON',sys.executable),'tests/browser_public_expansion_v42.py')
if (R/'tests/browser_usability_review_v45.py').exists():
    run(os.environ.get('WGSS_BROWSER_PYTHON',sys.executable),'tests/browser_usability_review_v45.py')
run(os.environ.get('WGSS_BROWSER_PYTHON',sys.executable),'tests/browser_public_guides_v46.py')
run(os.environ.get('WGSS_BROWSER_PYTHON',sys.executable),'tests/browser_public_integration_v48.py')
run(sys.executable,'tests/test_collector_gate_v45.py')
run(os.environ.get('WGSS_BROWSER_PYTHON',sys.executable),'tests/test_document_transport_v46.py')
K=json.loads((R/'dist/data/business-backbone.json').read_text());assert K['product_quality']['gates'][1]['status']=='passed'
print(json.dumps({'publication_checks':'passed','canonical_review_count':K['canonical_count'],'product_profiles':len(K['product_profiles']),'source_inventory':len(K['product_inventory']),'queries_checked':K['product_quality']['query_count'],'financial_product_readiness_approved':False,'global_mece_approved':False}))
