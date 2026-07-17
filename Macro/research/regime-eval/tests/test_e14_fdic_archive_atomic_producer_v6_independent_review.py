from __future__ import annotations
import hashlib, json, unittest
from pathlib import Path
from regime_eval.e14_post2005_source_execution_gate_v2 import _validate_schema_value
DATA = Path("../../data/historical-real-v12-2008-2025/challengers"); MODELS = Path("models")
class E14FdicArchiveAtomicProducerV6IndependentReviewTests(unittest.TestCase):
    def setUp(self):
        self.receipt=json.loads((DATA/"e14-fdic-archive-atomic-producer-v6-independent-review-v1.json").read_text()); self.schema=json.loads((MODELS/"e14-fdic-archive-atomic-producer-v6-independent-review-schema-v1.json").read_text())
    def test_closed_schema(self): _validate_schema_value(self.receipt,self.schema,self.schema,"$")
    def test_hashes_are_exact(self):
        expected={"implementationContract":MODELS/"e14-fdic-archive-atomic-producer-v6-implementation-contract-v1.json","blockedReview":DATA/"e14-fdic-archive-atomic-producer-v5-independent-review-v1.json","plan":MODELS/"e14-fdic-archive-atomic-producer-v6-plan-v1.json","auditSchema":MODELS/"e14-fdic-archive-atomic-producer-v6-audit-schema-v1.json","audit":DATA/"e14-fdic-archive-atomic-producer-v6-audit-v1.json","producer":Path("regime_eval/e14_fdic_archive_atomic_producer_v6.py"),"producerTests":Path("tests/test_e14_fdic_archive_atomic_producer_v6.py"),"auditTests":Path("tests/test_e14_fdic_archive_atomic_producer_v6_audit.py"),"testReceipt":DATA/"e14-fdic-archive-atomic-producer-v6-test-receipt-v1.json","testTranscript":DATA/"e14-fdic-archive-atomic-producer-v6-test-transcript-v1.txt","runtimeValidationContract":MODELS/"e14-fdic-archive-producer-v5-runtime-test-contract-v1.json","projectConfiguration":Path("pyproject.toml"),"reviewSchema":MODELS/"e14-fdic-archive-atomic-producer-v6-independent-review-schema-v1.json"}
        for key,path in expected.items(): self.assertEqual(self.receipt["hashes"][key],hashlib.sha256(path.read_bytes()).hexdigest(),key)
    def test_needs_changes_keeps_downstream_closed(self):
        self.assertEqual("needs_changes",self.receipt["decision"]); self.assertEqual(7,len(self.receipt["blockingFindings"])); self.assertFalse(self.receipt["assessments"]["coordinatedLedgerAnchorRollbackPrevented"]); self.assertFalse(self.receipt["assessments"]["postTargetRenameCrashRecoverable"]); self.assertTrue(self.receipt["assessments"]["downstreamStillClosed"])
if __name__=="__main__": unittest.main()
