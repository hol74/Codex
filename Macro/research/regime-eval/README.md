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

## E13 - Constrained Candidate Generation

E13 cambia il modo di proporre modelli: una grammatica finita viene congelata
prima di calcolare risultati. Il generatore espande deterministicamente le
combinazioni ammesse per i due task separati e produce un manifest immutabile:

```text
python -m regime_eval e13-generate-candidates --protocol models/e13-candidate-generation-protocol-v1.json --output models/e13-generated-candidates-v1.json
```

Il manifest contiene 16 candidati `research-generated`, 8 per task, e nessuna
metrica. La valutazione successiva e' vincolata a leave-one-episode-out nelle
sole finestre inner, con shortlist Pareto massima di due candidati per task.
L'outer OOS non puo' generare, ordinare, selezionare o tarare candidati.

E13.2 congela separatamente le regole LOEO e valuta il manifest senza
modificarlo:

```text
python -m regime_eval e13-loeo-evaluate --dataset ../../data/historical-real-v12-2008-2025/dataset/historical-dataset-2008-04-01-2025-12-31.json --plan ../../data/historical-real-v12-2008-2025/dataset/walk-forward-plan.json --stress-truth ground-truth/us-non-recession-stress-v2.json --recession-truth ground-truth/nber-us-recessions-v1.json --protocol models/e13-candidate-generation-protocol-v1.json --manifest models/e13-generated-candidates-v1.json --foundation-lock models/e12-data-foundation-lock-v1.json --evaluation-contract models/e13-loeo-evaluation-contract-v1.json --output ../../data/historical-real-v12-2008-2025/challengers/e13-loeo-evaluation-v1.json
```

Il report non produce una shortlist. Il task finanziario dispone dei tre
episodi minimi ed espone il trade-off copertura/falsi allarmi; il task
recessivo resta `INSUFFICIENT_EPISODES` con una sola recessione inner.

E13.3 congela la shortlist Pareto finanziaria con:

```text
python -m regime_eval e13-freeze-shortlist --loeo-report ../../data/historical-real-v12-2008-2025/challengers/e13-loeo-evaluation-v1.json --evaluation-contract models/e13-loeo-evaluation-contract-v1.json --manifest models/e13-generated-candidates-v1.json --shortlist-contract models/e13-shortlist-contract-v1.json --output models/e13-financial-shortlist-v1.json
```

L'output contiene un profilo orientato alla copertura e uno alla precisione,
le esclusioni motivate e una shortlist recessiva esplicitamente vuota. Lo
stato massimo e' `research-shortlisted`: i gate assoluti non sono ancora stati
eseguiti.

E13.4 applica requisiti assoluti, senza classifica relativa:

```text
python -m regime_eval e13-financial-absolute-gate --shortlist models/e13-financial-shortlist-v1.json --loeo-report ../../data/historical-real-v12-2008-2025/challengers/e13-loeo-evaluation-v1.json --gate models/e13-financial-absolute-gate-v1.json --output models/e13-financial-gate-decisions-v1.json
```

Il comando restituisce exit code non zero quando nessun candidato passa. Nel
primo run entrambi sono `REJECTED_FOR_SHADOW`: il profilo coverage ha troppi
falsi allarmi, quello precision perde troppi episodi. Il report resta valido e
write-once; l'exit non zero rappresenta la decisione negativa del gate.

## E14 - Information Audit

Prima di generare altri modelli, E14 misura separabilita' delle feature,
eterogeneita' degli episodi e semantica dei controlli:

```text
python -m regime_eval e14-information-audit --dataset ../../data/historical-real-v12-2008-2025/dataset/historical-dataset-2008-04-01-2025-12-31.json --plan ../../data/historical-real-v12-2008-2025/dataset/walk-forward-plan.json --stress-truth ground-truth/us-non-recession-stress-v2.json --recession-truth ground-truth/nber-us-recessions-v1.json --foundation-lock models/e12-data-foundation-lock-v1.json --e13-decisions models/e13-financial-gate-decisions-v1.json --contract models/e14-information-audit-contract-v1.json --output ../../data/historical-real-v12-2008-2025/challengers/e14-information-audit-v1.json
```

Il comando e' esclusivamente diagnostico: usa date inner, non tratta gli
unlabeled come negativi e non genera candidati, ranking o promozioni.

E14.2 congela la tassonomia tri-state v3 e verifica la copertura informativa
prima di autorizzare nuovi candidati:

```text
python -m regime_eval e14-label-audit --dataset ../../data/historical-real-v12-2008-2025/dataset/historical-dataset-2008-04-01-2025-12-31.json --plan ../../data/historical-real-v12-2008-2025/dataset/walk-forward-plan.json --taxonomy ground-truth/us-financial-stress-v3.json --information-audit ../../data/historical-real-v12-2008-2025/challengers/e14-information-audit-v1.json --contract models/e14-label-audit-contract-v1.json --output ../../data/historical-real-v12-2008-2025/challengers/e14-label-audit-v1.json
```

Il comando restituisce exit code non zero quando la copertura non autorizza la
generazione. Il report resta valido, deterministico e write-once: l'exit code
negativo e' la decisione del gate, non un errore di esecuzione.

E14.3 verifica le fonti storiche e le ipotesi pre-2008 senza scaricare dati o
creare label:

