# Macro-Regime Report

As-of date: 2026-07-01
Model: CRS Rule-Based Engine v0.1-local
Feature set: CRS Baseline v0.1-local

## Input Summary

Data source: Imported
Data source detail: Data snapshot imported from local JSON file.
Data source reference: C:\ProgettiAzure\Codex\Macro\samples\macro-data-2026-07-01.json
Active feature definitions: 5
Feature scores produced: 5
Warnings: 0

## Regime

Primary regime: Goldilocks
Operational regime: Goldilocks
Confidence: 0.6267
Composite score: 0.7907
Status: Confirmed

## Probabilities

| Rank | Regime | Probability |
|---:|---|---:|
| 1 | Goldilocks | 0.3482 |
| 2 | Reflation | 0.2617 |
| 3 | LateCycleOverheating | 0.1914 |
| 4 | Stagflation | 0.0801 |
| 5 | DeflationBust | 0.0756 |
| 6 | UncertainTransition | 0.043 |

## Feature Scores

| Feature | Dimension | Score | Weight |
|---|---|---:|---:|
| GROWTH_MOM | Growth | 0.975 | 1 |
| INFL_PRESS | Inflation | 0.4 | 1 |
| RISK_APPETITE | Risk | 0.9286 | 1 |
| MONETARY_COND | Monetary | 0.75 | 1 |
| CREDIT_STRESS | Credit | 0.9 | 1 |

## Explanations

- Driver: Growth momentum is a driver (0.475)
- Driver: Risk appetite is a driver (0.4286)
- Driver: Credit stress is a driver (0.4)
- ContrarySignal: Inflation pressure is a contrary signal (0.1)

## Allocation Proposal

Decision suggestion: PartialRebalance
Turnover: 0.08
Estimated cost: 0.0001

| Asset class | Current | Strategic | Target | Trade | Band | Tilt |
|---|---:|---:|---:|---:|---:|---:|
| Cash | 0.05 | 0.05 | 0.02 | -0.03 | 0.02-0.2 | -0.03 |
| GlobalEquity | 0.6 | 0.6 | 0.68 | 0.08 | 0.45-0.75 | 0.08 |
| GovernmentBonds | 0.25 | 0.25 | 0.2 | -0.05 | 0.1-0.4 | -0.05 |
| Gold | 0.1 | 0.1 | 0.1 | 0 | 0-0.2 | 0 |

### Allocation Rationale

- Constructive growth supports equity tilt.
- Duration can be reduced in risk-on regimes.
- Cash drag can be reduced while risk appetite is strong.

### Allocation Constraints

No allocation constraints triggered.

## Warnings

No warnings.
