# Macro Regime - Fase E - Slice 6: Feature and Baseline Redesign - Completed

Data di avvio: 2026-07-13.

## Decisione

Il passaggio diretto al challenger HMM e' sospeso. L'infrastruttura di ricerca e'
solida, ma la baseline `0.1-demo` non discrimina in modo credibile i regimi sullo
storico reale: `Goldilocks` domina, alcune feature saturano e la ground truth NBER
contiene troppo pochi episodi OOS per dimostrare efficacia.

E6 introduce prima controlli automatici e versionati, poi procedera' al redesign.
La baseline esistente non viene modificata retroattivamente.

## Primo incremento eseguito

- aggiunto il comando Python `baseline-audit`;
- aggiunta la configurazione versionata `models/baseline-audit-v1.json`;
- misurate distribuzioni full-history e OOS uniche per ogni feature;
- introdotti gate su saturazione, diversita' primaria, concentrazione del regime
  dominante e quota `UncertainTransition`;
- mantenuta la scrittura del report anche quando il gate fallisce;
- completata la copertura degli scenari archetipici del detector con uno scenario
  esplicito `LateCycleOverheating`.

## Soglie diagnostiche v1

- bordo inferiore: score <= 0,05;
- bordo superiore: score >= 0,95;
- massimo 25% delle osservazioni OOS ai bordi per singola feature;
- almeno 3 regimi primari osservati OOS;
- massimo 80% per il regime primario dominante;
- massimo 50% di `UncertainTransition` operativo.

Queste soglie non costituiscono una prova di efficacia o un promotion score. Sono
vincoli minimi per impedire che un modello piu' complesso apprenda una superficie
di feature palesemente degenerata.

## Passi ancora aperti nella Slice E6

L'audit sul dataset reale 2008-2025 e' stato eseguito e conservato. Sulle 84 date
OOS uniche il gate fallisce con quattro violazioni:

- `CREDIT_STRESS`: boundary rate 95,24%, oltre il limite del 25%;
- regimi primari osservati: 2, sotto il minimo di 3;
- `Goldilocks`: 94,05%, oltre il limite dell'80%;
- `UncertainTransition`: 57,14%, oltre il limite del 50%.

Restano aperti:

1. ridisegnare le normalizzazioni di credito, inflazione e condizioni monetarie;
2. pubblicare feature set e baseline v1 con versioni ed effective date nuove;
3. rieseguire baseline, NBER e audit confrontando ogni regressione;
4. definire il dataset macro esteso e il nuovo holdout/shadow-live prima dell'HMM.

## Verifiche del primo incremento

- `python -m unittest discover -s tests -v`: 11 test superati;
- `python -m compileall -q regime_eval tests`: superato;
- test mirati `BaselineRegimeDetectorTests`: 8 superati;
- `dotnet test MacroRegime.slnx --no-restore`: 219 test superati
  (Domain 81, Application 30, Infrastructure 82, Reporting 2, CLI 18, Web 6);
- audit reale scritto correttamente con gate negativo e quattro violazioni
  esplicite.

## Secondo incremento - Baseline v1 candidate

E' stata introdotta una candidate separata dalla demo, selezionabile solo nel
comando storico tramite `--baseline-version v1`. La CLI usa un suffisso dedicato
per impedire la sovrascrittura degli artefatti `0.1-demo`.

Modifiche:

- `CREDIT_STRESS` usa la scala del proxy reale `BAA10Y` (1%-4%);
- `MONETARY_COND` e' non monotona: premia una curva moderatamente positiva e
  penalizza inversione e steepening estremo;
- `INFL_PRESS` usa un range 1,5%-3,0% e dichiara il limite del solo breakeven;
- growth e VIX restano invariati per isolare l'effetto del redesign;
- raw regime score e confirmation threshold 0,55 restano invariati.

Risultati OOS su 84 date:

- saturazione credito: 95,24% -> 1,19%;
- regimi primari osservati: 2 -> 3;
- Goldilocks: 94,05% -> 83,33%;
- `UncertainTransition`: 57,14% -> 78,57%;
- gate falliti: 4 -> 2.

Il gate resta negativo per Goldilocks oltre l'80% e incertezza oltre il 50%.
La soglia non viene abbassata dopo avere osservato il risultato. La model card
`research/regime-eval/model-cards/baseline-v1-candidate.md` registra la candidate
come non promossa.

Verifiche del secondo incremento:

- `dotnet build MacroRegime.slnx --no-restore`: superato;
- `dotnet test MacroRegime.slnx --no-restore`: 226 test superati
  (Domain 86, Application 30, Infrastructure 83, Reporting 2, CLI 19, Web 6);
- `python -m unittest discover -s tests -v`: 11 test superati;
- `python -m compileall -q regime_eval tests`: superato;
- evaluation, walk-forward report, NBER report e audit v1 generati sul dataset
  reale e identificati dagli hash degli input.