```text
python -m regime_eval e14-historical-feasibility --catalog models/e14-historical-source-catalog-v1.json --taxonomy ground-truth/us-financial-stress-v3.json --label-audit ../../data/historical-real-v12-2008-2025/challengers/e14-label-audit-v1.json --contract models/e14-historical-feasibility-contract-v1.json --output ../../data/historical-real-v12-2008-2025/challengers/e14-historical-feasibility-v1.json
```

Il primo gate restituisce exit code 3 e
`GO_FOR_EPISODE_DOSSIERS_ONLY`: le fonti positive sono plausibili, ma gli hard
negative non sono ancora dimostrati. Gli indici compositi con storia
ricostruita restano diagnostici e la popolazione completa rimane vietata.

E14.4a congela lo schema dei dossier e il contratto dei detector indipendenti:

```text
python -m regime_eval e14-mechanism-contract-audit --detector-contract models/e14-mechanism-detector-contract-v1.json --dossier-schema models/e14-episode-dossier-schema-v1.json --source-catalog models/e14-historical-source-catalog-v1.json --feasibility-report ../../data/historical-real-v12-2008-2025/challengers/e14-historical-feasibility-v1.json --taxonomy ground-truth/us-financial-stress-v3.json --output ../../data/historical-real-v12-2008-2025/challengers/e14-mechanism-contract-audit-v1.json
```

Il comando passa con `READY_FOR_DOSSIER_CURATION`. Non legge dataset o dossier,
non sceglie soglie e non autorizza ground truth, corpus o candidati.

E14.4b1 cura i dossier positivi pre-2008 a partire da un pack congelato di
asserzioni su fonti primarie:

```text
python -m regime_eval e14-curate-positive-dossiers --pack models/e14-positive-dossier-pack-v1.json --dossier-schema models/e14-episode-dossier-schema-v1.json --detector-contract models/e14-mechanism-detector-contract-v1.json --source-catalog models/e14-historical-source-catalog-v1.json --contract-audit ../../data/historical-real-v12-2008-2025/challengers/e14-mechanism-contract-audit-v1.json --dossier-dir ../../data/historical-real-v12-2008-2025/challengers/e14-dossiers-v1 --output ../../data/historical-real-v12-2008-2025/challengers/e14-positive-dossier-curation-v1.json
```

Il comando produce 8 dossier write-once nello stato `reviewed`. Restituisce
exit code 3 perche' un solo reviewer non puo' accettare i dossier e non esiste
ancora alcun hard negative conforme. Il report e' quindi valido, ma non
autorizza modifiche alla ground truth, popolazione del corpus o candidati.

E14.4b2 aggiunge hard negative affermativi per tutti i meccanismi e prepara la
coda per il reviewer indipendente:

```text
python -m regime_eval e14-adjudication-queue --hard-negative-pack models/e14-hard-negative-dossier-pack-v1.json --dossier-schema models/e14-episode-dossier-schema-v1.json --review-schema models/e14-independent-review-schema-v1.json --detector-contract models/e14-mechanism-detector-contract-v1.json --positive-pack models/e14-positive-dossier-pack-v1.json --positive-curation-audit ../../data/historical-real-v12-2008-2025/challengers/e14-positive-dossier-curation-v1.json --positive-dossier-dir ../../data/historical-real-v12-2008-2025/challengers/e14-dossiers-v1 --hard-negative-dossier-dir ../../data/historical-real-v12-2008-2025/challengers/e14-hard-negative-dossiers-v2 --review-receipt-dir ../../data/historical-real-v12-2008-2025/challengers/e14-independent-reviews-v1 --queue-output ../../data/historical-real-v12-2008-2025/challengers/e14-independent-review-queue-v2.json --output ../../data/historical-real-v12-2008-2025/challengers/e14-adjudication-readiness-v2.json
```

In assenza di ricevute il comando restituisce un exit non zero intenzionale e
lo stato `INDEPENDENT_REVIEW_REQUIRED`. La coda contiene 8 dossier positivi e
4 hard negative. Una ricevuta valida deve legare l'hash del dossier, dichiarare
l'indipendenza del reviewer e non puo' essere firmata dall'autore del pack.
La run `v2` e' quella autorevole: rende chiuse anche le proprieta' della
ricevuta e vieta `accept` quando claim o confini non sono confermati. La prima
run locale `v1` resta superseded e non viene modificata per rispettare
l'immutabilita' degli artefatti.

E14.4b3a costruisce il pacchetto da consegnare al reviewer esterno:

```text
python -m regime_eval e14-build-review-handoff --contract models/e14-review-handoff-contract-v1.json --review-queue ../../data/historical-real-v12-2008-2025/challengers/e14-independent-review-queue-v2.json --adjudication-audit ../../data/historical-real-v12-2008-2025/challengers/e14-adjudication-readiness-v2.json --review-schema models/e14-independent-review-schema-v1.json --dossier-schema models/e14-episode-dossier-schema-v1.json --positive-dossier-dir ../../data/historical-real-v12-2008-2025/challengers/e14-dossiers-v1 --hard-negative-dossier-dir ../../data/historical-real-v12-2008-2025/challengers/e14-hard-negative-dossiers-v2 --bundle-dir ../../data/historical-real-v12-2008-2025/challengers/e14-external-review-bundle-v1 --output ../../data/historical-real-v12-2008-2025/challengers/e14-review-handoff-audit-v1.json
```

Il bundle contiene `README.md`, copie immutabili dei dossier, worksheet e
template. Il reviewer deve copiare ogni template nella directory
`e14-independent-reviews-v1`, completarlo e non modificare il bundle. I
template hanno placeholder e valori `null`: non sono ricevute valide e non
devono essere collocati direttamente nella directory di ingestione.

