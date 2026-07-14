# Macro Regime Research Lab

Questo laboratorio Python valuta la baseline e i futuri modelli challenger senza
introdurre dipendenze Python nel runtime C#.

La prima slice implementa il gate dati della Fase E:

- validazione dello schema `historical-dataset` prodotto dalla CLI C#;
- controlli point-in-time su publication/availability date;
- manifest riproducibile con SHA-256, copertura, simboli e orizzonti;
- piano walk-forward rolling 10 anni train / 2 anni test / avanzamento 1 anno;
- nessuna selezione di iperparametri sui periodi di test.

## Comandi

Da questa directory:

```text
python -m regime_eval validate path/to/historical-dataset.json
python -m regime_eval manifest path/to/historical-dataset.json --output dataset-manifest.json
python -m regime_eval plan-walk-forward path/to/historical-dataset.json --output walk-forward-plan.json
python -m regime_eval baseline-report --evaluation baseline-evaluation.json --dataset historical-dataset.json --plan walk-forward-plan.json --output baseline-walk-forward-report.json
python -m regime_eval baseline-audit --evaluation baseline-evaluation.json --dataset historical-dataset.json --plan walk-forward-plan.json --config models/baseline-audit-v1.json --output baseline-audit-v1-report.json
python -m regime_eval recession-report --evaluation baseline-evaluation.json --dataset historical-dataset.json --plan walk-forward-plan.json --ground-truth ground-truth/nber-us-recessions-v1.json --output baseline-nber-recession-report.json
python -m regime_eval stress-report --evaluation baseline-evaluation.json --dataset historical-dataset.json --plan walk-forward-plan.json --stress-truth ground-truth/us-non-recession-stress-v1.json --recession-truth ground-truth/nber-us-recessions-v1.json --output baseline-stress-report.json
python -m regime_eval evidence-report --evaluation baseline-evaluation.json --dataset historical-dataset.json --plan walk-forward-plan.json --ground-truth ground-truth/nber-us-recessions-v1.json --policy models/baseline-v1-4-evidence-v2-preregistered.json --output baseline-evidence-v2-report.json
python -m regime_eval dual-timescale-report --evaluation baseline-evaluation.json --dataset historical-dataset.json --plan walk-forward-plan.json --recession-truth ground-truth/nber-us-recessions-v1.json --stress-truth ground-truth/us-non-recession-stress-v2.json --config models/dual-timescale-regime-v1.json --output dual-timescale-regime-v1-report.json
python -m regime_eval clustering-report --evaluation baseline-evaluation.json --dataset historical-dataset.json --plan walk-forward-plan.json --ground-truth ground-truth/nber-us-recessions-v1.json --config models/kmeans-recession-v1.json --output kmeans-recession-v1-report.json
python -m unittest discover -s tests -v
```

Il laboratorio usa ancora solo la standard library Python. Anche il primo
challenger k-means e' implementato senza dipendenze scientifiche; eventuali
librerie aggiuntive per HMM o modelli successivi richiederanno una scelta
esplicita e riproducibile.

## Gate dei challenger

Un dataset destinato alla valutazione deve:

1. superare la validazione point-in-time;
2. coprire almeno 12 anni per produrre un fold completo;
3. avere train e test non sovrapposti;
4. essere identificato da un manifest e dal suo hash;
5. avere una copertura reale documentata, non solo sample demo.

## Corpus reale di riferimento

La Slice E2 ha prodotto localmente `data/historical-real-2008-2025/`:

- campionamento mensile all'ultimo giorno di mercato completo;
- 213 righe dal 2008-04-30 al 2025-12-31;
- 6 simboli market e forward return a 28, 56 e 91 giorni;
- manifest separati per corpus sorgente e dataset di ricerca;
- 6 fold rolling completi con configurazione 10/2/1.

La directory `data/` e' esclusa da Git. Va rigenerata con le credenziali FRED e
non deve essere confusa con un fixture versionato.

## E12 - foundation event-aware

E12.2 usa un layout separato `data/historical-real-v12-2008-2025/` e aggiunge
massimi intramese VIX/SOFR-EFFR e drawdown SPY/HYG senza cambiare il dataset
schema v1. Dopo population e build, il freeze si esegue dal laboratorio con:

```text
python -m regime_eval e12-freeze-foundation --corpus-manifest ../../data/historical-real-v12-2008-2025/corpus-manifest.json --dataset ../../data/historical-real-v12-2008-2025/dataset/historical-dataset-2008-04-01-2025-12-31.json --plan ../../data/historical-real-v12-2008-2025/dataset/walk-forward-plan.json --lifecycle models/e12-task-lifecycle-v1.json --output ../../data/historical-real-v12-2008-2025/e12-data-foundation-freeze.json
```

