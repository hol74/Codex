# Macro Regime - Fase E - Slice 8: evaluation contracts e shadow ledger

Data di chiusura: 2026-07-13.

## Esito

E8 chiude il vuoto architetturale fra backtest e shadow-live. Previsione,
scoring e decisione umana del Model Gate sono ora tre artefatti distinti,
immutabili e collegati tramite SHA-256.

Lo shadow-live reale non e' ancora iniziato: E8 ne realizza il contratto e lo
verifica con un dry-run retrospettivo dichiarato sui mesi febbraio-maggio 2020.

## Contratti implementati

### PredictionLedger

- non accetta outcome o ground truth;
- contiene run id, run mode e timestamp esplicito;
- lega dataset, evaluation e model config ai rispettivi hash;
- registra fingerprint del codice e versione del runtime Python;
- conserva forecast origin, information cutoff, distribuzione completa dei
  regimi, probabilita' recessiva, decisione binaria, warning e hash della riga;
- rifiuta la sovrascrittura del file.

### PredictionScore

- legge un ledger gia' congelato senza modificarlo;
- richiede una ground truth separata e con copertura sufficiente;
- conserva hash del ledger e della ground truth;
- produce confusion matrix, recall, precision, specificity, accuracy, balanced
  accuracy, F1, Brier score e log loss;
- contiene le label soltanto nell'artefatto di scoring.

### GateDecision

- conserva report hash, esito automatico, reviewer, rationale e timestamp;
- separa ruolo del modello e lifecycle status;
- impedisce di approvare un modello che ha fallito il gate automatico;
- rifiuta la sovrascrittura.

## Nucleo condiviso

Le metriche binarie e i delta sono stati estratti in `regime_eval/metrics.py`.
K-means, Gaussian HMM e shadow score usano ora lo stesso significato delle
metriche, evitando divergenze fra challenger.

## Dry-run reale

Baseline v1.4, date 2020-02-28 / 2020-05-29:

- ledger: 4 previsioni, nessuna label;
- score separato: TP 2, FP 1, TN 1, FN 0;
- recall 100%, precision 66,67%, F1 80%;
- Brier score 0,28417767; log loss 0,76336067;
- risultati puramente dimostrativi, non un nuovo benchmark e non un gate.

Decisione HMM persistita: `rejected`; il report sorgente e' legato allo SHA-256
`df07f9bff006f00bbd8e72b129dc869360f83e72c38392850e18611556e3200e`.

Artefatti locali:

- `data/historical-real-v11-2008-2025/governance-e8/baseline-v1-4-prediction-ledger-dry-run.json`,
  SHA-256 `976481ec55459294cf628b875792fbd5bc41d0699b685791ed482bbdd3502fbf`;
- `data/historical-real-v11-2008-2025/governance-e8/baseline-v1-4-prediction-score-dry-run.json`,
  SHA-256 `99e69c323ccee71aa4e5dad0b89586f0342f3dcb3ef3fece5f23a592a57b414b`;
- `data/historical-real-v11-2008-2025/governance-e8/gaussian-hmm-recession-v1-gate-decision.json`,
  SHA-256 `744c9fe6b84e4ed33378936fd1d228d9839bc0337efdb7f312f7c15a8dfcd26`.

## Verifiche

- build: 0 warning, 0 errori;
- test C#: 237 superati (Domain 93, Application 30, Infrastructure 87,
  Reporting 2, CLI 19, Web 6);
- test Python: 16 superati; compileall superato;
- test specifici: ledger senza label, immutabilita', hash chaining, CLI dei tre
  comandi e divieto di approvare un gate automatico fallito;
- gate architetturale: nessun client HTTP nei sorgenti Domain/Application/Web;
- `git diff --check`: superato.

## Passaggio successivo

Avviare il primo ledger `shadow-live` su una nuova osservazione 2026, usando un
timestamp reale e senza fornire ground truth al comando di previsione. Lo score
restera' assente finche' una label versionata non sara' effettivamente
disponibile. In parallelo va costruita la ground truth degli stress non
recessivi.