E14.4b3b valida le ricevute del reviewer con lo schema v2:

```text
python -m regime_eval e14-ingest-independent-reviews --contract models/e14-review-ingestion-contract-v1.json --review-queue ../../data/historical-real-v12-2008-2025/challengers/e14-independent-review-queue-v2.json --adjudication-audit ../../data/historical-real-v12-2008-2025/challengers/e14-adjudication-readiness-v2.json --handoff-audit ../../data/historical-real-v12-2008-2025/challengers/e14-review-handoff-audit-v1.json --review-schema models/e14-independent-review-schema-v2.json --receipt-dir ../../data/historical-real-v12-2008-2025/challengers/e14-independent-reviews-v1 --queue-output ../../data/historical-real-v12-2008-2025/challengers/e14-independent-review-queue-v3.json --output ../../data/historical-real-v12-2008-2025/challengers/e14-review-ingestion-audit-v1.json
```

Lo schema v2 permette `sourceLocatorsOpened=false` solo nei non-accept; una
decisione `accept` richiede fonti aperte, claim confermato e confini confermati.
Il primo ciclo reale produce 8 `accept` e 4 `needs-revision`, quindi l'exit non
zero e `DOSSIER_REVISIONS_REQUIRED` sono un esito metodologico, non un errore.

E14.4b4 revisiona soltanto i quattro hash non accettati e genera un bundle di
riesame che esclude deliberatamente gli otto dossier gia' accettati:

```text
python -m regime_eval e14-targeted-dossier-revision --contract models/e14-targeted-dossier-revision-contract-v1.json --reviewed-queue ../../data/historical-real-v12-2008-2025/challengers/e14-independent-review-queue-v3.json --review-ingestion-audit ../../data/historical-real-v12-2008-2025/challengers/e14-review-ingestion-audit-v1.json --dossier-schema models/e14-episode-dossier-schema-v1.json --positive-dossier-dir ../../data/historical-real-v12-2008-2025/challengers/e14-dossiers-v1 --hard-negative-dossier-dir ../../data/historical-real-v12-2008-2025/challengers/e14-hard-negative-dossiers-v2 --revised-dossier-dir ../../data/historical-real-v12-2008-2025/challengers/e14-revised-dossiers-v1 --bundle-dir ../../data/historical-real-v12-2008-2025/challengers/e14-targeted-review-bundle-v1 --queue-output ../../data/historical-real-v12-2008-2025/challengers/e14-independent-review-queue-v4.json --output ../../data/historical-real-v12-2008-2025/challengers/e14-targeted-dossier-revision-audit-v1.json
```

Le quattro nuove ricevute vengono fuse con gli otto accept preservati senza
riaprire le review precedenti:

```text
python -m regime_eval e14-ingest-targeted-reviews --contract models/e14-targeted-review-ingestion-contract-v1.json --targeted-queue ../../data/historical-real-v12-2008-2025/challengers/e14-independent-review-queue-v4.json --revision-audit ../../data/historical-real-v12-2008-2025/challengers/e14-targeted-dossier-revision-audit-v1.json --review-schema models/e14-independent-review-schema-v2.json --receipt-dir ../../data/historical-real-v12-2008-2025/challengers/e14-targeted-independent-reviews-v1 --queue-output ../../data/historical-real-v12-2008-2025/challengers/e14-independent-review-queue-v5.json --output ../../data/historical-real-v12-2008-2025/challengers/e14-targeted-review-ingestion-audit-v1.json
```

L'esito reale e' 4/4 accept mirati e 12/12 complessivi. Lo stato
`READY_FOR_LABEL_FOUNDATION_GATE` autorizza soltanto E14.4c: non muta la ground
truth e non autorizza ancora la generazione di candidati.

E14.4c espande i dossier accettati alla granularita' mese-meccanismo e crea
una proposta di fondazione separata dalla ground truth:

```text
python -m regime_eval e14-label-foundation-gate --contract models/e14-label-foundation-gate-contract-v1.json --reviewed-queue ../../data/historical-real-v12-2008-2025/challengers/e14-independent-review-queue-v5.json --targeted-ingestion-audit ../../data/historical-real-v12-2008-2025/challengers/e14-targeted-review-ingestion-audit-v1.json --taxonomy ground-truth/us-financial-stress-v3.json --dossier-schema models/e14-episode-dossier-schema-v1.json --proposal-schema models/e14-label-foundation-proposal-schema-v1.json --label-audit-contract models/e14-label-audit-contract-v1.json --mechanism-contract models/e14-mechanism-detector-contract-v1.json --positive-dossier-dir ../../data/historical-real-v12-2008-2025/challengers/e14-dossiers-v1 --hard-negative-dossier-dir ../../data/historical-real-v12-2008-2025/challengers/e14-hard-negative-dossiers-v2 --revised-dossier-dir ../../data/historical-real-v12-2008-2025/challengers/e14-revised-dossiers-v1 --proposal-output ../../data/historical-real-v12-2008-2025/challengers/e14-label-foundation-proposal-v1.json --output ../../data/historical-real-v12-2008-2025/challengers/e14-label-foundation-gate-audit-v1.json
```

La chiave di conflitto e' `(mese, meccanismo)`: stati diversi nello stesso
mese ma su meccanismi differenti vengono mantenuti, mentre stati opposti sulla
stessa chiave bloccano il merge. Gli unlabeled non diventano mai negativi e i
dossier di uno stesso evento non aumentano artificialmente il conteggio degli
episodi indipendenti.