Il report e' write-once, verifica i conteggi dichiarati dal corpus e registra
coverage totale e train/test per fold. Il lock versionato
`models/e12-data-foundation-lock-v1.json` conserva gli hash autorevoli per le
configurazioni candidate successive.

Il primo candidato task-specifico si esegue solo dopo la preregistrazione:

```text
python -m regime_eval e12-preregister-financial-stress --candidate models/event-aware-financial-stress-v1.json --gate models/e12-financial-stress-gate-v1.json --foundation-lock models/e12-data-foundation-lock-v1.json --output models/e12-financial-stress-preregistration-v1.json
python -m regime_eval e12-financial-stress-gate --dataset ../../data/historical-real-v12-2008-2025/dataset/historical-dataset-2008-04-01-2025-12-31.json --plan ../../data/historical-real-v12-2008-2025/dataset/walk-forward-plan.json --stress-truth ground-truth/us-non-recession-stress-v2.json --candidate models/event-aware-financial-stress-v1.json --gate models/e12-financial-stress-gate-v1.json --foundation-lock models/e12-data-foundation-lock-v1.json --foundation-freeze ../../data/historical-real-v12-2008-2025/e12-data-foundation-freeze.json --preregistration models/e12-financial-stress-preregistration-v1.json --output ../../data/historical-real-v12-2008-2025/challengers/event-aware-financial-stress-v1-inner-gate.json
```

La v1 e' stata respinta dal gate inner-only; il report resta un artefatto di
sviluppo e non autorizza modifiche post-hoc o promozione.

Il candidato recessivo E12.4 segue lo stesso confine:

```text
python -m regime_eval e12-preregister-recession-hazard --candidate models/sahm-yield-hazard-v1.json --gate models/e12-recession-hazard-gate-v1.json --foundation-lock models/e12-data-foundation-lock-v1.json --output models/e12-recession-hazard-preregistration-v1.json
python -m regime_eval e12-recession-hazard-gate --dataset ../../data/historical-real-v12-2008-2025/dataset/historical-dataset-2008-04-01-2025-12-31.json --plan ../../data/historical-real-v12-2008-2025/dataset/walk-forward-plan.json --recession-truth ground-truth/nber-us-recessions-v1.json --candidate models/sahm-yield-hazard-v1.json --gate models/e12-recession-hazard-gate-v1.json --foundation-lock models/e12-data-foundation-lock-v1.json --foundation-freeze ../../data/historical-real-v12-2008-2025/e12-data-foundation-freeze.json --preregistration models/e12-recession-hazard-preregistration-v1.json --output ../../data/historical-real-v12-2008-2025/challengers/sahm-yield-hazard-v1-inner-gate.json
```

Anche questa v1 e' stata respinta. Il gate finanziario e quello recessivo
restano semanticamente e operativamente separati.

## Baseline walk-forward

La Slice E3 mantiene due responsabilita' separate:

- la CLI C# `--evaluate-historical-baseline --dataset-file` esegue il detector
  rule-based autorevole su ogni riga e salva probabilita', feature e warning;
- `baseline-report` verifica gli hash e aggrega confidenza, incertezza, stabilita'
  e rendimenti forward per fold e regime.

Le finestre di test sono out-of-sample rispetto alla struttura walk-forward, ma
la baseline `0.1-demo` e' applicata retrospettivamente ed e' efficace dal 2026:
il report non rappresenta performance live ex-ante. L'accuracy di regime non e'
calcolata finche' non sara' disponibile una ground truth esterna versionata.

## Ground truth recessiva

La Slice E4 aggiunge `ground-truth/nber-us-recessions-v1.json`, con cronologia
NBER, fonti, hash e mapping mensile esplicito: il picco e' l'ultimo mese di
espansione; l'etichetta recessiva va dal mese successivo al picco fino al trough
incluso. `recession-report` misura il segnale binario `DeflationBust` separatamente
per primary e operational regime.

La cronologia NBER e' ex-post e non va usata come input real-time. Accuracy e
specificity devono essere lette insieme a recall, precision, F1, prevalenza,
false-negative dates e detection lag; sul campione OOS i mesi recessivi sono solo
due e l'accuracy isolata e' dominata dalla classe non recessiva.

## Stress non recessivi

