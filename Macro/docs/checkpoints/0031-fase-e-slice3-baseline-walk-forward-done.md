# Macro Regime - Fase E - Slice 3: Baseline walk-forward - Done

Data: 2026-07-13

## Scopo

Eseguire la baseline rule-based sul dataset reale pluriennale e fissare un primo
benchmark riproducibile prima di introdurre modelli challenger.

## Confine implementativo

La baseline resta autorevole in C#:

- `HistoricalBaselineEvaluator` legge `historical-dataset` schema v1;
- ricostruisce ogni `DataSnapshot` tramite il mapper Infrastructure esistente;
- invoca il `BaselineRegimeDetector` Domain senza duplicarne le formule;
- salva primary/operational regime, confidence, composite score, probabilita',
  feature normalizzate e warning;
- collega l'output all'hash SHA-256 del dataset.

Il lab Python legge evaluation, dataset e piano walk-forward, ne verifica gli
hash e produce metriche descrittive. Non addestra o ricalibra la baseline.

## Artefatti reali

- evaluation: `data/historical-real-2008-2025/baseline/baseline-evaluation-2008-04-01-2025-12-31.json`;
- report: `data/historical-real-2008-2025/baseline/baseline-walk-forward-report.json`;
- righe predette: 213;
- SHA-256 dataset: `3cac7d9b290b149f6529fea80e326ff83f8e44abaf907eb91fb4a368099a288a`;
- SHA-256 evaluation: `dd6bc5f686e0086ce6617d102233d3644a04d5b654ffc6b727ac9d9dedc0278e`;
- SHA-256 report: `0598953f4a204df88f870deb4f178f26378c246bd1daac9c6db88c21af803ced`.

La directory `data/` resta esclusa da Git.

## Metodo walk-forward

- 6 fold rolling: train 10 anni, test 2 anni, step 1 anno;
- 144 osservazioni-fold, poiche' i test biennali si sovrappongono;
- aggregato calcolato sulle 84 date test uniche dal 2018-04-30 al 2025-03-31;
- nessun fitting o tuning su train/test: la baseline e' fissa;
- rendimenti forward presentati come descrittivi, non come strategia di trading.

La baseline usata e' `CRS Rule-Based Engine 0.1-demo`, efficace dal 2026-07-01.
L'applicazione al 2008-2025 e' pertanto retrospettiva: le finestre sono quelle del
protocollo walk-forward, ma il risultato non prova una performance live ex-ante.

## Risultati aggregati out-of-sample

- confidence media: 0,54167375;
- confidence mediana: 0,53675993;
- sotto confirmation threshold: 57,14%;
- `UncertainTransition`: 57,14%;
- feature mancanti: 0%;
- transition rate operativo mensile: 10,84%.

Primary regime:

- `Goldilocks`: 79/84 (94,05%);
- `DeflationBust`: 5/84 (5,95%).

Operational regime:

- `Goldilocks`: 31/84 (36,90%);
- `DeflationBust`: 5/84 (5,95%);
- `UncertainTransition`: 48/84 (57,14%).

Gli ultimi due fold hanno `UncertainTransition` al 100%; la confidence media e'
rispettivamente 0,5186 e 0,5239. Il dato segnala che la baseline corrente non
discrimina sufficientemente i regimi recenti oppure che soglia e normalizzazioni
non sono calibrate per il corpus. Non si modifica la soglia osservando il test:
qualsiasi revisione dovra' essere una nuova versione e seguire il Model Gate.

## Rendimenti descrittivi

Sulle 84 date test uniche, a 91 giorni:

- `SPY`: rendimento medio 3,55%, positivo nel 72,62% dei casi;
- `ACWI`: 2,76%, positivo nel 67,86%;
- `HYG`: 1,15%, positivo nel 72,62%;
- `IEF`: 0,29%, positivo nel 51,19%;
- `GLD`: 3,53%, positivo nel 66,67%;
- `BIL`: 0,59%, positivo nel 77,38%.

Questi valori descrivono il campione e non dimostrano causalita' o capacita'
predittiva. I soli 5 casi `DeflationBust` out-of-sample sono troppo pochi per
conclusioni affidabili sui rendimenti condizionati.

## Cosa non viene misurato

Non viene calcolata una regime accuracy: manca una ground truth esterna versionata
che distingua almeno recessioni NBER e cronologia crisi. Inventare etichette dal
medesimo dataset macro produrrebbe una validazione circolare.

Non sono calcolati tilt simulation, costi, turnover o promotion score. Nessun
challenger e' stato introdotto in questa slice.

## Verifiche

```text
dotnet build MacroRegime.slnx --no-restore
dotnet test MacroRegime.slnx --no-restore --no-build
python -m unittest discover -s tests -v
python -m compileall -q regime_eval tests
```

Esito:

- build: 0 warning, 0 errori;
- C#: 218 test superati, 0 falliti;
- Python: 8 test superati, 0 falliti;
- nessun client HTTP nei sorgenti Domain/Application/Web.

## Prossimo passo

Versionare una ground truth esterna NBER e una cronologia crisi minimale, con
fonti e regole di mapping mensile esplicite. Solo dopo si potranno calcolare
recall/false negative per `DeflationBust` e confrontare un primo challenger con
la baseline senza ricorrere a etichette circolari.