La run reale produce 42 label mese-meccanismo, zero conflitti e copertura
positiva sufficiente. Gli hard negative restano pero' due eventi indipendenti,
uno per meccanismo, sotto le soglie 6 totali e 2 per meccanismo. Lo stato
`FOUNDATION_MERGE_READY_MORE_EVIDENCE_REQUIRED` autorizza E14.4d a versionare
la tassonomia v4, ma mantiene chiusa la generazione di candidati.

E14.4d materializza la proposta in una nuova tassonomia mechanism-aware senza
modificare la v3:

```text
python -m regime_eval e14-materialize-taxonomy-v4 --contract models/e14-taxonomy-v4-materialization-contract-v1.json --taxonomy-v3 ground-truth/us-financial-stress-v3.json --foundation-proposal ../../data/historical-real-v12-2008-2025/challengers/e14-label-foundation-proposal-v1.json --foundation-gate-audit ../../data/historical-real-v12-2008-2025/challengers/e14-label-foundation-gate-audit-v1.json --proposal-schema models/e14-label-foundation-proposal-schema-v1.json --taxonomy-schema models/e14-financial-stress-taxonomy-v4-schema.json --label-audit-contract models/e14-label-audit-contract-v1.json --mechanism-contract models/e14-mechanism-detector-contract-v1.json --taxonomy-output ground-truth/us-financial-stress-v4.json --output ../../data/historical-real-v12-2008-2025/challengers/e14-taxonomy-v4-materialization-audit-v1.json
```

Le nuove voci sono monomeccanismo e mantengono il proprio intervallo. Il campo
`independentEventId` e' la chiave di conteggio: piu' dossier dello stesso
evento non diventano osservazioni indipendenti. La v4 estende la cronologia a
maggio 1984 senza restringere il precedente limite dicembre 2025.

La run reale termina
`TAXONOMY_V4_VERSIONED_MORE_HARD_NEGATIVES_REQUIRED`: la copertura positiva e'
sufficiente, ma i quattro dossier hard-negative rappresentano solo due eventi
indipendenti. E14.4e deve quindi ampliare e sottoporre a review gli hard
negative prima di riaprire il coverage gate o generare candidati.

E14.4e cura quattro nuovi hard negative indipendenti e li aggiunge a una nuova
review queue senza mutare la tassonomia:

```text
python -m regime_eval e14-curate-hard-negative-expansion --contract models/e14-hard-negative-expansion-contract-v1.json --pack models/e14-hard-negative-expansion-pack-v1.json --taxonomy ground-truth/us-financial-stress-v4.json --materialization-audit ../../data/historical-real-v12-2008-2025/challengers/e14-taxonomy-v4-materialization-audit-v1.json --reviewed-queue ../../data/historical-real-v12-2008-2025/challengers/e14-independent-review-queue-v5.json --dossier-schema models/e14-episode-dossier-schema-v1.json --review-schema models/e14-independent-review-schema-v2.json --label-audit-contract models/e14-label-audit-contract-v1.json --mechanism-contract models/e14-mechanism-detector-contract-v1.json --dossier-output-dir ../../data/historical-real-v12-2008-2025/challengers/e14-hard-negative-expansion-dossiers-v1 --queue-output ../../data/historical-real-v12-2008-2025/challengers/e14-independent-review-queue-v6.json --output ../../data/historical-real-v12-2008-2025/challengers/e14-hard-negative-expansion-curation-audit-v1.json
```

La run reale produce quattro dossier write-once, uno per meccanismo, e zero
conflitti sulla chiave `(mese, meccanismo)`. I 12 manifest gia' accettati
restano byte-identici nella queue v6; i quattro nuovi manifest sono in attesa
di ricevuta. La copertura hard-negative potenziale raggiunge 6 eventi
indipendenti e 2 per meccanismo, ma non e' copertura accettata. Lo stato
`INDEPENDENT_REVIEW_REQUIRED` mantiene chiusi tassonomia v4, generazione dei
candidati, outer OOS e promozione. E14.4f crea l'handoff immutabile; E14.4g
validera' review indipendenti sui quattro nuovi hash.

E14.4f prepara l'handoff esterno senza svolgere o simulare la review:

```text
python -m regime_eval e14-build-hard-negative-expansion-handoff --contract models/e14-hard-negative-expansion-handoff-contract-v1.json --review-queue ../../data/historical-real-v12-2008-2025/challengers/e14-independent-review-queue-v6.json --curation-audit ../../data/historical-real-v12-2008-2025/challengers/e14-hard-negative-expansion-curation-audit-v1.json --expansion-contract models/e14-hard-negative-expansion-contract-v1.json --review-schema models/e14-independent-review-schema-v2.json --dossier-schema models/e14-episode-dossier-schema-v1.json --expansion-dossier-dir ../../data/historical-real-v12-2008-2025/challengers/e14-hard-negative-expansion-dossiers-v1 --bundle-dir ../../data/historical-real-v12-2008-2025/challengers/e14-hard-negative-expansion-review-bundle-v1 --output ../../data/historical-real-v12-2008-2025/challengers/e14-hard-negative-expansion-handoff-audit-v1.json
```