`ground-truth/us-non-recession-stress-v1.json` aggiunge una cronologia ex-post
multi-label per stress finanziario, growth scare, shock inflazionistico e
tightening monetario. `stress-report` richiede anche la ground truth NBER e
rifiuta episodi che intersecano mesi recessivi.

Il report misura distribuzione dei regimi, allineamento semantico e incertezza
solo sui mesi etichettati. Non calcola accuracy sulla classe negativa: la
cronologia e' selettiva e l'assenza di label non dimostra assenza di stress. La
v1 e' un artefatto di audit congelato, non un set di tuning.

## Slice E6 - Audit prima del redesign

E6 sospende il passaggio diretto all'HMM. `baseline-audit` produce un artefatto
deterministico con distribuzioni delle feature, saturazione ai bordi, diversita'
dei regimi primari, concentrazione del regime dominante, quota di transizioni
incerte e coppie top-2. Un gate fallito restituisce exit code 3 dopo avere scritto
il report: e' un risultato diagnostico atteso, non un errore di esecuzione.

La candidate v1 viene generata dal runtime C# autorevole senza sovrascrivere la
demo:

```text
dotnet run --project src/MacroRegime.Cli -- --evaluate-historical-baseline --baseline-version v1 --dataset-file historical-dataset.json --output-dir output
```

L'output usa il suffisso `-v1-candidate`. La model card
`model-cards/baseline-v1-candidate.md` conserva sia i miglioramenti sia le
regressioni; la candidate non e' promossa.

La candidate temporale v1.1 richiede il corpus esteso con `CPI_YOY`,
`CPI_YOY_3M_CHANGE` e `YC_10Y2Y_3M_CHANGE` e si esegue con
`--baseline-version v1.1`. L'output usa il suffisso `-v1-1-candidate`; risultati
e limiti sono in `model-cards/baseline-v1-1-candidate.md`.

La v1.2 introduce raw score archetipici e confidence fit/margine, selezionabile
con `--baseline-version v1.2`. Prima di qualsiasi report OOS si esegue:

```text
python -m regime_eval baseline-train-gate --evaluation baseline-v1-2.json --dataset historical-dataset.json --plan walk-forward-plan.json --config models/baseline-v1-2-train-gate-v2-preregistered.json --output baseline-v1-2-train-gate-v2.json
```

Il gate v1 reale era negativo (0 fold eleggibili su 6). Il gate v2 separa
integrita'/copertura aggregate e operativita' per fold: copertura e operativita'
passano, ma `RISK_APPETITE` resta al bordo nel 27,38% delle validation uniche
contro il 25% massimo. La candidate resta fermata prima dei report OOS.

La candidate v1.3 usa `--baseline-version v1.3` e cambia soltanto il mapping VIX
in una logistica inversa centrata a 20, scala 7. Il train gate v2 passa integrita'
e copertura, ma fallisce robustezza operativa (2/6 fold): nessun report OOS viene
aperto. Configurazioni e risultato sono nella model card v1.3.

La v1.4 (`--baseline-version v1.4`) traduce archetipi e cutoff divergente sugli
stessi livelli VIX semantici e usa confidence geometrica. Supera train gate v2 e
audit OOS; i report walk-forward, audit e NBER vengono quindi autorizzati. La
candidate e' baseline di ricerca, non modello operativo promosso: dettagli e
regressione NBER sono nella model card v1.4.

## Primo challenger

`kmeans-recession-v1` è un clustering standard-library, deterministico e
train-only. Scaling, centroidi e mapping cluster/NBER vengono rifatti in ogni
train fold. Il test verifica sia la riproducibilità byte-for-byte sia che cambiare
le sole label test non alteri le predizioni.

Il risultato è negativo ed è conservato nella model card: il challenger non
rileva alcun mese recessivo sulle date OOS uniche e non viene promosso. Non sono
stati provati valori alternativi di `clusterCount` dopo la lettura del test.

## Challenger temporale Gaussian HMM

`gaussian-hmm-recession-v1` usa tre stati, emissioni gaussiane diagonali e
Baum-Welch deterministico. Scaling, parametri e mapping stato/NBER sono stimati
solo sul train. Sul test usa posterior filtrati causalmente, senza backward
smoothing.

```text
python -m regime_eval hmm-report --evaluation baseline-v1-4.json --dataset historical-dataset.json --plan walk-forward-plan.json --ground-truth ground-truth/nber-us-recessions-v1.json --config models/gaussian-hmm-recession-v1.json --output gaussian-hmm-recession-v1-report.json
```

