from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .baseline import write_baseline_report
from .baseline_audit import write_baseline_audit
from .challenger import write_clustering_challenger_report
from .dataset import DatasetValidationError, load_dataset, write_manifest
from .ground_truth import write_recession_report
from .hmm_challenger import write_hmm_challenger_report
from .shadow import (
    write_baseline_prediction_ledger,
    write_gate_decision,
    write_shadow_score,
)
from .shadow_ops import ensure_shadow_ledger, write_shadow_index, write_shadow_preflight
from .stress import write_stress_report
from .train_gate import write_baseline_train_gate
from .walk_forward import WalkForwardConfig, build_walk_forward_plan


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
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
    plan = subparsers.add_parser("plan-walk-forward", help="build rolling train/test folds")
    plan.add_argument("dataset")
    plan.add_argument("--train-years", type=int, default=10)
    plan.add_argument("--test-years", type=int, default=2)
    plan.add_argument("--step-years", type=int, default=1)
    plan.add_argument("--output")
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