Il bundle esclude i 12 dossier gia' accettati e contiene quattro copie
byte-identiche, quattro worksheet e quattro template schema v2. I template
devono essere copiati fuori dal bundle, completati da un reviewer indipendente
e salvati nella directory indicata dal README. Lo stato reale
`EXPANSION_AWAITING_EXTERNAL_REVIEW` non accetta la copertura potenziale e non
autorizza tassonomia o candidati. E14.4g ingerira' esclusivamente ricevute
legate ai quattro hash congelati dall'audit E14.4f.

E14.4g valida le ricevute indipendenti e non crea una queue parziale quando ne
manca anche una:

```text
python -m regime_eval e14-ingest-hard-negative-expansion-reviews --contract models/e14-hard-negative-expansion-review-ingestion-contract-v1.json --review-queue ../../data/historical-real-v12-2008-2025/challengers/e14-independent-review-queue-v6.json --curation-audit ../../data/historical-real-v12-2008-2025/challengers/e14-hard-negative-expansion-curation-audit-v1.json --handoff-audit ../../data/historical-real-v12-2008-2025/challengers/e14-hard-negative-expansion-handoff-audit-v1.json --handoff-contract models/e14-hard-negative-expansion-handoff-contract-v1.json --review-schema models/e14-independent-review-schema-v2.json --receipt-dir ../../data/historical-real-v12-2008-2025/challengers/e14-hard-negative-expansion-independent-reviews-v1 --queue-output ../../data/historical-real-v12-2008-2025/challengers/e14-independent-review-queue-v7.json --output ../../data/historical-real-v12-2008-2025/challengers/e14-hard-negative-expansion-review-ingestion-readiness-v1.json
```

Se le ricevute sono meno di quattro, il comando restituisce un esito non zero,
scrive soltanto l'audit `EXPANSION_REVIEW_INCOMPLETE` e lascia inesistente la
queue v7. Con quattro ricevute valide scrive una queue completa: tutti gli
`accept` autorizzano soltanto un coverage gate E14.4h separato; qualunque
`reject` o `needs-revision` richiede la revisione dei soli hash non accettati.
Il run reale corrente trova 0/4 ricevute. Nessuna review viene prodotta o
attribuita al processo di ingestione.

Dopo la consegna indipendente, il retry reale ha validato quattro ricevute e
ha scritto `e14-independent-review-queue-v7.json`. L'esito e' 2 `accept`, 2
`needs-revision`, zero `reject`: 1987 banking-credit e 2018Q4 funding sono
accettati; 2023 broad-market richiede un locator IMF direttamente accessibile;
repo 2019 cross-border richiede evidenza sul meccanismo di crescita reale, non
soltanto sugli spillover nei mercati repo. Lo stato
`EXPANSION_DOSSIER_REVISIONS_REQUIRED` mantiene chiuso E14.4h. Il prossimo
incremento deve preservare i 14 accept e revisionare/riesaminare soltanto i due
hash non accettati.

E14.4g2 implementa quella revisione senza riaprire gli accept. Il comando
`e14-revise-hard-negative-expansion` accetta sia il pack v1 (due hash) sia il
retry v2 (un solo hash); `e14-ingest-hard-negative-targeted-reviews` scrive la
queue successiva soltanto quando tutte le ricevute attese sono presenti.

Il regional-bank 2023 e' stato accettato usando il capitolo PDF IMF vivo. Il
repo 2019 e' stato ritirato invece di forzare il meccanismo ed e' stato
sostituito dal Flash Crash 2010 cross-border. Il primo locator CPB diretto era
404 ed e' stato respinto; il retry lega la pagina CPB live e il download XLS
ufficiale, nel quale il reviewer ha verificato 154,0 ad aprile e 157,4 a maggio
(circa +2,2%) e crescita Q2 circa +3,4%. La seconda receipt e' `accept`.

La queue v11 contiene 16/16 dossier accettati. L'audit
`e14-hard-negative-targeted-review-ingestion-audit-v2.json` raggiunge 6 eventi
hard-negative indipendenti e 2 per meccanismo e autorizza esclusivamente il
coverage gate E14.4h. Tassonomia, candidati e outer OOS restano chiusi.

E14.4h riconta la copertura accettata senza materializzare label:

```text
python -m regime_eval e14-hard-negative-coverage-gate --contract models/e14-hard-negative-coverage-gate-contract-v1.json --reviewed-queue ../../data/historical-real-v12-2008-2025/challengers/e14-independent-review-queue-v11.json --targeted-ingestion-audit ../../data/historical-real-v12-2008-2025/challengers/e14-hard-negative-targeted-review-ingestion-audit-v2.json --taxonomy ground-truth/us-financial-stress-v4.json --dossier-schema models/e14-episode-dossier-schema-v1.json --label-audit-contract models/e14-label-audit-contract-v1.json --mechanism-contract models/e14-mechanism-detector-contract-v1.json --expansion-contract models/e14-hard-negative-expansion-contract-v1.json --dossier-dir ../../data/historical-real-v12-2008-2025/challengers/e14-dossiers-v1 --dossier-dir ../../data/historical-real-v12-2008-2025/challengers/e14-hard-negative-dossiers-v2 --dossier-dir ../../data/historical-real-v12-2008-2025/challengers/e14-revised-dossiers-v1 --dossier-dir ../../data/historical-real-v12-2008-2025/challengers/e14-hard-negative-expansion-dossiers-v1 --dossier-dir ../../data/historical-real-v12-2008-2025/challengers/e14-hard-negative-expansion-revised-dossiers-v1 --dossier-dir ../../data/historical-real-v12-2008-2025/challengers/e14-hard-negative-expansion-revised-dossiers-v2 --output ../../data/historical-real-v12-2008-2025/challengers/e14-hard-negative-coverage-gate-audit-v1.json
```

