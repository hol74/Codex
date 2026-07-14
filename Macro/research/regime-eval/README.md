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
