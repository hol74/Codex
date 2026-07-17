from __future__ import annotations
import hashlib,json,unittest
from pathlib import Path
from regime_eval.e14_post2005_source_execution_gate_v2 import _validate_schema_value
DATA=Path("../../data/historical-real-v12-2008-2025/challengers"); MODELS=Path("models")
class E14FdicArchiveAtomicProducerV7AuditTests(unittest.TestCase):
 def setUp(self): self.audit=json.loads((DATA/"e14-fdic-archive-atomic-producer-v7-audit-v1.json").read_text()); self.schema=json.loads((MODELS/"e14-fdic-archive-atomic-producer-v7-audit-schema-v1.json").read_text())
 def test_closed_schema(self): _validate_schema_value(self.audit,self.schema,self.schema,"$")
 def test_hashes_exact(self):
  expected={"blockedReview":DATA/"e14-fdic-archive-atomic-producer-v6-independent-review-v1.json","authoritySchema":MODELS/"e14-external-monotonic-authority-contract-schema-v1.json","plan":MODELS/"e14-fdic-archive-atomic-producer-v7-plan-v1.json","authorityVerifier":Path("regime_eval/e14_external_monotonic_authority.py"),"producer":Path("regime_eval/e14_fdic_archive_atomic_producer_v7.py"),"tests":Path("tests/test_e14_fdic_archive_atomic_producer_v7.py"),"projectConfiguration":Path("pyproject.toml")}
  for key,path in expected.items(): self.assertEqual(self.audit["hashes"][key],hashlib.sha256(path.read_bytes()).hexdigest(),key)
 def test_everything_stays_closed(self): self.assertEqual(0,self.audit["protocol"]["authoritiesProvisioned"]); self.assertFalse(self.audit["decision"]["externalProvisioningAuthorized"]); self.assertFalse(self.audit["decision"]["downstreamAuthorized"])
if __name__=="__main__": unittest.main()