Ogni manifest deve risolversi contro esattamente un file con hash e dimensione
corretti. I 12 dossier gia' presenti in v4 devono mantenere lo stesso hash; i
quattro restanti devono essere hard negative, coprire quattro eventi distinti
e uno per meccanismo. Il run reale raggiunge 6 eventi hard-negative e 2 per
meccanismo senza conflitti. `ACCEPTED_HARD_NEGATIVE_COVERAGE_READY` autorizza
E14.4i a creare una nuova tassonomia immutabile, ma non autorizza ancora
candidate generation, outer OOS o promozione.

E14.4i materializza l'espansione accettata in una nuova tassonomia write-once:

```text
python -m regime_eval e14-materialize-taxonomy-v5 --contract models/e14-taxonomy-v5-materialization-contract-v1.json --taxonomy-v4 ground-truth/us-financial-stress-v4.json --coverage-gate-audit ../../data/historical-real-v12-2008-2025/challengers/e14-hard-negative-coverage-gate-audit-v1.json --reviewed-queue ../../data/historical-real-v12-2008-2025/challengers/e14-independent-review-queue-v11.json --taxonomy-v4-schema models/e14-financial-stress-taxonomy-v4-schema.json --taxonomy-v5-schema models/e14-financial-stress-taxonomy-v5-schema.json --label-audit-contract models/e14-label-audit-contract-v1.json --mechanism-contract models/e14-mechanism-detector-contract-v1.json --taxonomy-output ground-truth/us-financial-stress-v5.json --output ../../data/historical-real-v12-2008-2025/challengers/e14-taxonomy-v5-materialization-audit-v1.json
```

Il comando non sovrascrive output esistenti, verifica gli hash di tutti gli
input e conserva strutturalmente episodi ed evidenze della v4. La run reale
produce 16 evidenze, 11 eventi positivi e 6 hard negative indipendenti, con 2
hard negative per meccanismo e zero conflitti. Lo stato
`TAXONOMY_V5_VERSIONED_CANDIDATE_READINESS_REQUIRED` consente soltanto il gate
E14.4j; non genera candidati e non legge outer OOS.

E14.4j verifica separatamente la readiness della generazione:

```text
python -m regime_eval e14-candidate-readiness-gate --contract models/e14-candidate-readiness-gate-contract-v1.json --taxonomy ground-truth/us-financial-stress-v5.json --materialization-audit ../../data/historical-real-v12-2008-2025/challengers/e14-taxonomy-v5-materialization-audit-v1.json --mechanism-contract models/e14-mechanism-detector-contract-v1.json --source-catalog models/e14-historical-source-catalog-v1.json --legacy-candidate-protocol models/e13-candidate-generation-protocol-v1.json --legacy-foundation-lock models/e12-data-foundation-lock-v1.json --output ../../data/historical-real-v12-2008-2025/challengers/e14-candidate-readiness-gate-audit-v1.json
```

La run reale termina intenzionalmente con codice non zero e stato
`CANDIDATE_READINESS_BLOCKED_FOUNDATION_AND_PROTOCOL`. Tassonomia, coverage e
detector superano i controlli, ma le sei feature sono ancora proposte non
popolate e manca una foundation point-in-time manifestata. Il protocollo E13
e' inoltre legato al lock E12 e definisce due task, non i quattro meccanismi
E14. Restano riusabili soltanto le sue policy causali, train-only, inner-only e
missingness-explicit. Il gate non legge dataset, non genera candidati e non
apre outer OOS. Il passo successivo e' E14.4k.

E14.4k materializza la feature foundation reale e il relativo lock:

```text
python -m regime_eval e14-materialize-feature-foundation --contract models/e14-mechanism-feature-foundation-contract-v1.json --taxonomy ground-truth/us-financial-stress-v5.json --readiness-audit ../../data/historical-real-v12-2008-2025/challengers/e14-candidate-readiness-gate-audit-v1.json --mechanism-contract models/e14-mechanism-detector-contract-v1.json --source-catalog models/e14-historical-source-catalog-v1.json --foundation-schema models/e14-mechanism-feature-foundation-schema-v1.json --raw-dir ../../data/historical-real-v12-2008-2025/e14-feature-foundation-v1/raw --foundation-output ../../data/historical-real-v12-2008-2025/e14-feature-foundation-v1/e14-mechanism-feature-foundation-v1.json --lock-output models/e14-mechanism-feature-foundation-lock-v1.json --output ../../data/historical-real-v12-2008-2025/challengers/e14-mechanism-feature-foundation-audit-v1.json
```

Gli input sono cinque snapshot ufficiali congelati tramite hash. Il comando
materializza cinque serie e sei binding detector, per 1.812 osservazioni. Le
serie interrotte restano assenti dopo il proprio confine: TEDRATE non viene
unito a SOFR e DTWEXB non viene unito al successore. Il dato FDIC e' reso
disponibile dopo un lag conservativo di 60 giorni; Q4 2025 e' quindi escluso
dal cutoff 2025-12-31. Lo stato
`FEATURE_FOUNDATION_MATERIALIZED_WITH_VINTAGE_LIMITATIONS` registra anche che
FRED daily e il workbook FDIC sono snapshot correnti soggetti a correzioni.
Il lock autorizza soltanto E14.4l a progettare il protocollo a quattro
detector; candidati, outer OOS e promozione restano chiusi.