Il report reale converge in tutti i 6 fold ma fallisce il gate: recall 50% e F1
11,76%, contro 100% e 33,33% della baseline v1.4 operational. Il modello non e'
promosso e non viene sottoposto a tuning post-hoc sul medesimo OOS. Dettagli e
hash sono in `model-cards/gaussian-hmm-recession-v1.md`.

## E8 - Ledger per lo shadow-live

La previsione viene congelata senza ground truth:

```text
python -m regime_eval shadow-preflight --evaluation baseline-v1-4-evaluation.json --dataset historical-dataset.json --model-config models/baseline-v1-4-preregistered.json --as-of 2026-07-31 --generated-at-utc 2026-08-01T08:00:00Z --source-root ../.. --output shadow-preflight.json
python -m regime_eval shadow-cycle --evaluation baseline-v1-4-evaluation.json --dataset historical-dataset.json --model-config models/baseline-v1-4-preregistered.json --preflight shadow-preflight.json --as-of 2026-07-31 --generated-at-utc 2026-08-01T08:05:00Z --output ledger/prediction-ledger-2026-07-31.json --index ledger/shadow-index.json
```

Solo quando la label versionata e' disponibile si crea uno score separato:

```text
python -m regime_eval shadow-score --ledger prediction-ledger.json --ground-truth ground-truth/nber-us-recessions-v2.json --scored-at-utc 2027-01-01T08:00:00Z --output prediction-score.json
```

La decisione umana del Model Gate e' anch'essa un artefatto separato:

```text
python -m regime_eval gate-decision --report challenger-report.json --decision rejected --reviewer research-owner --rationale "Automatic gate failed." --decided-at-utc 2026-07-13T13:10:00Z --output gate-decision.json
```

Tutti e tre i formati sono write-once. Il ledger registra probabilita' di
recessione, distribuzione completa dei regimi, input hash, fingerprint del
codice e runtime; non contiene mai outcome.

## E9 - Shadow Operations

`shadow-live` richiede ora un `ShadowPreflight` passato e write-once. Il
preflight accetta solo mesi informativi chiusi, dataset point-in-time senza
forward return, tutte le nove serie macro richieste con lag massimo di tre mesi
e registra fingerprint deterministici delle sorgenti C# e Python.

`shadow-cycle` e' idempotente: con gli stessi input recupera il ledger
esistente senza riscriverlo; se path, date o hash sono incompatibili, termina
con errore. `shadow-index` ricostruisce una vista non autorevole dai soli ledger
`shadow-live` immutabili. Nessuno di questi comandi riceve ground truth.

### Orchestrazione mensile E9.2

Il comando end-to-end determina il mese successivo all'ultimo ledger e non
consente salti nella serie temporale:

```text
python -m regime_eval shadow-operations --source-root ../.. --operations-root ../../data/shadow-live-2026 --model-config models/baseline-v1-4-preregistered.json --generated-at-utc 2026-08-01T08:00:00Z --mode prepare-only --result ../../data/shadow-live-2026/operations-audit/shadow-operations-2026-08-01.json
```

`prepare-only` esegue population, dataset build, evaluation e preflight, ma non
crea il ledger. `full` aggiunge il freeze del ledger e la ricostruzione
dell'indice. Gli step C# sono eseguiti senza shell e senza API key negli
argomenti; FRED continua a leggere la credenziale dall'ambiente o da `.env`.

Ogni ciclo usa `cycles/yyyy-MM/` con sottodirectory `source`, `dataset`,
`evaluation`, `preflight` e `logs`. `cycle-state.json` e' uno stato operativo
atomico e non autorevole: registra tentativi, exit code e hash e permette di
saltare gli step gia' completati e invariati. Ogni invocazione produce invece
una receipt `ShadowOperationsRun` write-once. Un risultato
`no-eligible-month` non avvia alcun processo e non crea directory di ciclo.

## E10 - Evidence v2 e stress dimensionale

`evidence-report` separa il superamento tecnico dalla sufficienza dell'evidenza
operativa e aggiunge scoring probabilistico, average precision, calibrazione,
bootstrap a blocchi ed errori temporali per episodio. Sul corpus reale la v1.4
restituisce `INSUFFICIENT_EVIDENCE`: 84 date OOS ma soltanto due mesi positivi e
un episodio recessivo.

`us-non-recession-stress-v2.json` valuta quattro dimensioni prima del regime
composito e separa gli episodi v1 da due episodi protetti v2. Il primo report
conferma il blind spot finanziario sulla partizione protetta.

`dual-timescale-regime-v1` e' un filtro causale preregistrato con componente
macro lenta e finanziaria rapida. Il diagnostico storico e' negativo (recall e
F1 0%) e il modello e' respinto senza modifica dei parametri. Il comando scrive
comunque il report, ma restituisce exit code non zero perche' non supera alcun
gate di promozione.

