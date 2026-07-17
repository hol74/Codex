from __future__ import annotations
import json, tempfile, unittest
from pathlib import Path
from regime_eval.dataset import DatasetValidationError
from regime_eval.e14_external_monotonic_authority import PINNED_PRODUCTION_AUTHORITIES, verify_provisioned_authority
from regime_eval.e14_fdic_archive_atomic_producer_v7 import publish_bundle_v7
from regime_eval.e14_post2005_source_execution_gate_v2 import _validate_schema_value

MODELS=Path("models")
class E14FdicArchiveAtomicProducerV7Tests(unittest.TestCase):
    def setUp(self):
        self.schema=json.loads((MODELS/"e14-external-monotonic-authority-contract-schema-v1.json").read_text())
        self.fake={"schemaVersion":1,"authorityId":"caller-authority-0001","deploymentId":"caller-deployment-0001","endpointIdentity":"caller-endpoint-0001","capabilities":{key:True for key in self.schema["properties"]["capabilities"]["required"]},"authorizationPolicy":{"productionPublicationAuthorized":False,"providerNetworkCaptureAuthorized":False,"discoveryCatalogAuthorized":False,"executionGateAuthorized":False,"sourceAcquisitionAuthorized":False}}
    def test_production_authority_registry_is_intentionally_empty(self): self.assertEqual({},PINNED_PRODUCTION_AUTHORITIES)
    def test_contract_schema_requires_all_external_guarantees(self): _validate_schema_value(self.fake,self.schema,self.schema,"$")
    def test_caller_cannot_self_pin_authority(self):
        with self.assertRaisesRegex(DatasetValidationError,"no deployment-pinned"):
            verify_provisioned_authority((json.dumps(self.fake)+"\n").encode())
    def test_publication_fails_before_target_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory)/"forbidden"
            with self.assertRaisesRegex(DatasetValidationError,"no deployment-pinned"):
                publish_bundle_v7(authority_contract_raw=(json.dumps(self.fake)+"\n").encode(),target_dir=target)
            self.assertFalse(target.exists())
    def test_local_v6_anchor_is_not_registered_as_authority(self): self.assertNotIn("local-v6",PINNED_PRODUCTION_AUTHORITIES)
if __name__=="__main__": unittest.main()