E14.4l congela e verifica il protocollo research a quattro detector:

```text
python -m regime_eval e14-freeze-candidate-protocol --contract models/e14-four-detector-protocol-readiness-contract-v1.json --taxonomy ground-truth/us-financial-stress-v5.json --foundation ../../data/historical-real-v12-2008-2025/e14-feature-foundation-v1/e14-mechanism-feature-foundation-v1.json --foundation-lock models/e14-mechanism-feature-foundation-lock-v1.json --foundation-audit ../../data/historical-real-v12-2008-2025/challengers/e14-mechanism-feature-foundation-audit-v1.json --mechanism-contract models/e14-mechanism-detector-contract-v1.json --protocol models/e14-four-detector-candidate-generation-protocol-v1.json --protocol-schema models/e14-four-detector-candidate-protocol-schema-v1.json --output ../../data/historical-real-v12-2008-2025/challengers/e14-four-detector-protocol-readiness-audit-v1.json
```

Il protocollo contiene dieci profili e un budget finito di 40 candidati: 16
broad-market, 4 funding, 16 banking e 4 cross-border. Le soglie sono quantili
inner-train, i transform sono causali e train-only e i mesi unlabeled non sono
negativi impliciti. La run reale termina
`RESEARCH_CANDIDATE_GENERATION_READY_OUTER_OOS_CLOSED`: E14.5 puo' generare il
solo manifest deterministico. Fitting, evaluation, composizione, outer OOS e
promozione restano chiusi; il rischio vintage e' accettato soltanto entro il
confine research.

E14.5 genera il manifest immutabile dei candidati senza leggere dataset o
label e senza eseguire transform, fitting o evaluation:

```text
python -m regime_eval e14-generate-candidates --contract models/e14-four-detector-candidate-manifest-contract-v1.json --protocol models/e14-four-detector-candidate-generation-protocol-v1.json --readiness-audit ../../data/historical-real-v12-2008-2025/challengers/e14-four-detector-protocol-readiness-audit-v1.json --foundation ../../data/historical-real-v12-2008-2025/e14-feature-foundation-v1/e14-mechanism-feature-foundation-v1.json --foundation-lock models/e14-mechanism-feature-foundation-lock-v1.json --manifest-schema models/e14-four-detector-candidate-manifest-schema-v1.json --output models/e14-generated-four-detector-candidates-v1.json
```

Il risultato contiene 40 ID univoci legati a protocollo, meccanismo, detector,
profilo, binding delle feature e parametri di persistenza. I quantili
`[0.80, 0.90, 0.95]` restano opzioni da selezionare nel train inner e non
moltiplicano il numero di candidati. Lo stato
`GENERATED_NOT_FIT_NOT_EVALUATED_OUTER_OOS_CLOSED` mantiene esplicitamente
false transform, fitting, evaluation, ranking, composizione, outer OOS e
promozione. E14.6 dovra' preregistrare il protocollo LOEO inner prima di
autorizzare qualsiasi calcolo sui candidati.

E14.6 congela il protocollo LOEO inner e verifica la copertura strutturale
prima di qualunque fitting:

```text
python -m regime_eval e14-preregister-loeo --contract models/e14-four-detector-loeo-readiness-contract-v1.json --taxonomy ground-truth/us-financial-stress-v5.json --candidate-manifest models/e14-generated-four-detector-candidates-v1.json --foundation ../../data/historical-real-v12-2008-2025/e14-feature-foundation-v1/e14-mechanism-feature-foundation-v1.json --foundation-lock models/e14-mechanism-feature-foundation-lock-v1.json --candidate-protocol models/e14-four-detector-candidate-generation-protocol-v1.json --preregistration models/e14-four-detector-loeo-preregistration-v1.json --preregistration-schema models/e14-four-detector-loeo-preregistration-schema-v1.json --output ../../data/historical-real-v12-2008-2025/challengers/e14-four-detector-loeo-preregistration-audit-v1.json
```

Il comando termina intenzionalmente non-zero con stato
`INNER_LOEO_PREREGISTERED_STRUCTURAL_COVERAGE_BLOCKED`. Applicando 60 mesi di
storia minima, l'intersezione delle serie del profilo e i confini metodologici,
solo i 16 candidati broad-market conservano almeno tre episodi positivi e due
hard negative osservabili. Banking-credit, cross-border-growth e
funding-liquidity restano senza candidati eleggibili. Non e' autorizzato
neppure un fitting broad-only: E14.6a deve riesaminare la foundation o ritirare
in modo esplicito le grammatiche prive di evidenza sufficiente.

E14.6a preregistra il percorso di riparazione senza scaricare dati:

```text
python -m regime_eval e14-preregister-coverage-repair --contract models/e14-structural-coverage-repair-contract-v1.json --taxonomy ground-truth/us-financial-stress-v5.json --foundation ../../data/historical-real-v12-2008-2025/e14-feature-foundation-v1/e14-mechanism-feature-foundation-v1.json --preregistration models/e14-four-detector-loeo-preregistration-v1.json --loeo-audit ../../data/historical-real-v12-2008-2025/challengers/e14-four-detector-loeo-preregistration-audit-v1.json --repair-plan models/e14-structural-coverage-repair-plan-v1.json --repair-schema models/e14-structural-coverage-repair-plan-schema-v1.json --output ../../data/historical-real-v12-2008-2025/challengers/e14-structural-coverage-repair-audit-v1.json
```

