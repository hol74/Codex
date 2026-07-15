from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .baseline import write_baseline_report
from .baseline_audit import write_baseline_audit
from .challenger import write_clustering_challenger_report
from .dataset import DatasetValidationError, load_dataset, write_manifest
from .dimensional_baseline import write_dimensional_baseline_gate
from .dual_timescale_challenger import write_dual_timescale_report
from .evidence import write_model_evidence_report
from .e11_challengers import write_e11_challenger_gate
from .e12_foundation import write_e12_foundation_report
from .e12_financial_stress import (
    write_e12_financial_preregistration,
    write_e12_financial_stress_gate,
)
from .e12_recession_hazard import (
    write_e12_recession_hazard_gate,
    write_e12_recession_preregistration,
)
from .e13_generator import write_e13_candidate_manifest
from .e13_loeo import write_e13_loeo_report
from .e13_shortlist import write_e13_shortlist
from .e13_gate import write_e13_financial_gate_decisions
from .e14_information_audit import write_e14_information_audit
from .e14_label_audit import write_e14_label_audit
from .e14_label_foundation_gate import write_e14_label_foundation_gate
from .e14_candidate_readiness import write_e14_candidate_readiness_gate
from .e14_feature_foundation import write_e14_feature_foundation
from .e14_feature_foundation_v2 import write_e14_feature_foundation_v2
from .e14_readiness_v2 import write_e14_readiness_v2
from .e14_candidate_protocol import write_e14_candidate_protocol_readiness
from .e14_candidate_generator import write_e14_candidate_manifest
from .e14_loeo_preregistration import write_e14_loeo_preregistration_audit
from .e14_coverage_repair import write_e14_coverage_repair_audit
from .e14_taxonomy_v4 import write_e14_taxonomy_v4
from .e14_taxonomy_v5 import write_e14_taxonomy_v5
from .e14_hard_negative_expansion import write_e14_hard_negative_expansion
from .e14_hard_negative_expansion_handoff import write_e14_hard_negative_expansion_handoff
from .e14_hard_negative_expansion_review_ingestion import (
    write_e14_hard_negative_expansion_review_ingestion,
)
from .e14_hard_negative_targeted_revision import write_e14_hard_negative_targeted_revision
from .e14_hard_negative_targeted_review_ingestion import (
    write_e14_hard_negative_targeted_review_ingestion,
)
from .e14_hard_negative_coverage_gate import write_e14_hard_negative_coverage_gate
from .e14_historical_feasibility import write_e14_historical_feasibility
from .e14_mechanism_contract import write_e14_mechanism_contract_audit
from .e14_dossier_curation import write_e14_positive_dossier_curation
from .e14_adjudication import write_e14_adjudication_queue
from .e14_review_handoff import write_e14_review_handoff_bundle
from .e14_review_ingestion import write_e14_review_ingestion
from .e14_targeted_revision import write_e14_targeted_revision
from .e14_targeted_review_ingestion import write_e14_targeted_review_ingestion
from .ground_truth import write_recession_report
from .hmm_challenger import write_hmm_challenger_report
from .preregistration import write_preregistration_manifest
from .shadow import (
    write_baseline_prediction_ledger,
    write_gate_decision,
    write_shadow_score,
)
from .shadow_ops import ensure_shadow_ledger, write_shadow_index, write_shadow_preflight
from .shadow_orchestrator import run_shadow_operations
from .stress import write_stress_report
from .train_gate import write_baseline_train_gate
from .walk_forward import WalkForwardConfig, build_walk_forward_plan


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "e14-readiness-gate-v2":
            roster, output = write_e14_readiness_v2(
                args.contract, args.taxonomy, args.foundation,
                args.foundation_lock, args.foundation_audit,
                args.candidate_manifest_v1, args.repair_plan,
                args.readiness_policy, args.readiness_policy_schema,
                args.roster_schema, args.roster_output, args.output,
            )
            print(roster)
            print(output)
            report = json.loads(output.read_text(encoding="utf-8"))
            return 0 if report["decision"]["fullFourMechanismReadiness"] else 3
        if args.command == "e14-materialize-feature-foundation-v2":
            foundation, lock, output = write_e14_feature_foundation_v2(
                args.contract, args.taxonomy, args.foundation_v1,
                args.foundation_lock_v1, args.repair_plan, args.repair_audit,
                args.foundation_schema, args.raw_dir, args.foundation_output,
                args.lock_output, args.output,
            )
            print(foundation)
            print(lock)
            print(output)
            report = json.loads(output.read_text(encoding="utf-8"))
            return 0 if report["decision"]["featureFoundationV2Materialized"] else 3
        if args.command == "e14-preregister-coverage-repair":
            output = write_e14_coverage_repair_audit(
                args.contract, args.taxonomy, args.foundation,
                args.preregistration, args.loeo_audit, args.repair_plan,
                args.repair_schema, args.output,
            )
            print(output)
            return 0
        if args.command == "e14-preregister-loeo":
            output = write_e14_loeo_preregistration_audit(
                args.contract, args.taxonomy, args.candidate_manifest,
                args.foundation, args.foundation_lock, args.candidate_protocol,
                args.preregistration, args.preregistration_schema, args.output,
            )
            print(output)
            report = json.loads(output.read_text(encoding="utf-8"))
            return 0 if report["decision"]["fullFourMechanismReadiness"] else 3
        if args.command == "e14-generate-candidates":
            output = write_e14_candidate_manifest(
                args.contract, args.protocol, args.readiness_audit,
                args.foundation, args.foundation_lock, args.manifest_schema,
                args.output,
            )
            print(output)
            return 0
        if args.command == "e14-freeze-candidate-protocol":
            output = write_e14_candidate_protocol_readiness(
                args.contract, args.taxonomy, args.foundation,
                args.foundation_lock, args.foundation_audit,
                args.mechanism_contract, args.protocol,
                args.protocol_schema, args.output,
            )
            print(output)
            report = json.loads(output.read_text(encoding="utf-8"))
            return 0 if report["decision"]["researchCandidateGenerationReady"] else 3
        if args.command == "e14-materialize-feature-foundation":
            foundation, lock, output = write_e14_feature_foundation(
                args.contract, args.taxonomy, args.readiness_audit,
                args.mechanism_contract, args.source_catalog,
                args.foundation_schema, args.raw_dir, args.foundation_output,
                args.lock_output, args.output,
            )
            print(foundation)
            print(lock)
            print(output)
            report = json.loads(output.read_text(encoding="utf-8"))
            return 0 if report["decision"]["featureFoundationMaterialized"] else 3
        if args.command == "e14-candidate-readiness-gate":
            output = write_e14_candidate_readiness_gate(
                args.contract, args.taxonomy, args.materialization_audit,
                args.mechanism_contract, args.source_catalog,
                args.legacy_candidate_protocol, args.legacy_foundation_lock,
                args.output,
            )
            print(output)
            report = json.loads(output.read_text(encoding="utf-8"))
            return 0 if report["decision"]["candidateReadinessSatisfied"] else 3
        if args.command == "e14-materialize-taxonomy-v5":
            taxonomy, output = write_e14_taxonomy_v5(
                args.contract, args.taxonomy_v4, args.coverage_gate_audit,
                args.reviewed_queue, args.taxonomy_v4_schema,
                args.taxonomy_v5_schema, args.label_audit_contract,
                args.mechanism_contract, args.taxonomy_output, args.output,
            )
            print(taxonomy)
            print(output)
            report = json.loads(output.read_text(encoding="utf-8"))
            return 0 if report["decision"]["taxonomyV5Ready"] else 3
        if args.command == "e14-hard-negative-coverage-gate":
            output = write_e14_hard_negative_coverage_gate(
                args.contract, args.reviewed_queue, args.targeted_ingestion_audit,
                args.taxonomy, args.dossier_schema, args.label_audit_contract,
                args.mechanism_contract, args.expansion_contract, args.dossier_dir,
                args.output,
            )
            print(output)
            report = json.loads(output.read_text(encoding="utf-8"))
            return 0 if report["decision"]["acceptedHardNegativeCoverageSufficient"] else 3
        if args.command == "e14-ingest-hard-negative-targeted-reviews":
            queue, output = write_e14_hard_negative_targeted_review_ingestion(
                args.contract, args.targeted_queue, args.revision_audit,
                args.revision_pack, args.review_schema, args.receipt_dir,
                args.queue_output, args.output,
            )
            if queue is not None:
                print(queue)
            print(output)
            report = json.loads(output.read_text(encoding="utf-8"))
            return 0 if report["decision"]["independentReviewComplete"] else 3
        if args.command == "e14-revise-hard-negative-expansion":
            queue, output = write_e14_hard_negative_targeted_revision(
                args.pack, args.reviewed_queue, args.review_ingestion_audit,
                args.dossier_schema, args.review_schema, args.base_dossier_dir,
                args.revised_dossier_dir, args.bundle_dir, args.queue_output, args.output,
            )
            print(queue)
            print(output)
            return 0
        if args.command == "e14-ingest-hard-negative-expansion-reviews":
            queue, output = write_e14_hard_negative_expansion_review_ingestion(
                args.contract,
                args.review_queue,
                args.curation_audit,
                args.handoff_audit,
                args.handoff_contract,
                args.review_schema,
                args.receipt_dir,
                args.queue_output,
                args.output,
            )
            if queue is not None:
                print(queue)
            print(output)
            report = json.loads(output.read_text(encoding="utf-8"))
            return 0 if report["decision"]["independentReviewComplete"] else 3
        if args.command == "e14-build-hard-negative-expansion-handoff":
            output = write_e14_hard_negative_expansion_handoff(
                args.contract,
                args.review_queue,
                args.curation_audit,
                args.expansion_contract,
                args.review_schema,
                args.dossier_schema,
                args.expansion_dossier_dir,
                args.bundle_dir,
                args.output,
            )
            print(output)
            return 0
        if args.command == "e14-curate-hard-negative-expansion":
            queue, output = write_e14_hard_negative_expansion(
                args.contract, args.pack, args.taxonomy, args.materialization_audit,
                args.reviewed_queue, args.dossier_schema, args.review_schema,
                args.label_audit_contract, args.mechanism_contract,
                args.dossier_output_dir, args.queue_output, args.output,
            )
            print(queue)
            print(output)
            report = json.loads(output.read_text(encoding="utf-8"))
            return 0 if report["decision"]["potentialCoverageSufficientIfAllAccepted"] else 3
        if args.command == "e14-materialize-taxonomy-v4":
            taxonomy, output = write_e14_taxonomy_v4(
                args.contract, args.taxonomy_v3, args.foundation_proposal,
                args.foundation_gate_audit, args.proposal_schema,
                args.taxonomy_schema, args.label_audit_contract,
                args.mechanism_contract, args.taxonomy_output, args.output,
            )
            print(taxonomy)
            print(output)
            report = json.loads(output.read_text(encoding="utf-8"))
            return 0 if report["decision"]["taxonomyV4Ready"] else 3
        if args.command == "e14-label-foundation-gate":
            proposal, output = write_e14_label_foundation_gate(
                args.contract, args.reviewed_queue, args.targeted_ingestion_audit,
                args.taxonomy, args.dossier_schema, args.proposal_schema,
                args.label_audit_contract, args.mechanism_contract,
                args.positive_dossier_dir, args.hard_negative_dossier_dir,
                args.revised_dossier_dir, args.proposal_output, args.output,
            )
            print(proposal)
            print(output)
            report = json.loads(output.read_text(encoding="utf-8"))
            return 0 if report["decision"]["foundationMergeAuthorized"] else 3
        if args.command == "e14-ingest-targeted-reviews":
            queue, output = write_e14_targeted_review_ingestion(
                args.contract, args.targeted_queue, args.revision_audit,
                args.review_schema, args.receipt_dir, args.queue_output, args.output,
            )
            print(queue)
            print(output)
            report = json.loads(output.read_text(encoding="utf-8"))
            return 0 if report["decision"]["labelFoundationGateAuthorized"] else 3
        if args.command == "e14-targeted-dossier-revision":
            queue, output = write_e14_targeted_revision(
                args.contract, args.reviewed_queue, args.review_ingestion_audit,
                args.dossier_schema, args.positive_dossier_dir,
                args.hard_negative_dossier_dir, args.revised_dossier_dir,
                args.bundle_dir, args.queue_output, args.output,
            )
            print(queue)
            print(output)
            return 0
        if args.command == "e14-ingest-independent-reviews":
            queue, output = write_e14_review_ingestion(
                args.contract, args.review_queue, args.adjudication_audit,
                args.handoff_audit, args.review_schema, args.receipt_dir,
                args.queue_output, args.output,
            )
            print(queue)
            print(output)
            report = json.loads(output.read_text(encoding="utf-8"))
            return 0 if report["decision"]["labelFoundationGateAuthorized"] else 3
        if args.command == "e14-build-review-handoff":
            output = write_e14_review_handoff_bundle(
                args.contract, args.review_queue, args.adjudication_audit,
                args.review_schema, args.dossier_schema, args.positive_dossier_dir,
                args.hard_negative_dossier_dir, args.bundle_dir, args.output,
            )
            print(output)
            return 0
        if args.command == "e14-adjudication-queue":
            queue, output = write_e14_adjudication_queue(
                args.hard_negative_pack, args.dossier_schema, args.review_schema,
                args.detector_contract, args.positive_pack, args.positive_curation_audit,
                args.positive_dossier_dir, args.hard_negative_dossier_dir,
                args.review_receipt_dir, args.queue_output, args.output,
            )
            print(queue)
            print(output)
            report = json.loads(output.read_text(encoding="utf-8"))
            return 0 if report["decision"]["labelFoundationGateAuthorized"] else 3
        if args.command == "e14-curate-positive-dossiers":
            output = write_e14_positive_dossier_curation(
                args.pack, args.dossier_schema, args.detector_contract,
                args.source_catalog, args.contract_audit, args.dossier_dir, args.output,
            )
            print(output)
            report = json.loads(output.read_text(encoding="utf-8"))
            return 0 if report["decision"]["groundTruthMutationAuthorized"] else 3
        if args.command == "e14-mechanism-contract-audit":
            output = write_e14_mechanism_contract_audit(
                args.detector_contract, args.dossier_schema, args.source_catalog,
                args.feasibility_report, args.taxonomy, args.output,
            )
            print(output)
            return 0
        if args.command == "e14-historical-feasibility":
            output = write_e14_historical_feasibility(
                args.catalog, args.taxonomy, args.label_audit, args.contract, args.output,
            )
            print(output)
            report = json.loads(output.read_text(encoding="utf-8"))
            return 0 if report["decision"]["fullCorpusPopulationAuthorized"] else 3
        if args.command == "e14-label-audit":
            output = write_e14_label_audit(
                args.taxonomy, args.information_audit, args.dataset, args.plan,
                args.contract, args.output,
            )
            print(output)
            report = json.loads(output.read_text(encoding="utf-8"))
            return 0 if report["decision"]["ready"] else 3
        if args.command == "e14-information-audit":
            output = write_e14_information_audit(
                args.dataset, args.plan, args.stress_truth, args.recession_truth,
                args.foundation_lock, args.e13_decisions, args.contract, args.output,
            )
            print(output)
            return 0
        if args.command == "e13-financial-absolute-gate":
            output = write_e13_financial_gate_decisions(
                args.shortlist, args.loeo_report, args.gate, args.output,
            )
            print(output)
            report = json.loads(output.read_text(encoding="utf-8"))
            return 0 if report["protocol"]["passedCount"] > 0 else 3
        if args.command == "e13-freeze-shortlist":
            output = write_e13_shortlist(
                args.loeo_report, args.evaluation_contract, args.manifest,
                args.shortlist_contract, args.output,
            )
            print(output)
            return 0
        if args.command == "e13-loeo-evaluate":
            output = write_e13_loeo_report(
                args.dataset, args.plan, args.stress_truth, args.recession_truth,
                args.protocol, args.manifest, args.foundation_lock,
                args.evaluation_contract, args.output,
            )
            print(output)
            return 0
        if args.command == "e13-generate-candidates":
            output = write_e13_candidate_manifest(args.protocol, args.output)
            print(output)
            return 0
        if args.command == "e12-preregister-recession-hazard":
            output = write_e12_recession_preregistration(
                args.candidate, args.gate, args.foundation_lock, args.output
            )
            print(output)
            return 0
        if args.command == "e12-recession-hazard-gate":
            output = write_e12_recession_hazard_gate(
                args.dataset, args.plan, args.recession_truth, args.candidate,
                args.gate, args.foundation_lock, args.foundation_freeze,
                args.preregistration, args.output,
            )
            print(output)
            report = json.loads(output.read_text(encoding="utf-8"))
            return 0 if report["gate"]["passed"] else 3
        if args.command == "e12-preregister-financial-stress":
            output = write_e12_financial_preregistration(
                args.candidate, args.gate, args.foundation_lock, args.output
            )
            print(output)
            return 0
        if args.command == "e12-financial-stress-gate":
            output = write_e12_financial_stress_gate(
                args.dataset, args.plan, args.stress_truth, args.candidate,
                args.gate, args.foundation_lock, args.foundation_freeze,
                args.preregistration, args.output,
            )
            print(output)
            report = json.loads(output.read_text(encoding="utf-8"))
            return 0 if report["gate"]["passed"] else 3
        if args.command == "e12-freeze-foundation":
            output = write_e12_foundation_report(
                args.corpus_manifest,
                args.dataset,
                args.plan,
                args.lifecycle,
                args.output,
            )
            print(output)
            return 0
        if args.command == "e11-preregister":
            output = write_preregistration_manifest(
                args.gate, args.model_config, args.output
            )
            print(output)
            return 0
        if args.command == "e11-dimensional-baseline-gate":
            output = write_dimensional_baseline_gate(
                args.evaluation,
                args.dataset,
                args.plan,
                args.recession_truth,
                args.stress_truth,
                args.candidate,
                args.geometry,
                args.gate,
                args.manifest,
                args.output,
            )
            print(output)
            report = json.loads(output.read_text(encoding="utf-8"))
            return 0 if report["gate"]["passed"] else 3
        if args.command == "e11-challenger-gate":
            output = write_e11_challenger_gate(
                args.evaluation,
                args.dataset,
                args.plan,
                args.recession_truth,
                args.stress_truth,
                args.candidate,
                args.gate,
                args.manifest,
                args.output,
            )
            print(output)
            report = json.loads(output.read_text(encoding="utf-8"))
            return 0 if report["gate"]["passed"] else 3
        if args.command == "baseline-report":
            output = write_baseline_report(args.evaluation, args.dataset, args.plan, args.output)
            print(output)
            return 0
        if args.command == "baseline-audit":
            output = write_baseline_audit(
                args.evaluation, args.dataset, args.plan, args.config, args.output
            )
            print(output)
            report = json.loads(output.read_text(encoding="utf-8"))
            return 0 if report["gate"]["passed"] else 3
        if args.command == "baseline-train-gate":
            output = write_baseline_train_gate(
                args.evaluation, args.dataset, args.plan, args.config, args.output
            )
            print(output)
            report = json.loads(output.read_text(encoding="utf-8"))
            return 0 if report["gate"]["eligibleForOuterOos"] else 3
        if args.command == "recession-report":
            output = write_recession_report(
                args.evaluation, args.dataset, args.plan, args.ground_truth, args.output
            )
            print(output)
            return 0
        if args.command == "stress-report":
            output = write_stress_report(
                args.evaluation,
                args.dataset,
                args.plan,
                args.stress_truth,
                args.recession_truth,
                args.output,
            )
            print(output)
            return 0
        if args.command == "evidence-report":
            output = write_model_evidence_report(
                args.evaluation,
                args.dataset,
                args.plan,
                args.ground_truth,
                args.policy,
                args.output,
            )
            print(output)
            report = json.loads(output.read_text(encoding="utf-8"))
            return 0 if report["promotionGate"]["status"] == "ELIGIBLE_FOR_HUMAN_REVIEW" else 3
        if args.command == "clustering-report":
            output = write_clustering_challenger_report(
                args.evaluation, args.dataset, args.plan, args.ground_truth, args.config, args.output
            )
            print(output)
            return 0
        if args.command == "hmm-report":
            output = write_hmm_challenger_report(
                args.evaluation, args.dataset, args.plan, args.ground_truth, args.config, args.output
            )
            print(output)
            return 0
        if args.command == "dual-timescale-report":
            output = write_dual_timescale_report(
                args.evaluation,
                args.dataset,
                args.plan,
                args.recession_truth,
                args.stress_truth,
                args.config,
                args.output,
            )
            print(output)
            return 3
        if args.command == "shadow-predict":
            output = write_baseline_prediction_ledger(
                args.evaluation,
                args.dataset,
                args.model_config,
                args.as_of,
                args.generated_at_utc,
                args.run_mode,
                args.output,
                args.preflight,
            )
            print(output)
            return 0
        if args.command == "shadow-preflight":
            output = write_shadow_preflight(
                args.evaluation,
                args.dataset,
                args.model_config,
                args.as_of,
                args.generated_at_utc,
                args.source_root,
                args.output,
            )
            print(output)
            return 0
        if args.command == "shadow-cycle":
            output = ensure_shadow_ledger(
                args.evaluation,
                args.dataset,
                args.model_config,
                args.preflight,
                args.as_of,
                args.generated_at_utc,
                args.output,
            )
            index = write_shadow_index(Path(args.output).parent, args.index)
            print(output)
            print(index)
            return 0
        if args.command == "shadow-index":
            output = write_shadow_index(args.ledger_dir, args.output)
            print(output)
            return 0
        if args.command == "shadow-operations":
            output = run_shadow_operations(
                args.source_root,
                args.operations_root,
                args.model_config,
                args.generated_at_utc,
                args.mode,
                args.result,
                args.dotnet,
            )
            print(output)
            result = json.loads(output.read_text(encoding="utf-8"))
            return 4 if result["status"] == "failed" else 0
        if args.command == "shadow-score":
            output = write_shadow_score(
                args.ledger,
                args.ground_truth,
                args.scored_at_utc,
                args.output,
            )
            print(output)
            return 0
        if args.command == "gate-decision":
            output = write_gate_decision(
                args.report,
                args.decision,
                args.reviewer,
                args.rationale,
                args.decided_at_utc,
                args.output,
            )
            print(output)
            return 0
        dataset = load_dataset(args.dataset)
        if args.command == "validate":
            print(json.dumps(dataset.manifest(), indent=2, sort_keys=True))
        elif args.command == "manifest":
            output = write_manifest(dataset, args.output)
            print(output)
        elif args.command == "plan-walk-forward":
            config = WalkForwardConfig(args.train_years, args.test_years, args.step_years)
            folds = build_walk_forward_plan(dataset.dates, config)
            payload = json.dumps(
                {"config": {"dataset": str(Path(args.dataset)),
                            "trainYears": args.train_years,
                            "testYears": args.test_years,
                            "stepYears": args.step_years},
                 "foldCount": len(folds),
                 "folds": [fold.to_dict() for fold in folds]},
                indent=2,
                sort_keys=True,
                default=str,
            )
            if args.output:
                output = Path(args.output)
                output.parent.mkdir(parents=True, exist_ok=True)
                output.write_text(payload + "\n", encoding="utf-8")
                print(output)
            else:
                print(payload)
            if not folds:
                print("Dataset coverage is insufficient for one complete walk-forward fold.", file=sys.stderr)
                return 2
        return 0
    except DatasetValidationError as exc:
        print(f"Dataset validation failed: {exc}", file=sys.stderr)
        return 2


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Macro Regime research data gate")
    subparsers = parser.add_subparsers(dest="command", required=True)
    validate = subparsers.add_parser("validate", help="validate and summarize a dataset")
    validate.add_argument("dataset")
    manifest = subparsers.add_parser("manifest", help="write a reproducibility manifest")
    manifest.add_argument("dataset")
    manifest.add_argument("--output", required=True)
    e13_generate = subparsers.add_parser(
        "e13-generate-candidates",
        help="expand the frozen E13 grammar into an immutable candidate manifest",
    )
    e13_generate.add_argument("--protocol", required=True)
    e13_generate.add_argument("--output", required=True)
    e13_loeo = subparsers.add_parser(
        "e13-loeo-evaluate",
        help="evaluate the frozen E13 population with inner-only leave-one-episode-out",
    )
    e13_loeo.add_argument("--dataset", required=True)
    e13_loeo.add_argument("--plan", required=True)
    e13_loeo.add_argument("--stress-truth", required=True)
    e13_loeo.add_argument("--recession-truth", required=True)
    e13_loeo.add_argument("--protocol", required=True)
    e13_loeo.add_argument("--manifest", required=True)
    e13_loeo.add_argument("--foundation-lock", required=True)
    e13_loeo.add_argument("--evaluation-contract", required=True)
    e13_loeo.add_argument("--output", required=True)
    e13_shortlist = subparsers.add_parser(
        "e13-freeze-shortlist",
        help="freeze at most two complementary E13 Pareto candidates per eligible task",
    )
    e13_shortlist.add_argument("--loeo-report", required=True)
    e13_shortlist.add_argument("--evaluation-contract", required=True)
    e13_shortlist.add_argument("--manifest", required=True)
    e13_shortlist.add_argument("--shortlist-contract", required=True)
    e13_shortlist.add_argument("--output", required=True)
    e13_gate = subparsers.add_parser(
        "e13-financial-absolute-gate",
        help="apply independent absolute gates to the frozen E13 financial shortlist",
    )
    e13_gate.add_argument("--shortlist", required=True)
    e13_gate.add_argument("--loeo-report", required=True)
    e13_gate.add_argument("--gate", required=True)
    e13_gate.add_argument("--output", required=True)
    e14_audit = subparsers.add_parser(
        "e14-information-audit",
        help="diagnose E13 feature, label and episode limitations without generating candidates",
    )
    e14_audit.add_argument("--dataset", required=True)
    e14_audit.add_argument("--plan", required=True)
    e14_audit.add_argument("--stress-truth", required=True)
    e14_audit.add_argument("--recession-truth", required=True)
    e14_audit.add_argument("--foundation-lock", required=True)
    e14_audit.add_argument("--e13-decisions", required=True)
    e14_audit.add_argument("--contract", required=True)
    e14_audit.add_argument("--output", required=True)
    e14_labels = subparsers.add_parser(
        "e14-label-audit",
        help="audit tri-state labels, mechanism coverage and explicit hard negatives",
    )
    e14_labels.add_argument("--taxonomy", required=True)
    e14_labels.add_argument("--information-audit", required=True)
    e14_labels.add_argument("--dataset", required=True)
    e14_labels.add_argument("--plan", required=True)
    e14_labels.add_argument("--contract", required=True)
    e14_labels.add_argument("--output", required=True)
    e14_feasibility = subparsers.add_parser(
        "e14-historical-feasibility",
        help="gate historical point-in-time sources and pre-2008 episode hypotheses",
    )
    e14_feasibility.add_argument("--catalog", required=True)
    e14_feasibility.add_argument("--taxonomy", required=True)
    e14_feasibility.add_argument("--label-audit", required=True)
    e14_feasibility.add_argument("--contract", required=True)
    e14_feasibility.add_argument("--output", required=True)
    e14_mechanisms = subparsers.add_parser(
        "e14-mechanism-contract-audit",
        help="audit independent mechanism detectors and the episode-dossier schema",
    )
    e14_mechanisms.add_argument("--detector-contract", required=True)
    e14_mechanisms.add_argument("--dossier-schema", required=True)
    e14_mechanisms.add_argument("--source-catalog", required=True)
    e14_mechanisms.add_argument("--feasibility-report", required=True)
    e14_mechanisms.add_argument("--taxonomy", required=True)
    e14_mechanisms.add_argument("--output", required=True)
    e14_dossiers = subparsers.add_parser(
        "e14-curate-positive-dossiers",
        help="curate reviewed positive episode dossiers from frozen primary-source assertions",
    )
    e14_dossiers.add_argument("--pack", required=True)
    e14_dossiers.add_argument("--dossier-schema", required=True)
    e14_dossiers.add_argument("--detector-contract", required=True)
    e14_dossiers.add_argument("--source-catalog", required=True)
    e14_dossiers.add_argument("--contract-audit", required=True)
    e14_dossiers.add_argument("--dossier-dir", required=True)
    e14_dossiers.add_argument("--output", required=True)
    e14_adjudication = subparsers.add_parser(
        "e14-adjudication-queue",
        help="curate affirmative hard negatives and build the independent-review queue",
    )
    e14_adjudication.add_argument("--hard-negative-pack", required=True)
    e14_adjudication.add_argument("--dossier-schema", required=True)
    e14_adjudication.add_argument("--review-schema", required=True)
    e14_adjudication.add_argument("--detector-contract", required=True)
    e14_adjudication.add_argument("--positive-pack", required=True)
    e14_adjudication.add_argument("--positive-curation-audit", required=True)
    e14_adjudication.add_argument("--positive-dossier-dir", required=True)
    e14_adjudication.add_argument("--hard-negative-dossier-dir", required=True)
    e14_adjudication.add_argument("--review-receipt-dir", required=True)
    e14_adjudication.add_argument("--queue-output", required=True)
    e14_adjudication.add_argument("--output", required=True)
    e14_handoff = subparsers.add_parser(
        "e14-build-review-handoff",
        help="build an immutable external-review bundle without performing the review",
    )
    e14_handoff.add_argument("--contract", required=True)
    e14_handoff.add_argument("--review-queue", required=True)
    e14_handoff.add_argument("--adjudication-audit", required=True)
    e14_handoff.add_argument("--review-schema", required=True)
    e14_handoff.add_argument("--dossier-schema", required=True)
    e14_handoff.add_argument("--positive-dossier-dir", required=True)
    e14_handoff.add_argument("--hard-negative-dossier-dir", required=True)
    e14_handoff.add_argument("--bundle-dir", required=True)
    e14_handoff.add_argument("--output", required=True)
    e14_ingestion = subparsers.add_parser(
        "e14-ingest-independent-reviews",
        help="validate independent review receipts v2 and freeze review decisions",
    )
    e14_ingestion.add_argument("--contract", required=True)
    e14_ingestion.add_argument("--review-queue", required=True)
    e14_ingestion.add_argument("--adjudication-audit", required=True)
    e14_ingestion.add_argument("--handoff-audit", required=True)
    e14_ingestion.add_argument("--review-schema", required=True)
    e14_ingestion.add_argument("--receipt-dir", required=True)
    e14_ingestion.add_argument("--queue-output", required=True)
    e14_ingestion.add_argument("--output", required=True)
    e14_revision = subparsers.add_parser(
        "e14-targeted-dossier-revision",
        help="revise only needs-revision dossier hashes and build a targeted rereview bundle",
    )
    e14_revision.add_argument("--contract", required=True)
    e14_revision.add_argument("--reviewed-queue", required=True)
    e14_revision.add_argument("--review-ingestion-audit", required=True)
    e14_revision.add_argument("--dossier-schema", required=True)
    e14_revision.add_argument("--positive-dossier-dir", required=True)
    e14_revision.add_argument("--hard-negative-dossier-dir", required=True)
    e14_revision.add_argument("--revised-dossier-dir", required=True)
    e14_revision.add_argument("--bundle-dir", required=True)
    e14_revision.add_argument("--queue-output", required=True)
    e14_revision.add_argument("--output", required=True)
    e14_targeted_ingestion = subparsers.add_parser(
        "e14-ingest-targeted-reviews",
        help="ingest only receipts for revised E14 hashes and preserve prior accepts",
    )
    e14_targeted_ingestion.add_argument("--contract", required=True)
    e14_targeted_ingestion.add_argument("--targeted-queue", required=True)
    e14_targeted_ingestion.add_argument("--revision-audit", required=True)
    e14_targeted_ingestion.add_argument("--review-schema", required=True)
    e14_targeted_ingestion.add_argument("--receipt-dir", required=True)
    e14_targeted_ingestion.add_argument("--queue-output", required=True)
    e14_targeted_ingestion.add_argument("--output", required=True)
    e14_coverage = subparsers.add_parser(
        "e14-hard-negative-coverage-gate",
        help="audit accepted E14 hard-negative coverage without mutating taxonomy or generating candidates",
    )
    e14_coverage.add_argument("--contract", required=True)
    e14_coverage.add_argument("--reviewed-queue", required=True)
    e14_coverage.add_argument("--targeted-ingestion-audit", required=True)
    e14_coverage.add_argument("--taxonomy", required=True)
    e14_coverage.add_argument("--dossier-schema", required=True)
    e14_coverage.add_argument("--label-audit-contract", required=True)
    e14_coverage.add_argument("--mechanism-contract", required=True)
    e14_coverage.add_argument("--expansion-contract", required=True)
    e14_coverage.add_argument("--dossier-dir", action="append", required=True)
    e14_coverage.add_argument("--output", required=True)
    e14_foundation = subparsers.add_parser(
        "e14-label-foundation-gate",
        help="derive a mechanism-month label proposal from accepted E14 dossiers without mutating ground truth",
    )
    e14_foundation.add_argument("--contract", required=True)
    e14_foundation.add_argument("--reviewed-queue", required=True)
    e14_foundation.add_argument("--targeted-ingestion-audit", required=True)
    e14_foundation.add_argument("--taxonomy", required=True)
    e14_foundation.add_argument("--dossier-schema", required=True)
    e14_foundation.add_argument("--proposal-schema", required=True)
    e14_foundation.add_argument("--label-audit-contract", required=True)
    e14_foundation.add_argument("--mechanism-contract", required=True)
    e14_foundation.add_argument("--positive-dossier-dir", required=True)
    e14_foundation.add_argument("--hard-negative-dossier-dir", required=True)
    e14_foundation.add_argument("--revised-dossier-dir", required=True)
    e14_foundation.add_argument("--proposal-output", required=True)
    e14_foundation.add_argument("--output", required=True)
    e14_protocol = subparsers.add_parser(
        "e14-freeze-candidate-protocol",
        help="freeze and audit the taxonomy-v5-bound four-detector research candidate protocol",
    )
    e14_protocol.add_argument("--contract", required=True)
    e14_protocol.add_argument("--taxonomy", required=True)
    e14_protocol.add_argument("--foundation", required=True)
    e14_protocol.add_argument("--foundation-lock", required=True)
    e14_protocol.add_argument("--foundation-audit", required=True)
    e14_protocol.add_argument("--mechanism-contract", required=True)
    e14_protocol.add_argument("--protocol", required=True)
    e14_protocol.add_argument("--protocol-schema", required=True)
    e14_protocol.add_argument("--output", required=True)
    e14_generator = subparsers.add_parser(
        "e14-generate-candidates",
        help="generate the immutable 40-candidate E14 research manifest without fitting or evaluation",
    )
    e14_generator.add_argument("--contract", required=True)
    e14_generator.add_argument("--protocol", required=True)
    e14_generator.add_argument("--readiness-audit", required=True)
    e14_generator.add_argument("--foundation", required=True)
    e14_generator.add_argument("--foundation-lock", required=True)
    e14_generator.add_argument("--manifest-schema", required=True)
    e14_generator.add_argument("--output", required=True)
    e14_loeo = subparsers.add_parser(
        "e14-preregister-loeo",
        help="freeze E14 inner LOEO rules and audit structural candidate eligibility without fitting",
    )
    e14_loeo.add_argument("--contract", required=True)
    e14_loeo.add_argument("--taxonomy", required=True)
    e14_loeo.add_argument("--candidate-manifest", required=True)
    e14_loeo.add_argument("--foundation", required=True)
    e14_loeo.add_argument("--foundation-lock", required=True)
    e14_loeo.add_argument("--candidate-protocol", required=True)
    e14_loeo.add_argument("--preregistration", required=True)
    e14_loeo.add_argument("--preregistration-schema", required=True)
    e14_loeo.add_argument("--output", required=True)
    e14_repair = subparsers.add_parser(
        "e14-preregister-coverage-repair",
        help="audit and freeze the E14.6a structural coverage repair path without downloading or fitting",
    )
    e14_repair.add_argument("--contract", required=True)
    e14_repair.add_argument("--taxonomy", required=True)
    e14_repair.add_argument("--foundation", required=True)
    e14_repair.add_argument("--preregistration", required=True)
    e14_repair.add_argument("--loeo-audit", required=True)
    e14_repair.add_argument("--repair-plan", required=True)
    e14_repair.add_argument("--repair-schema", required=True)
    e14_repair.add_argument("--output", required=True)
    e14_foundation_v2 = subparsers.add_parser(
        "e14-materialize-feature-foundation-v2",
        help="materialize the E14.6b replacement foundation without generating or fitting candidates",
    )
    e14_foundation_v2.add_argument("--contract", required=True)
    e14_foundation_v2.add_argument("--taxonomy", required=True)
    e14_foundation_v2.add_argument("--foundation-v1", required=True)
    e14_foundation_v2.add_argument("--foundation-lock-v1", required=True)
    e14_foundation_v2.add_argument("--repair-plan", required=True)
    e14_foundation_v2.add_argument("--repair-audit", required=True)
    e14_foundation_v2.add_argument("--foundation-schema", required=True)
    e14_foundation_v2.add_argument("--raw-dir", required=True)
    e14_foundation_v2.add_argument("--foundation-output", required=True)
    e14_foundation_v2.add_argument("--lock-output", required=True)
    e14_foundation_v2.add_argument("--output", required=True)
    e14_readiness_v2 = subparsers.add_parser(
        "e14-readiness-gate-v2",
        help="audit the 28-entry E14.6c readiness roster without generating or fitting candidates",
    )
    e14_readiness_v2.add_argument("--contract", required=True)
    e14_readiness_v2.add_argument("--taxonomy", required=True)
    e14_readiness_v2.add_argument("--foundation", required=True)
    e14_readiness_v2.add_argument("--foundation-lock", required=True)
    e14_readiness_v2.add_argument("--foundation-audit", required=True)
    e14_readiness_v2.add_argument("--candidate-manifest-v1", required=True)
    e14_readiness_v2.add_argument("--repair-plan", required=True)
    e14_readiness_v2.add_argument("--readiness-policy", required=True)
    e14_readiness_v2.add_argument("--readiness-policy-schema", required=True)
    e14_readiness_v2.add_argument("--roster-schema", required=True)
    e14_readiness_v2.add_argument("--roster-output", required=True)
    e14_readiness_v2.add_argument("--output", required=True)
    e14_taxonomy_v4 = subparsers.add_parser(
        "e14-materialize-taxonomy-v4",
        help="version the accepted E14 foundation proposal into an immutable mechanism-aware taxonomy v4",
    )
    e14_taxonomy_v4.add_argument("--contract", required=True)
    e14_taxonomy_v4.add_argument("--taxonomy-v3", required=True)
    e14_taxonomy_v4.add_argument("--foundation-proposal", required=True)
    e14_taxonomy_v4.add_argument("--foundation-gate-audit", required=True)
    e14_taxonomy_v4.add_argument("--proposal-schema", required=True)
    e14_taxonomy_v4.add_argument("--taxonomy-schema", required=True)
    e14_taxonomy_v4.add_argument("--label-audit-contract", required=True)
    e14_taxonomy_v4.add_argument("--mechanism-contract", required=True)
    e14_taxonomy_v4.add_argument("--taxonomy-output", required=True)
    e14_taxonomy_v4.add_argument("--output", required=True)
    e14_taxonomy_v5 = subparsers.add_parser(
        "e14-materialize-taxonomy-v5",
        help="version the accepted hard-negative expansion into immutable E14 taxonomy v5",
    )
    e14_taxonomy_v5.add_argument("--contract", required=True)
    e14_taxonomy_v5.add_argument("--taxonomy-v4", required=True)
    e14_taxonomy_v5.add_argument("--coverage-gate-audit", required=True)
    e14_taxonomy_v5.add_argument("--reviewed-queue", required=True)
    e14_taxonomy_v5.add_argument("--taxonomy-v4-schema", required=True)
    e14_taxonomy_v5.add_argument("--taxonomy-v5-schema", required=True)
    e14_taxonomy_v5.add_argument("--label-audit-contract", required=True)
    e14_taxonomy_v5.add_argument("--mechanism-contract", required=True)
    e14_taxonomy_v5.add_argument("--taxonomy-output", required=True)
    e14_taxonomy_v5.add_argument("--output", required=True)
    e14_readiness = subparsers.add_parser(
        "e14-candidate-readiness-gate",
        help="audit whether E14 taxonomy v5 and its feature/protocol foundation can generate candidates",
    )
    e14_readiness.add_argument("--contract", required=True)
    e14_readiness.add_argument("--taxonomy", required=True)
    e14_readiness.add_argument("--materialization-audit", required=True)
    e14_readiness.add_argument("--mechanism-contract", required=True)
    e14_readiness.add_argument("--source-catalog", required=True)
    e14_readiness.add_argument("--legacy-candidate-protocol", required=True)
    e14_readiness.add_argument("--legacy-foundation-lock", required=True)
    e14_readiness.add_argument("--output", required=True)
    e14_foundation = subparsers.add_parser(
        "e14-materialize-feature-foundation",
        help="materialize the hash-bound E14 mechanism feature foundation without generating candidates",
    )
    e14_foundation.add_argument("--contract", required=True)
    e14_foundation.add_argument("--taxonomy", required=True)
    e14_foundation.add_argument("--readiness-audit", required=True)
    e14_foundation.add_argument("--mechanism-contract", required=True)
    e14_foundation.add_argument("--source-catalog", required=True)
    e14_foundation.add_argument("--foundation-schema", required=True)
    e14_foundation.add_argument("--raw-dir", required=True)
    e14_foundation.add_argument("--foundation-output", required=True)
    e14_foundation.add_argument("--lock-output", required=True)
    e14_foundation.add_argument("--output", required=True)
    e14_expansion = subparsers.add_parser(
        "e14-curate-hard-negative-expansion",
        help="curate four independent E14 hard negatives and append them to a hash-bound review queue",
    )
    e14_expansion.add_argument("--contract", required=True)
    e14_expansion.add_argument("--pack", required=True)
    e14_expansion.add_argument("--taxonomy", required=True)
    e14_expansion.add_argument("--materialization-audit", required=True)
    e14_expansion.add_argument("--reviewed-queue", required=True)
    e14_expansion.add_argument("--dossier-schema", required=True)
    e14_expansion.add_argument("--review-schema", required=True)
    e14_expansion.add_argument("--label-audit-contract", required=True)
    e14_expansion.add_argument("--mechanism-contract", required=True)
    e14_expansion.add_argument("--dossier-output-dir", required=True)
    e14_expansion.add_argument("--queue-output", required=True)
    e14_expansion.add_argument("--output", required=True)
    e14_expansion_handoff = subparsers.add_parser(
        "e14-build-hard-negative-expansion-handoff",
        help="build an immutable external-review bundle for the four E14.4e expansion dossiers",
    )
    e14_expansion_handoff.add_argument("--contract", required=True)
    e14_expansion_handoff.add_argument("--review-queue", required=True)
    e14_expansion_handoff.add_argument("--curation-audit", required=True)
    e14_expansion_handoff.add_argument("--expansion-contract", required=True)
    e14_expansion_handoff.add_argument("--review-schema", required=True)
    e14_expansion_handoff.add_argument("--dossier-schema", required=True)
    e14_expansion_handoff.add_argument("--expansion-dossier-dir", required=True)
    e14_expansion_handoff.add_argument("--bundle-dir", required=True)
    e14_expansion_handoff.add_argument("--output", required=True)
    e14_expansion_ingestion = subparsers.add_parser(
        "e14-ingest-hard-negative-expansion-reviews",
        help="validate independent receipts for the four E14.4e expansion dossier hashes",
    )
    e14_expansion_ingestion.add_argument("--contract", required=True)
    e14_expansion_ingestion.add_argument("--review-queue", required=True)
    e14_expansion_ingestion.add_argument("--curation-audit", required=True)
    e14_expansion_ingestion.add_argument("--handoff-audit", required=True)
    e14_expansion_ingestion.add_argument("--handoff-contract", required=True)
    e14_expansion_ingestion.add_argument("--review-schema", required=True)
    e14_expansion_ingestion.add_argument("--receipt-dir", required=True)
    e14_expansion_ingestion.add_argument("--queue-output", required=True)
    e14_expansion_ingestion.add_argument("--output", required=True)
    e14_targeted_revision = subparsers.add_parser(
        "e14-revise-hard-negative-expansion",
        help="revise or replace only the non-accepted E14.4e hashes and build a targeted bundle",
    )
    e14_targeted_revision.add_argument("--pack", required=True)
    e14_targeted_revision.add_argument("--reviewed-queue", required=True)
    e14_targeted_revision.add_argument("--review-ingestion-audit", required=True)
    e14_targeted_revision.add_argument("--dossier-schema", required=True)
    e14_targeted_revision.add_argument("--review-schema", required=True)
    e14_targeted_revision.add_argument("--base-dossier-dir", required=True)
    e14_targeted_revision.add_argument("--revised-dossier-dir", required=True)
    e14_targeted_revision.add_argument("--bundle-dir", required=True)
    e14_targeted_revision.add_argument("--queue-output", required=True)
    e14_targeted_revision.add_argument("--output", required=True)
    e14_targeted_ingestion = subparsers.add_parser(
        "e14-ingest-hard-negative-targeted-reviews",
        help="validate independent receipts for only the two changed E14.4g2 dossier hashes",
    )
    e14_targeted_ingestion.add_argument("--contract", required=True)
    e14_targeted_ingestion.add_argument("--targeted-queue", required=True)
    e14_targeted_ingestion.add_argument("--revision-audit", required=True)
    e14_targeted_ingestion.add_argument("--revision-pack", required=True)
    e14_targeted_ingestion.add_argument("--review-schema", required=True)
    e14_targeted_ingestion.add_argument("--receipt-dir", required=True)
    e14_targeted_ingestion.add_argument("--queue-output", required=True)
    e14_targeted_ingestion.add_argument("--output", required=True)
    e12_foundation = subparsers.add_parser(
        "e12-freeze-foundation",
        help="validate E12 feature coverage by fold and freeze all foundation input hashes",
    )
    e12_foundation.add_argument("--corpus-manifest", required=True)
    e12_foundation.add_argument("--dataset", required=True)
    e12_foundation.add_argument("--plan", required=True)
    e12_foundation.add_argument("--lifecycle", required=True)
    e12_foundation.add_argument("--output", required=True)
    e12_preregister = subparsers.add_parser(
        "e12-preregister-financial-stress",
        help="freeze the E12 financial-stress candidate, gate and foundation lock",
    )
    e12_preregister.add_argument("--candidate", required=True)
    e12_preregister.add_argument("--gate", required=True)
    e12_preregister.add_argument("--foundation-lock", required=True)
    e12_preregister.add_argument("--output", required=True)
    e12_financial = subparsers.add_parser(
        "e12-financial-stress-gate",
        help="run the preregistered event-aware financial-stress inner gate",
    )
    e12_financial.add_argument("--dataset", required=True)
    e12_financial.add_argument("--plan", required=True)
    e12_financial.add_argument("--stress-truth", required=True)
    e12_financial.add_argument("--candidate", required=True)
    e12_financial.add_argument("--gate", required=True)
    e12_financial.add_argument("--foundation-lock", required=True)
    e12_financial.add_argument("--foundation-freeze", required=True)
    e12_financial.add_argument("--preregistration", required=True)
    e12_financial.add_argument("--output", required=True)
    e12_recession_preregister = subparsers.add_parser(
        "e12-preregister-recession-hazard",
        help="freeze the E12 recession-hazard candidate, gate and foundation lock",
    )
    e12_recession_preregister.add_argument("--candidate", required=True)
    e12_recession_preregister.add_argument("--gate", required=True)
    e12_recession_preregister.add_argument("--foundation-lock", required=True)
    e12_recession_preregister.add_argument("--output", required=True)
    e12_recession = subparsers.add_parser(
        "e12-recession-hazard-gate",
        help="run the preregistered SAHM/yield recession inner gate",
    )
    e12_recession.add_argument("--dataset", required=True)
    e12_recession.add_argument("--plan", required=True)
    e12_recession.add_argument("--recession-truth", required=True)
    e12_recession.add_argument("--candidate", required=True)
    e12_recession.add_argument("--gate", required=True)
    e12_recession.add_argument("--foundation-lock", required=True)
    e12_recession.add_argument("--foundation-freeze", required=True)
    e12_recession.add_argument("--preregistration", required=True)
    e12_recession.add_argument("--output", required=True)
    plan = subparsers.add_parser("plan-walk-forward", help="build rolling train/test folds")
    plan.add_argument("dataset")
    plan.add_argument("--train-years", type=int, default=10)
    plan.add_argument("--test-years", type=int, default=2)
    plan.add_argument("--step-years", type=int, default=1)
    plan.add_argument("--output")
    preregistration = subparsers.add_parser(
        "e11-preregister", help="freeze the E11 candidate gate and exactly three model configs"
    )
    preregistration.add_argument("--gate", required=True)
    preregistration.add_argument("--model-config", action="append", required=True)
    preregistration.add_argument("--output", required=True)
    dimensional = subparsers.add_parser(
        "e11-dimensional-baseline-gate",
        help="run the preregistered v1.5 baseline on nested inner validation only",
    )
    dimensional.add_argument("--evaluation", required=True)
    dimensional.add_argument("--dataset", required=True)
    dimensional.add_argument("--plan", required=True)
    dimensional.add_argument("--recession-truth", required=True)
    dimensional.add_argument("--stress-truth", required=True)
    dimensional.add_argument("--candidate", required=True)
    dimensional.add_argument("--geometry", required=True)
    dimensional.add_argument("--gate", required=True)
    dimensional.add_argument("--manifest", required=True)
    dimensional.add_argument("--output", required=True)
    challenger_gate = subparsers.add_parser(
        "e11-challenger-gate",
        help="run a preregistered E11 challenger on nested inner validation only",
    )
    challenger_gate.add_argument("--evaluation", required=True)
    challenger_gate.add_argument("--dataset", required=True)
    challenger_gate.add_argument("--plan", required=True)
    challenger_gate.add_argument("--recession-truth", required=True)
    challenger_gate.add_argument("--stress-truth", required=True)
    challenger_gate.add_argument("--candidate", required=True)
    challenger_gate.add_argument("--gate", required=True)
    challenger_gate.add_argument("--manifest", required=True)
    challenger_gate.add_argument("--output", required=True)
    baseline = subparsers.add_parser("baseline-report", help="summarize baseline results over walk-forward folds")
    baseline.add_argument("--evaluation", required=True)
    baseline.add_argument("--dataset", required=True)
    baseline.add_argument("--plan", required=True)
    baseline.add_argument("--output", required=True)
    audit = subparsers.add_parser("baseline-audit", help="audit feature saturation and regime diversity")
    audit.add_argument("--evaluation", required=True)
    audit.add_argument("--dataset", required=True)
    audit.add_argument("--plan", required=True)
    audit.add_argument("--config", required=True)
    audit.add_argument("--output", required=True)
    train_gate = subparsers.add_parser("baseline-train-gate", help="run the preregistered train-only baseline gate")
    train_gate.add_argument("--evaluation", required=True)
    train_gate.add_argument("--dataset", required=True)
    train_gate.add_argument("--plan", required=True)
    train_gate.add_argument("--config", required=True)
    train_gate.add_argument("--output", required=True)
    recession = subparsers.add_parser("recession-report", help="score DeflationBust against NBER recession months")
    recession.add_argument("--evaluation", required=True)
    recession.add_argument("--dataset", required=True)
    recession.add_argument("--plan", required=True)
    recession.add_argument("--ground-truth", required=True)
    recession.add_argument("--output", required=True)
    stress = subparsers.add_parser(
        "stress-report", help="report regime alignment on curated non-recession stress months"
    )
    stress.add_argument("--evaluation", required=True)
    stress.add_argument("--dataset", required=True)
    stress.add_argument("--plan", required=True)
    stress.add_argument("--stress-truth", required=True)
    stress.add_argument("--recession-truth", required=True)
    stress.add_argument("--output", required=True)
    evidence = subparsers.add_parser(
        "evidence-report", help="evaluate probabilistic evidence and operational-promotion sufficiency"
    )
    evidence.add_argument("--evaluation", required=True)
    evidence.add_argument("--dataset", required=True)
    evidence.add_argument("--plan", required=True)
    evidence.add_argument("--ground-truth", required=True)
    evidence.add_argument("--policy", required=True)
    evidence.add_argument("--output", required=True)
    clustering = subparsers.add_parser("clustering-report", help="run deterministic train-only k-means challenger")
    clustering.add_argument("--evaluation", required=True)
    clustering.add_argument("--dataset", required=True)
    clustering.add_argument("--plan", required=True)
    clustering.add_argument("--ground-truth", required=True)
    clustering.add_argument("--config", required=True)
    clustering.add_argument("--output", required=True)
    hmm = subparsers.add_parser("hmm-report", help="run deterministic train-only Gaussian HMM challenger")
    hmm.add_argument("--evaluation", required=True)
    hmm.add_argument("--dataset", required=True)
    hmm.add_argument("--plan", required=True)
    hmm.add_argument("--ground-truth", required=True)
    hmm.add_argument("--config", required=True)
    hmm.add_argument("--output", required=True)
    dual = subparsers.add_parser(
        "dual-timescale-report", help="run the preregistered causal dual-timescale challenger"
    )
    dual.add_argument("--evaluation", required=True)
    dual.add_argument("--dataset", required=True)
    dual.add_argument("--plan", required=True)
    dual.add_argument("--recession-truth", required=True)
    dual.add_argument("--stress-truth", required=True)
    dual.add_argument("--config", required=True)
    dual.add_argument("--output", required=True)
    shadow_predict = subparsers.add_parser(
        "shadow-predict", help="freeze baseline predictions without outcome labels"
    )
    shadow_predict.add_argument("--evaluation", required=True)
    shadow_predict.add_argument("--dataset", required=True)
    shadow_predict.add_argument("--model-config", required=True)
    shadow_predict.add_argument("--as-of", action="append", required=True)
    shadow_predict.add_argument("--generated-at-utc", required=True)
    shadow_predict.add_argument("--run-mode", choices=("dry-run", "shadow-live"), required=True)
    shadow_predict.add_argument("--preflight")
    shadow_predict.add_argument("--output", required=True)
    shadow_preflight = subparsers.add_parser(
        "shadow-preflight", help="freeze the data and implementation checks for a shadow cycle"
    )
    shadow_preflight.add_argument("--evaluation", required=True)
    shadow_preflight.add_argument("--dataset", required=True)
    shadow_preflight.add_argument("--model-config", required=True)
    shadow_preflight.add_argument("--as-of", action="append", required=True)
    shadow_preflight.add_argument("--generated-at-utc", required=True)
    shadow_preflight.add_argument("--source-root", required=True)
    shadow_preflight.add_argument("--output", required=True)
    shadow_cycle = subparsers.add_parser(
        "shadow-cycle", help="create or idempotently recover one operational shadow ledger"
    )
    shadow_cycle.add_argument("--evaluation", required=True)
    shadow_cycle.add_argument("--dataset", required=True)
    shadow_cycle.add_argument("--model-config", required=True)
    shadow_cycle.add_argument("--preflight", required=True)
    shadow_cycle.add_argument("--as-of", action="append", required=True)
    shadow_cycle.add_argument("--generated-at-utc", required=True)
    shadow_cycle.add_argument("--output", required=True)
    shadow_cycle.add_argument("--index", required=True)
    shadow_index = subparsers.add_parser(
        "shadow-index", help="rebuild the derived index from immutable shadow ledgers"
    )
    shadow_index.add_argument("--ledger-dir", required=True)
    shadow_index.add_argument("--output", required=True)
    shadow_operations = subparsers.add_parser(
        "shadow-operations", help="orchestrate the monthly C# preparation and shadow freeze"
    )
    shadow_operations.add_argument("--source-root", required=True)
    shadow_operations.add_argument("--operations-root", required=True)
    shadow_operations.add_argument("--model-config", required=True)
    shadow_operations.add_argument("--generated-at-utc", required=True)
    shadow_operations.add_argument("--mode", choices=("prepare-only", "full"), required=True)
    shadow_operations.add_argument("--result", required=True)
    shadow_operations.add_argument("--dotnet", default="dotnet")
    shadow_score = subparsers.add_parser(
        "shadow-score", help="score an immutable prediction ledger against later ground truth"
    )
    shadow_score.add_argument("--ledger", required=True)
    shadow_score.add_argument("--ground-truth", required=True)
    shadow_score.add_argument("--scored-at-utc", required=True)
    shadow_score.add_argument("--output", required=True)
    gate_decision = subparsers.add_parser(
        "gate-decision", help="persist the human decision for a model report"
    )
    gate_decision.add_argument("--report", required=True)
    gate_decision.add_argument(
        "--decision", choices=("approved", "rejected", "deferred"), required=True
    )
    gate_decision.add_argument("--reviewer", required=True)
    gate_decision.add_argument("--rationale", required=True)
    gate_decision.add_argument("--decided-at-utc", required=True)
    gate_decision.add_argument("--output", required=True)
    return parser
