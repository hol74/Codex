from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from .baseline import write_baseline_report
from .dataset import DatasetValidationError, load_dataset, write_manifest
from .walk_forward import WalkForwardConfig, build_walk_forward_plan


def main(argv: list[str] | None = None) -> int:
    parser = _parser()
    args = parser.parse_args(argv)
    try:
        if args.command == "baseline-report":
            output = write_baseline_report(args.evaluation, args.dataset, args.plan, args.output)
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
    return parser