Il requisito di 60 mesi resta invariato. Le fonti proposte sono l'archivio
FDIC failures/assistance, `TWEXBMTH` e `TB3SMFFM` trasformato in Fed funds meno
T-bill. La proiezione raggiunge 28 candidati potenzialmente eleggibili, ma non
e' evidenza materializzata. Lo stato
`STRUCTURAL_COVERAGE_REPAIR_PREREGISTERED_MATERIALIZATION_REQUIRED` autorizza
solo E14.6b. I subindex NFCI sono esclusi come detector primari perche'
ristimati/revisionati e restano utilizzabili soltanto come diagnostica.

E14.6b scarica e congela le tre fonti preregistrate, conserva immutata la
foundation v1 e materializza una foundation v2 separata:

```text
python -m regime_eval e14-materialize-feature-foundation-v2 --contract models/e14-mechanism-feature-foundation-contract-v2.json --taxonomy ground-truth/us-financial-stress-v5.json --foundation-v1 ../../data/historical-real-v12-2008-2025/e14-feature-foundation-v1/e14-mechanism-feature-foundation-v1.json --foundation-lock-v1 models/e14-mechanism-feature-foundation-lock-v1.json --repair-plan models/e14-structural-coverage-repair-plan-v1.json --repair-audit ../../data/historical-real-v12-2008-2025/challengers/e14-structural-coverage-repair-audit-v1.json --foundation-schema models/e14-mechanism-feature-foundation-schema-v2.json --raw-dir ../../data/historical-real-v12-2008-2025/e14-feature-foundation-v2/raw --foundation-output ../../data/historical-real-v12-2008-2025/e14-feature-foundation-v2/e14-mechanism-feature-foundation-v2.json --lock-output models/e14-mechanism-feature-foundation-lock-v2.json --output ../../data/historical-real-v12-2008-2025/challengers/e14-mechanism-feature-foundation-audit-v2.json
```

La v2 contiene le due serie broad-market v1 riportate per contenuto esatto e
tre replacement: 1.104 mesi FDIC, 563 variazioni `TWEXBMTH` e 858 osservazioni
Fed funds meno T-bill. Il registro FDIC ha 4.115 righe e inventario API
completo; 154 transazioni prive di `QBFASSET` rendono esplicitamente missing 69
mesi, mentre 556 mesi senza transazioni sono zeri osservati validi. La copertura
reale positiva/hard-negative e' 3/2 banking, 6/2 broad, 5/2 cross-border e 3/2
funding. `TWEXBMTH` non viene estesa oltre dicembre 2019; per `TB3SMFFM` sono
congelate statistiche separate prima/dopo il confine 2019, senza affermare
equivalenza distributiva.

Lo stato
`FEATURE_FOUNDATION_V2_MATERIALIZED_RESEARCH_ONLY_REVISION_LIMITATIONS_CANDIDATE_GENERATION_CLOSED`
certifica la riparazione strutturale ma mantiene `strictVintageReady=false`:
non esistono nei preregistered input snapshot point-in-time precedenti per una
comparazione completa delle revisioni. Candidate generation, fitting,
evaluation, outer OOS e promozione restano chiusi fino al gate E14.6c.

E14.6c applica missingness interna, storia non-missing e lag di disponibilita'
reali per materializzare un roster di readiness, non un candidate manifest:

```text
python -m regime_eval e14-readiness-gate-v2 --contract models/e14-four-detector-readiness-contract-v2.json --taxonomy ground-truth/us-financial-stress-v5.json --foundation ../../data/historical-real-v12-2008-2025/e14-feature-foundation-v2/e14-mechanism-feature-foundation-v2.json --foundation-lock models/e14-mechanism-feature-foundation-lock-v2.json --foundation-audit ../../data/historical-real-v12-2008-2025/challengers/e14-mechanism-feature-foundation-audit-v2.json --candidate-manifest-v1 models/e14-generated-four-detector-candidates-v1.json --repair-plan models/e14-structural-coverage-repair-plan-v1.json --readiness-policy models/e14-four-detector-readiness-policy-v2.json --readiness-policy-schema models/e14-four-detector-readiness-policy-schema-v2.json --roster-schema models/e14-four-detector-readiness-roster-schema-v2.json --roster-output models/e14-four-detector-readiness-roster-v2.json --output ../../data/historical-real-v12-2008-2025/challengers/e14-four-detector-readiness-audit-v2.json
```

Il gate richiede 60 osservazioni non-missing, deriva il lag `availableOn` da
ogni serie e vieta carry attraverso il calendar slot missing. I lag risultano
zero per VIX, BAA10Y e FDIC e un mese per `TWEXBMTH` e Fed funds meno T-bill.
Tutti i 28 ingressi sono eleggibili: 16 ID broad preservati esattamente, 24 ID
v1 ritirati e 12 nuovi ID con namespace `-v2-`. Gli ingressi nuovi hanno stato
`readiness-planned-not-generated-not-fit`.

La sensitivity funding 2019 e' congelata come diagnostica inner obbligatoria:
confronto delle soglie full/pre-2019, shift normalizzato per IQR, alert rate e
metriche per episodi pre/post. Il tratto pre-2019 non diventa un gate
alternativo, perche' contiene un solo episodio funding positivo. Lo stato
`FOUR_DETECTOR_READINESS_V2_PASSED_PROTOCOL_V2_DESIGN_AUTHORIZED_FITTING_CLOSED`
autorizza solo la progettazione del protocollo v2; manifest generation,
fitting, evaluation, ranking, outer OOS e promozione restano chiusi.