## E11 - Controlled Candidate Lab

E11.1 congela il contratto sperimentale prima di implementare o valutare i
modelli. Sono ammesse esattamente tre configurazioni: baseline dimensionale
v1.5, changepoint con durata v1 e rare-event logit v1. La selezione usa soltanto
inner rolling validation; l'outer OOS 2008-2025 puo' diventare una diagnostica
successiva ma non puo' selezionare, ordinare o promuovere un candidato.

Il manifest write-once si genera una sola volta con:

```text
python -m regime_eval e11-preregister --gate models/e11-shadow-candidate-gate-v1.json --model-config models/baseline-v1-5-dimensional.json --model-config models/changepoint-duration-v1.json --model-config models/rare-event-logit-v1.json --output models/e11-preregistration-manifest.json
```

Il gate lega gli hash degli input, del contratto e delle tre configurazioni.
Prima di nuovi outcome il massimo lifecycle ottenibile e' `shadow-candidate`;
`operational-approved` richiede evidenza prospettica e decisione umana.

E11.2 implementa la baseline dimensionale e la valuta soltanto sulle inner
validation derivate dalle finestre walk-forward:

```text
python -m regime_eval e11-dimensional-baseline-gate --evaluation ../../data/historical-real-v11-2008-2025/baseline/baseline-evaluation-2008-04-01-2025-12-31-v1-4-candidate.json --dataset ../../data/historical-real-v11-2008-2025/dataset/historical-dataset-2008-04-01-2025-12-31.json --plan ../../data/historical-real-v11-2008-2025/dataset/walk-forward-plan.json --recession-truth ground-truth/nber-us-recessions-v1.json --stress-truth ground-truth/us-non-recession-stress-v2.json --candidate models/baseline-v1-5-dimensional.json --geometry models/baseline-v1-4-preregistered.json --gate models/e11-shadow-candidate-gate-v1.json --manifest models/e11-preregistration-manifest.json --output ../../data/historical-real-v11-2008-2025/challengers/baseline-v1-5-dimensional-inner-gate.json
```

Il runner verifica il manifest preregistrato, non riceve righe outer-test e
calcola tutte le predizioni prima di applicare le label. L'esito reale e'
`REJECTED_FOR_SHADOW`: Brier delta `+0.00081972` e protected-stress hit rate
`0/2`. Le soglie e le formule restano congelate.

E11.3 usa un runner condiviso per i due challenger preregistrati:

```text
python -m regime_eval e11-challenger-gate --evaluation ../../data/historical-real-v11-2008-2025/baseline/baseline-evaluation-2008-04-01-2025-12-31-v1-4-candidate.json --dataset ../../data/historical-real-v11-2008-2025/dataset/historical-dataset-2008-04-01-2025-12-31.json --plan ../../data/historical-real-v11-2008-2025/dataset/walk-forward-plan.json --recession-truth ground-truth/nber-us-recessions-v1.json --stress-truth ground-truth/us-non-recession-stress-v2.json --candidate models/changepoint-duration-v1.json --gate models/e11-shadow-candidate-gate-v1.json --manifest models/e11-preregistration-manifest.json --output ../../data/historical-real-v11-2008-2025/challengers/changepoint-duration-v1-inner-gate.json
python -m regime_eval e11-challenger-gate --evaluation ../../data/historical-real-v11-2008-2025/baseline/baseline-evaluation-2008-04-01-2025-12-31-v1-4-candidate.json --dataset ../../data/historical-real-v11-2008-2025/dataset/historical-dataset-2008-04-01-2025-12-31.json --plan ../../data/historical-real-v11-2008-2025/dataset/walk-forward-plan.json --recession-truth ground-truth/nber-us-recessions-v1.json --stress-truth ground-truth/us-non-recession-stress-v2.json --candidate models/rare-event-logit-v1.json --gate models/e11-shadow-candidate-gate-v1.json --manifest models/e11-preregistration-manifest.json --output ../../data/historical-real-v11-2008-2025/challengers/rare-event-logit-v1-inner-gate.json
```

Entrambi gli esiti sono `REJECTED_FOR_SHADOW`. Il changepoint produce troppi
falsi positivi e probabilita' non calibrate; il logit e' conservativo ma perde
il positivo inner e due fold sono ineligibili per assenza di positivi nel fit.
E11.4 consolida quindi zero shadow-candidate, senza aprire l'outer OOS.