## Terzo incremento - Dati temporali e candidate v1.1

E' stato creato il corpus separato `data/historical-real-v11-2008-2025/`, senza
sovrascrivere quello usato dalle candidate precedenti. Contiene 213 snapshot e
9 serie macro per snapshot:

- sette serie sorgente, inclusa `CPI_YOY` da CPIAUCSL initial releases;
- `CPI_YOY_3M_CHANGE` e `YC_10Y2Y_3M_CHANGE` derivati point-in-time;
- dataset validato con SHA-256
  `1a2db1c7540a2419757b37d01717de258548f9bcf301994dfcd5c83f47f17649`.

La v1.1 combina CPI realizzato, breakeven e momentum per l'inflazione e aggiunge
la dinamica trimestrale alla curva. Raw score e threshold 0,55 restano invariati.

Risultati OOS su 84 date:

- Goldilocks 70,24%, DeflationBust 15,48%, Reflation 14,29%;
- tutte le feature sotto il limite di saturazione;
- 3 regimi primari osservati;
- `UncertainTransition` 75%;
- un solo gate fallito, contro due nella v1.0 e quattro nella demo.

La candidate non e' promossa. La model card
`research/regime-eval/model-cards/baseline-v1-1-candidate.md` vieta il tuning
post-hoc della soglia e indirizza il prossimo incremento verso raw score e
confidence train-only.

Verifiche del terzo incremento:

- `dotnet build MacroRegime.slnx --no-restore`: 0 warning, 0 errori;
- `dotnet test MacroRegime.slnx --no-restore`: 231 test superati
  (Domain 89, Application 30, Infrastructure 85, Reporting 2, CLI 19, Web 6);
- `python -m unittest discover -s tests -v`: 11 test superati;
- `python -m compileall -q regime_eval tests`: superato;
- validazione point-in-time del nuovo dataset: superata;
- gate architetturale rete: nessun client HTTP aggiunto a Domain, Application o
  Web; gli adapter esterni restano in Infrastructure.

## Quarto incremento - Raw score/confidence v1.2 e train gate

La candidate `1.2-candidate` usa archetipi macro preregistrati, score quadratici
e confidence fit/margine. Il nuovo `baseline-train-gate` ha valutato soltanto le
inner validation dei sei outer train: 0 fold eleggibili su 6, minimo 4.

La candidate e' stata fermata prima dei report OOS e non e' promossa. Il prossimo
incremento deve preregistrare un gate v2 strutturalmente separato fra controlli
aggregati di feature/copertura e robustezza confidence per-fold; non deve
ritoccare post-hoc la configurazione v1.2.

Checkpoint dettagliato:
`docs/checkpoints/0035-fase-e-slice6-v12-train-gate-rejected.md`.

## Quinto incremento - Train gate v2

Il gate v2 mantiene tutte le soglie ma valuta integrita' feature e copertura su
84 date inner-validation uniche, lasciando l'incertezza per fold. Copertura e
robustezza operativa passano; l'integrita' fallisce soltanto per
`RISK_APPETITE`, boundary rate 27,38% contro il massimo 25%.

La v1.2 resta non eleggibile e l'OOS non viene aperto. Il prossimo incremento e'
una nuova versione della normalizzazione VIX, non una modifica della soglia.

Checkpoint: `docs/checkpoints/0036-fase-e-slice6-train-gate-v2-done.md`.

## Sesto incremento - Candidate v1.3 VIX

La normalizzazione VIX logistica porta la saturazione `RISK_APPETITE` dal 27,38%
all'1,19% e fa passare integrita' e copertura del gate v2. La robustezza operativa
regredisce pero' a 2 fold validi su 6, con incertezza aggregata al 60,71%.

La v1.3 e' respinta senza apertura OOS. Il prossimo incremento deve riallineare
train-only scala feature, archetipi e confidence in una nuova versione.

Checkpoint: `docs/checkpoints/0037-fase-e-slice6-v13-vix-train-gate-rejected.md`.

## Settimo incremento - Candidate v1.4 e chiusura E6

La v1.4 traduce archetipi e cutoff divergente preservando i livelli VIX
semantici, e separa confidence geometrica dallo score power. Il train gate passa
6/6 fold; l'OOS autorizzato passa l'audit con zero violazioni, 4 regimi e 2,38%
di incertezza.

La regressione NBER (precision 20%, F1 33,33%) e l'assenza di holdout fresco
impediscono una promozione operativa. E6 e' chiusa tecnicamente e la v1.4 diventa
baseline congelata per i challenger successivi.

Checkpoint finale: `docs/checkpoints/0038-fase-e-slice6-v14-gates-passed-done.md`.
