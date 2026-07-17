# Macro-Regime Engine — Manuale operativo

## Come preparare, eseguire e controllare il sistema informativo

**Aggiornamento:** 17 luglio 2026  
**Nome richiesto del documento:** `istructions.md`  
**Destinatari:** proprietario del sistema, operatore, reviewer e sviluppatore  
**Avvertenza:** il sistema produce informazione e proposte vincolate; non fornisce consulenza finanziaria e non esegue ordini.

---

## Indice

1. [Come leggere questo manuale](#1-come-leggere-questo-manuale)
2. [Le modalità d'uso](#2-le-modalità-duso)
3. [Prerequisiti e preparazione iniziale](#3-prerequisiti-e-preparazione-iniziale)
4. [Regole operative obbligatorie](#4-regole-operative-obbligatorie)
5. [Pipeline consigliata per una singola analisi](#5-pipeline-consigliata-per-una-singola-analisi)
6. [Catalogo completo della CLI C#](#6-catalogo-completo-della-cli-c)
7. [Uso della dashboard Web](#7-uso-della-dashboard-web)
8. [Pipeline per dataset storico e valutazione](#8-pipeline-per-dataset-storico-e-valutazione)
9. [Pipeline mensile di Shadow Operations](#9-pipeline-mensile-di-shadow-operations)
10. [Scoring successivo e decisione umana](#10-scoring-successivo-e-decisione-umana)
11. [Catalogo della CLI Python](#11-catalogo-della-cli-python)
12. [Fasi da completare per usare efficacemente il sistema](#12-fasi-da-completare-per-usare-efficacemente-il-sistema)
13. [Output, cartelle e artefatti](#13-output-cartelle-e-artefatti)
14. [Codici di uscita e gestione degli errori](#14-codici-di-uscita-e-gestione-degli-errori)
15. [Controlli di qualità e manutenzione](#15-controlli-di-qualità-e-manutenzione)
16. [Procedure da non eseguire](#16-procedure-da-non-eseguire)
17. [Checklist operative](#17-checklist-operative)
18. [Riferimenti](#18-riferimenti)

---

## 1. Come leggere questo manuale

Il sistema ha tre percorsi distinti. Non devono essere mescolati.

1. **Uso informativo ordinario:** prepara i dati, valida gli input, calcola il regime e produce una proposta allocativa vincolata.
2. **Uso storico e di ricerca:** costruisce dataset, valuta modelli e confronta baseline e challenger.
3. **Shadow Operations:** congela previsioni prospettiche mensili prima che gli esiti siano conoscibili.

Per l'uso quotidiano sono sufficienti la CLI C# e, facoltativamente, la dashboard Web. La CLI Python è necessaria per ricerca, validazione storica e Shadow Operations. I comandi E11-E14 non sono normali comandi operativi: riproducono passaggi formali già svolti o aprono workflow governati.

Gli esempi sono scritti per PowerShell e presuppongono che il terminale si trovi nella radice del progetto:

```powershell
Set-Location C:\ProgettiAzure\Codex\Macro
```

Nei comandi sostituire date e percorsi di esempio con quelli del ciclo reale. La data deve sempre usare il formato `yyyy-MM-dd`; gli istanti UTC devono usare una forma come `2026-08-01T08:00:00Z`.

---

## 2. Le modalità d'uso

| Modalità | Scopo | Rete | Scrive artefatti | Uso consigliato |
|---|---|---:|---:|---|
| Demo | Verificare installazione e interfaccia | No | Sì | Solo prova tecnica |
| Validazione | Controllare dati e configurazioni | No | Report Markdown | Prima di ogni run reale |
| Analisi singola | Calcolare regime e proposta | No | Run, report, manifest | Uso informativo ordinario |
| Batch | Ripetere l'analisi su più date | No | Più run e manifest | Confronti locali |
| Download FRED | Acquisire dati macro | Sì solo con `http` | Snapshot macro JSON | Preparazione input |
| Download market | Acquisire dati di mercato | Sì solo con `yahoo` | Snapshot market JSON | Dataset storico |
| Popolazione storica | Scaricare un corpus reale | Sì | Corpus e manifest | Ricerca controllata |
| Build dataset | Unire snapshot locali | No | Dataset storico JSON | Ricerca controllata |
| Baseline evaluation | Valutare ogni riga storica | No | Evaluation JSON | Ricerca controllata |
| Web | Consultare ed eventualmente rieseguire la pipeline configurata | No | Run locali | Consultazione |
| Shadow `prepare-only` | Preparare il ciclo mensile senza ledger | FRED/Yahoo tramite orchestratore | Dataset, evaluation, preflight, receipt | Prima verifica mensile |
| Shadow `full` | Congelare la previsione prospettica | FRED/Yahoo tramite orchestratore | Ledger write-once e indice | Solo dopo preflight riuscito |
| Shadow scoring | Valutare una previsione quando l'esito è disponibile | No | PredictionScore | Solo in un momento successivo |
| Gate decision | Registrare la decisione umana | No | GateDecision | Dopo review |

### 2.1 Modalità demo e modalità reale

Se non vengono forniti dati o configurazioni, la CLI usa fallback demo deterministici. Questo comportamento serve a verificare che il software funzioni, non a produrre una valutazione reale.

Per un uso informativo serio utilizzare sempre:

- input espliciti;
- `--strict-data`;
- `--strict-config`;
- una cartella di output dedicata;
- una data coerente con gli input;
- una validazione completata prima della run.

---

## 3. Prerequisiti e preparazione iniziale

### 3.1 Software richiesto

- Windows con PowerShell, oppure una shell equivalente;
- .NET SDK 10, perché i progetti usano `net10.0`;
- Python 3.12 o superiore;
- accesso a Internet soltanto per restore, installazione iniziale e acquisizione dati reali;
- API key FRED per le operazioni FRED reali;
- spazio locale sufficiente per corpus, dataset, run e ledger.

Verifica delle versioni:

```powershell
dotnet --version
python --version
```

### 3.2 Preparazione C#

Dalla radice del progetto:

```powershell
dotnet restore MacroRegime.slnx
dotnet build MacroRegime.slnx --no-restore
dotnet test MacroRegime.slnx --no-restore --no-build
```

Il sistema è pronto soltanto se build e test terminano senza errori.

### 3.3 Preparazione Python

È consigliato un ambiente virtuale dedicato:

```powershell
Set-Location research\regime-eval
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e .
python -m unittest discover -s tests -v
python -m compileall -q regime_eval tests
Set-Location ..\..
```

L'ambiente virtuale `.venv` non deve essere trattato come artefatto di progetto.

### 3.4 Configurazione della API key FRED

Metodo raccomandato per la sessione PowerShell:

```powershell
$env:FRED_API_KEY = "valore-della-chiave"
```

In alternativa si può creare localmente un file `.env` nella directory da cui viene eseguita la CLI:

```text
FRED_API_KEY=valore-della-chiave
```

Il file `.env` è escluso da Git. Non inserire la chiave:

- nei documenti;
- nei log;
- nei checkpoint;
- nei nomi dei file;
- nei comandi salvati o condivisi, se evitabile.

L'opzione `--fred-api-key` esiste, ma l'ambiente è preferibile perché riduce l'esposizione nella cronologia dei comandi.

### 3.5 Verifica degli help reali

Prima di una procedura delicata consultare l'help della versione installata:

```powershell
dotnet run --project src\MacroRegime.Cli -- --help
```

```powershell
Set-Location research\regime-eval
python -m regime_eval --help
python -m regime_eval shadow-operations --help
Set-Location ..\..
```

L'help del codice corrente prevale su un esempio datato.

---

## 4. Regole operative obbligatorie

### 4.1 Stabilire prima la data informativa

Prima di acquisire dati definire la **as-of date**, cioè la data limite della conoscenza. Per un ciclo mensile usare un mese effettivamente chiuso. Non scegliere una data soltanto perché produce un risultato più favorevole.

### 4.2 Non mescolare input di date diverse

Il file `macro-data-2026-07-31.json` deve essere usato con `--as-of 2026-07-31`. Anche portafoglio e configurazioni devono essere efficaci alla data dichiarata.

### 4.3 Separare acquisizione e analisi

I comandi di download producono file, ma non eseguono l'analisi. La run successiva legge i file locali. Questo confine consente di ispezionare e validare gli input prima del calcolo.

### 4.4 Usare modalità strict

Senza `--strict-data` o `--strict-config`, un input mancante può essere sostituito da un fallback demo. In una run reale questo non è accettabile.

### 4.5 Non sovrascrivere artefatti governati

Ledger, preflight e receipt sono write-once. In caso di errore usare recovery o un nuovo percorso versionato. Non correggere manualmente un JSON già congelato.

### 4.6 Non anticipare lo scoring

Il PredictionLedger non deve contenere ground truth o forward return. Lo score viene creato soltanto quando l'esito previsto dal protocollo è diventato legittimamente disponibile.

### 4.7 La decisione resta umana

Un regime o una proposta non sono un ordine. L'operatore deve leggere warning, qualità dei dati, confidenza, segnali contrari, turnover e vincoli prima di registrare una decisione.

---

## 5. Pipeline consigliata per una singola analisi

Questa è la procedura ordinaria più sicura ed efficiente.

### Fase 1 — Definire cutoff e cartelle

```powershell
$analysisDate = "2026-07-31"
$inputRoot = ".\data\operational\$analysisDate"
$outputRoot = ".\data\runs\$analysisDate"
New-Item -ItemType Directory -Force -Path $inputRoot | Out-Null
New-Item -ItemType Directory -Force -Path $outputRoot | Out-Null
```

Le directory sono esempi. Una convenzione stabile riduce errori e rende più facile l'audit.

### Fase 2 — Acquisire i dati macro

Per una prova offline deterministica:

```powershell
dotnet run --project src\MacroRegime.Cli -- --download-fred --as-of $analysisDate --fred-source stub --output-dir $inputRoot
```

Per dati FRED reali:

```powershell
dotnet run --project src\MacroRegime.Cli -- --download-fred --as-of $analysisDate --fred-source http --output-dir $inputRoot
```

Output previsto:

```text
data/operational/yyyy-MM-dd/macro-data-yyyy-MM-dd.json
```

Il download FRED reale seleziona il vintage previsto dall'adapter. Verificare sempre i warning e non assumere che ogni serie abbia una ricostruzione storica perfetta.

### Fase 3 — Preparare portafoglio e configurazioni

Occorrono:

- modello;
- feature set;
- IPS o allocation policy;
- portafoglio corrente;
- regole di tilt.

I file `samples/` mostrano lo schema:

```text
samples/model-version-baseline.json
samples/feature-set-baseline.json
samples/allocation-policy-balanced.json
samples/current-portfolio-2026-07-01.json
samples/regime-tilt-rules.json
```

Per una data reale non usare automaticamente il portafoglio sample. Preparare un file `current-portfolio-yyyy-MM-dd.json` coerente e validato.

### Fase 4 — Validare senza eseguire

```powershell
dotnet run --project src\MacroRegime.Cli -- `
  --as-of $analysisDate `
  --data "$inputRoot\macro-data-$analysisDate.json" `
  --model ".\samples\model-version-baseline.json" `
  --feature-set ".\samples\feature-set-baseline.json" `
  --policy ".\samples\allocation-policy-balanced.json" `
  --portfolio "$inputRoot\current-portfolio-$analysisDate.json" `
  --tilts ".\samples\regime-tilt-rules.json" `
  --strict-data `
  --strict-config `
  --validate-only `
  --validate-report "$outputRoot\import-validation-$analysisDate.md" `
  --output-dir $outputRoot
```

Procedere soltanto se il comando restituisce codice `0` e il report non contiene errori. I warning devono essere letti e valutati, non ignorati automaticamente.

### Fase 5 — Eseguire l'analisi

```powershell
dotnet run --project src\MacroRegime.Cli -- `
  --as-of $analysisDate `
  --data "$inputRoot\macro-data-$analysisDate.json" `
  --model ".\samples\model-version-baseline.json" `
  --feature-set ".\samples\feature-set-baseline.json" `
  --policy ".\samples\allocation-policy-balanced.json" `
  --portfolio "$inputRoot\current-portfolio-$analysisDate.json" `
  --tilts ".\samples\regime-tilt-rules.json" `
  --strict-data `
  --strict-config `
  --cost-per-turnover 0.001 `
  --output-dir $outputRoot
```

Output previsti:

```text
<output>/runs/regime-run-yyyy-MM-dd.json
<output>/runs/manifest.json
<output>/reports/macro-regime-report-yyyy-MM-dd.md
```

### Fase 6 — Leggere il risultato

Controllare, nell'ordine:

1. esito tecnico della run;
2. as-of date e fonti;
3. regime primario;
4. regime operativo;
5. distribuzione completa delle probabilità;
6. confidenza;
7. driver e segnali contrari;
8. warning sui dati;
9. proposta allocativa;
10. turnover e costo stimato;
11. vincoli rispettati o bloccanti;
12. manifest e percorsi degli artefatti.

Se il regime operativo è `UncertainTransition`, il sistema sta comunicando incertezza: non va forzato manualmente un regime alternativo.

### Fase 7 — Registrare la decisione

La decisione umana deve riportare almeno:

- data;
- run considerata;
- decisione presa;
- motivazione;
- eventuale scostamento dalla proposta;
- rischi e warning accettati;
- identità del decisore.

Il progetto dispone del comando Python `gate-decision` per le decisioni di Model Gate; una decisione allocativa deve comunque rispettare il processo di governance previsto dall'IPS.

---

## 6. Catalogo completo della CLI C#

La forma generale è:

```powershell
dotnet run --project src\MacroRegime.Cli -- <argomenti-del-sistema>
```

Il doppio trattino separa gli argomenti di `dotnet run` dagli argomenti di MacroRegime.

### 6.1 Help

```powershell
dotnet run --project src\MacroRegime.Cli -- --help
```

### 6.2 Run demo

```powershell
dotnet run --project src\MacroRegime.Cli -- --as-of 2026-07-01 --output-dir .\.tmp\demo-run
```

Usa dati e configurazioni demo. Serve soltanto come smoke test.

### 6.3 Validazione import/config

```powershell
dotnet run --project src\MacroRegime.Cli -- --as-of 2026-07-01 --data .\samples\macro-data-2026-07-01.json --model .\samples\model-version-baseline.json --feature-set .\samples\feature-set-baseline.json --policy .\samples\allocation-policy-balanced.json --portfolio .\samples\current-portfolio-2026-07-01.json --tilts .\samples\regime-tilt-rules.json --strict-data --strict-config --validate-only --output-dir .\.tmp\validation
```

`--validate-report` consente di indicare un percorso Markdown esplicito.

### 6.4 Analisi singola

Opzioni:

| Opzione | Funzione |
|---|---|
| `--as-of` | Data dell'analisi, obbligatoria |
| `--data` | Snapshot macro JSON |
| `--model` | Versione modello JSON |
| `--feature-set` | Definizione feature JSON |
| `--policy` | Politica allocativa JSON |
| `--portfolio` | Portafoglio corrente JSON |
| `--tilts` | Regole di tilt JSON |
| `--strict-data` | Blocca dati mancanti o data incoerente |
| `--strict-config` | Blocca configurazioni mancanti o non efficaci |
| `--cost-per-turnover` | Costo stimato per unità di turnover; default `0.001` |
| `--output-dir` | Directory di output; default `macro-regime-output` |

### 6.5 Batch di date

```powershell
dotnet run --project src\MacroRegime.Cli -- `
  --batch-from 2026-07-01 `
  --batch-to 2026-07-31 `
  --data-dir .\data\macro `
  --portfolio-dir .\data\portfolio `
  --model .\samples\model-version-baseline.json `
  --feature-set .\samples\feature-set-baseline.json `
  --policy .\samples\allocation-policy-balanced.json `
  --tilts .\samples\regime-tilt-rules.json `
  --strict-data `
  --strict-config `
  --output-dir .\data\batch-output
```

Convenzioni richieste nelle directory:

```text
macro-data-yyyy-MM-dd.json
current-portfolio-yyyy-MM-dd.json
```

Il batch continua dopo l'errore di una singola data e termina con il riepilogo di successi e fallimenti. Un batch parzialmente fallito restituisce codice `2`.

### 6.6 Download FRED

Stub offline:

```powershell
dotnet run --project src\MacroRegime.Cli -- --download-fred --as-of 2026-07-31 --fred-source stub --output-dir .\data\macro
```

HTTP reale:

```powershell
dotnet run --project src\MacroRegime.Cli -- --download-fred --as-of 2026-07-31 --fred-source http --output-dir .\data\macro
```

`--fred-source` ammette soltanto `stub` e `http`.

### 6.7 Download market data

Stub offline:

```powershell
dotnet run --project src\MacroRegime.Cli -- --download-market-data --as-of 2026-07-31 --market-source stub --output-dir .\data\market
```

Yahoo reale:

```powershell
dotnet run --project src\MacroRegime.Cli -- --download-market-data --as-of 2026-07-31 --market-source yahoo --output-dir .\data\market
```

Yahoo usa un endpoint chart non ufficiale e sostituibile. Il file market non entra direttamente nella run informativa singola; serve soprattutto alla costruzione del dataset storico.

### 6.8 Popolazione storica reale

```powershell
dotnet run --project src\MacroRegime.Cli -- `
  --populate-historical-data `
  --dataset-from 2008-01-01 `
  --dataset-to 2025-12-31 `
  --macro-data-dir .\data\historical\macro `
  --market-data-dir .\data\historical\market `
  --corpus-manifest .\data\historical\historical-data-corpus-manifest.json `
  --forward-return-days 28,56,91 `
  --output-dir .\data\historical\population
```

Richiede FRED e Yahoo reali. È un'operazione di ricerca, non una fase necessaria per ogni run.

### 6.9 Costruzione dataset da file locali

```powershell
dotnet run --project src\MacroRegime.Cli -- `
  --build-historical-dataset `
  --dataset-from 2008-01-01 `
  --dataset-to 2025-12-31 `
  --macro-data-dir .\data\historical\macro `
  --market-data-dir .\data\historical\market `
  --forward-return-days 28,56,91 `
  --output-dir .\data\historical\dataset
```

Non usa la rete. Produce `historical-dataset-from-to.json` e segnala righe, date saltate e forward return.

### 6.10 Valutazione storica della baseline

```powershell
dotnet run --project src\MacroRegime.Cli -- `
  --evaluate-historical-baseline `
  --dataset-file .\data\historical\dataset\historical-dataset-2008-01-01-2025-12-31.json `
  --baseline-version v1.4 `
  --output-dir .\data\historical\evaluation
```

Versioni ammesse: `demo`, `v1`, `v1.1`, `v1.2`, `v1.3`, `v1.4`. Per riprodurre l'evidenza corrente usare la versione richiesta dal contratto, non scegliere quella con il risultato migliore.

### 6.11 Comandi mutuamente esclusivi

Eseguire separatamente:

- download FRED;
- download market;
- popolazione storica;
- build dataset;
- valutazione baseline;
- validazione o run ordinaria.

La CLI rifiuta combinazioni che confonderebbero acquisizione, valutazione e analisi.

---

## 7. Uso della dashboard Web

### 7.1 Avvio

```powershell
dotnet run --project src\MacroRegime.Web
```

Profilo locale predefinito:

```text
http://localhost:5120
```

### 7.2 Pagine disponibili

| Percorso | Funzione |
|---|---|
| `/` | Esegue o riesegue la pipeline configurata per una as-of date |
| `/RunDetail?asOfDate=yyyy-MM-dd` | Legge un run JSON salvato senza riesecuzione |
| `/CompareRuns` | Confronta due run salvati |
| `/ImportDiagnostics?asOfDate=yyyy-MM-dd` | Mostra la diagnostica degli input |

### 7.3 Configurazione

La configurazione predefinita è in:

```text
src/MacroRegime.Web/appsettings.json
```

Per impostazione iniziale punta ai sample del 1 luglio 2026 e usa modalità strict. Non cambiare data nella pagina aspettandosi che compaiano automaticamente file nuovi: anche i percorsi configurati devono essere coerenti.

È possibile sovrascrivere la cartella dei run tramite variabile ambiente ASP.NET:

```powershell
$env:MacroRegime__OutputDirectory = "C:\percorso\ai\run"
dotnet run --project src\MacroRegime.Web
```

Lo stesso schema a doppio underscore è applicabile alle altre proprietà `MacroRegime`. Verificare sempre il riepilogo della configurazione mostrato dalla pagina.

### 7.4 Uso consigliato della Web

Per massima controllabilità:

1. acquisire, validare ed eseguire la run con la CLI;
2. configurare la Web sulla medesima cartella di output;
3. usare `RunDetail` per leggere l'artefatto salvato;
4. usare `CompareRuns` per confrontare date;
5. evitare di usare la dashboard come downloader: la Web non ha rete per progetto.

---

## 8. Pipeline per dataset storico e valutazione

Questa pipeline non va ripetuta ogni mese se il corpus non è cambiato.

### Passo 1 — Popolare o aggiornare il corpus

Usare `--populate-historical-data` soltanto per il periodo nuovo o per una ricostruzione formalmente autorizzata. Conservare il manifest del corpus.

### Passo 2 — Costruire il dataset

Usare `--build-historical-dataset` sugli snapshot locali. Controllare:

- prima e ultima data;
- righe prodotte;
- date saltate;
- orizzonti forward return;
- percorso dell'output.

### Passo 3 — Valutare la baseline in C#

Usare `--evaluate-historical-baseline` con la versione preregistrata.

### Passo 4 — Entrare nel laboratorio Python

```powershell
Set-Location research\regime-eval
```

### Passo 5 — Validare dataset e manifest

```powershell
python -m regime_eval validate <dataset.json>
python -m regime_eval manifest <dataset.json> --output <dataset-manifest.json>
```

### Passo 6 — Congelare il piano walk-forward

```powershell
python -m regime_eval plan-walk-forward <dataset.json> --train-years 10 --test-years 2 --step-years 1 --output <walk-forward-plan.json>
```

Se non esiste almeno un fold completo, il comando restituisce codice `2`.

### Passo 7 — Produrre report e gate baseline

```powershell
python -m regime_eval baseline-report --evaluation <evaluation.json> --dataset <dataset.json> --plan <walk-forward-plan.json> --output <baseline-report.json>
```

```powershell
python -m regime_eval baseline-audit --evaluation <evaluation.json> --dataset <dataset.json> --plan <walk-forward-plan.json> --config models\baseline-audit-v1.json --output <baseline-audit.json>
```

```powershell
python -m regime_eval baseline-train-gate --evaluation <evaluation.json> --dataset <dataset.json> --plan <walk-forward-plan.json> --config models\baseline-v1-4-train-gate-v2-preregistered.json --output <train-gate.json>
```

### Passo 8 — Report di ground truth ed evidenza

I comandi disponibili comprendono:

- `recession-report`;
- `stress-report`;
- `evidence-report`;
- `clustering-report`;
- `hmm-report`;
- `dual-timescale-report`.

Usarli soltanto con configurazioni e ground truth versionati. K-means, HMM e dual-timescale restano challenger respinti nel ciclo già concluso; rieseguirli non li promuove.

### Passo 9 — Uscire dal laboratorio

```powershell
Set-Location ..\..
```

---

## 9. Pipeline mensile di Shadow Operations

Questa è la pipeline consigliata per l'uso prospettico. È più efficiente e meno soggetta a errori della sequenza manuale.

### 9.1 Quando eseguirla

Eseguire il ciclo soltanto quando:

- il mese precedente è chiuso;
- gli input richiesti sono stati pubblicati;
- la API key FRED è disponibile;
- build e test sono verdi;
- non esiste già un ledger per quel mese;
- il modello e il protocollo non sono cambiati senza approvazione.

Il primo cutoff prospettico completo atteso dopo lo stato corrente è il 31 luglio 2026.

### 9.2 Preparare l'ambiente

```powershell
$env:FRED_API_KEY = "valore-della-chiave"
Set-Location research\regime-eval
```

La root operativa corrente è:

```text
data/shadow-live-2026/
```

### 9.3 Eseguire `prepare-only`

```powershell
python -m regime_eval shadow-operations `
  --source-root ..\.. `
  --operations-root ..\..\data\shadow-live-2026 `
  --model-config models\baseline-v1-4-preregistered.json `
  --generated-at-utc 2026-08-01T08:00:00Z `
  --mode prepare-only `
  --result ..\..\data\shadow-live-2026\operations-audit\shadow-operations-2026-08-01-prepare-only.json
```

`prepare-only` esegue:

1. selezione del prossimo mese eleggibile;
2. popolazione dati;
3. costruzione dataset;
4. valutazione baseline C#;
5. preflight;
6. persistenza di stato e receipt.

Non crea il PredictionLedger.

### 9.4 Interpretare l'esito di preparazione

Stati possibili:

| Stato | Significato | Azione |
|---|---|---|
| `prepared` | Tutti i passaggi preparatori sono validi | Review e poi `full` |
| `no-eligible-month` | Non esiste un nuovo mese da elaborare | Non fare nulla |
| `failed` | Un passaggio operativo è fallito | Leggere receipt e log; correggere la causa |
| stato intermedio/recovery | Esistono step completati e verificabili | Ripetere lo stesso ciclo senza cancellare artefatti |

Controllare nella receipt:

- mese selezionato;
- comandi eseguiti;
- exit code;
- hash;
- assenza di outcome;
- esito del preflight;
- percorsi di dataset ed evaluation;
- eventuali warning di freschezza.

### 9.5 Eseguire `full`

Solo dopo review positiva del `prepare-only`:

```powershell
python -m regime_eval shadow-operations `
  --source-root ..\.. `
  --operations-root ..\..\data\shadow-live-2026 `
  --model-config models\baseline-v1-4-preregistered.json `
  --generated-at-utc 2026-08-01T08:15:00Z `
  --mode full `
  --result ..\..\data\shadow-live-2026\operations-audit\shadow-operations-2026-08-01-full.json
```

`full` riutilizza gli step completati e invariati, quindi:

1. verifica gli hash;
2. non ripete inutilmente population/build/evaluation;
3. congela il ledger write-once;
4. ricostruisce `shadow-index.json`;
5. salva una receipt distinta.

### 9.6 Recovery

Se il ciclo fallisce:

- non cancellare `cycle-state.json`;
- non modificare file completati;
- correggere soltanto la causa esterna, per esempio credenziale o disponibilità;
- rieseguire il comando con un nuovo percorso di receipt se il precedente è già stato scritto;
- lasciare che l'orchestratore verifichi gli hash e riparta dal primo step incompleto.

Un file completato ma modificato deve bloccare il recovery. Non aggirare il blocco.

### 9.7 Comandi Shadow a basso livello

Sono disponibili per test, diagnosi o recovery controllato:

```text
shadow-predict
shadow-preflight
shadow-cycle
shadow-index
```

Nell'operatività mensile preferire `shadow-operations`. La sequenza manuale minima sarebbe:

```powershell
python -m regime_eval shadow-preflight --evaluation <evaluation.json> --dataset <dataset.json> --model-config models\baseline-v1-4-preregistered.json --as-of 2026-07-31 --generated-at-utc 2026-08-01T08:00:00Z --source-root ..\.. --output <preflight.json>
```

```powershell
python -m regime_eval shadow-cycle --evaluation <evaluation.json> --dataset <dataset.json> --model-config models\baseline-v1-4-preregistered.json --preflight <preflight.json> --as-of 2026-07-31 --generated-at-utc 2026-08-01T08:05:00Z --output <ledger.json> --index <shadow-index.json>
```

`shadow-predict --run-mode shadow-live` richiede il preflight. `shadow-index` ricostruisce soltanto una vista derivata.

---

## 10. Scoring successivo e decisione umana

### 10.1 Shadow score

Quando la ground truth prevista dal contratto è disponibile:

```powershell
Set-Location research\regime-eval
python -m regime_eval shadow-score `
  --ledger <prediction-ledger.json> `
  --ground-truth ground-truth\nber-us-recessions-v1.json `
  --scored-at-utc 2027-01-01T08:00:00Z `
  --output <prediction-score.json>
```

La data è esemplificativa. Usare la ground truth e il tempo di maturazione stabiliti dal contratto applicabile.

### 10.2 Gate decision

```powershell
python -m regime_eval gate-decision `
  --report <model-report.json> `
  --decision deferred `
  --reviewer "research-owner" `
  --rationale "Evidenza prospettica ancora insufficiente." `
  --decided-at-utc 2027-01-01T09:00:00Z `
  --output <gate-decision.json>
```

Decisioni ammesse:

- `approved`;
- `rejected`;
- `deferred`.

`approved` non autorizza automaticamente trading, rete, pubblicazione, ottimizzazione o downstream non elencati nel gate.

---

## 11. Catalogo della CLI Python

### 11.1 Regola generale

Dalla directory `research/regime-eval`:

```powershell
python -m regime_eval <comando> --help
```

### 11.2 Comandi fondamentali di dataset

| Comando | Funzione |
|---|---|
| `validate` | Valida e riassume un dataset |
| `manifest` | Scrive il manifest di riproducibilità |
| `plan-walk-forward` | Costruisce i fold temporali |

### 11.3 Comandi baseline e confronto modelli

| Comando | Funzione |
|---|---|
| `baseline-report` | Riassume i risultati baseline sui fold |
| `baseline-audit` | Controlla saturazione feature e diversità dei regimi |
| `baseline-train-gate` | Applica il gate train-only preregistrato |
| `recession-report` | Confronta `DeflationBust` con i mesi NBER |
| `stress-report` | Valuta l'allineamento sugli stress non recessivi |
| `evidence-report` | Valuta evidenza probabilistica e sufficienza per la promozione |
| `clustering-report` | Esegue il challenger k-means deterministico |
| `hmm-report` | Esegue il challenger Gaussian HMM |
| `dual-timescale-report` | Esegue il challenger causale dual-timescale |

### 11.4 Comandi Shadow e decisione

| Comando | Funzione |
|---|---|
| `shadow-predict` | Congela previsioni senza outcome |
| `shadow-preflight` | Congela i controlli del ciclo |
| `shadow-cycle` | Crea o recupera idempotentemente un ledger |
| `shadow-index` | Ricostruisce l'indice derivato |
| `shadow-operations` | Orchestra il ciclo mensile completo |
| `shadow-score` | Valuta più tardi un ledger immutabile |
| `gate-decision` | Registra la decisione umana |

### 11.5 Comandi E11

```text
e11-preregister
e11-dimensional-baseline-gate
e11-challenger-gate
```

Servono a preregistrare e valutare candidati su inner validation. Non costituiscono una pipeline operativa ordinaria.

### 11.6 Comandi E12

```text
e12-freeze-foundation
e12-preregister-financial-stress
e12-financial-stress-gate
e12-preregister-recession-hazard
e12-recession-hazard-gate
```

Gestiscono fondazione event-aware e gate di stress/hazard già conclusi con esiti governati.

### 11.7 Comandi E13

```text
e13-generate-candidates
e13-loeo-evaluate
e13-freeze-shortlist
e13-financial-absolute-gate
```

Espandono una grammatica congelata, eseguono LOEO, congelano shortlist e applicano gate assoluti.

### 11.8 Comandi E14 — fondazione informativa e candidati

```text
e14-information-audit
e14-label-audit
e14-historical-feasibility
e14-mechanism-contract-audit
e14-curate-positive-dossiers
e14-adjudication-queue
e14-build-review-handoff
e14-ingest-independent-reviews
e14-targeted-dossier-revision
e14-ingest-targeted-reviews
e14-hard-negative-coverage-gate
e14-label-foundation-gate
e14-materialize-taxonomy-v4
e14-curate-hard-negative-expansion
e14-build-hard-negative-expansion-handoff
e14-ingest-hard-negative-expansion-reviews
e14-revise-hard-negative-expansion
e14-ingest-hard-negative-targeted-reviews
e14-materialize-taxonomy-v5
e14-candidate-readiness-gate
e14-materialize-feature-foundation
e14-freeze-candidate-protocol
e14-generate-candidates
e14-preregister-loeo
e14-preregister-coverage-repair
e14-materialize-feature-foundation-v2
e14-readiness-gate-v2
e14-freeze-candidate-protocol-v2
e14-materialize-candidate-manifest-v2
e14-preregister-loeo-v2
e14-loeo-evaluate-v2
e14-diagnose-loeo-no-go
```

### 11.9 Comandi E14.7 — nuove informazioni, fonti e vintage

```text
e14-preregister-new-information
e14-audit-source-vintage-feasibility
e14-preregister-feasibility-remediation
e14-reaudit-replacement-source-feasibility
e14-preregister-vintage-policy-decision
e14-audit-post2005-scope-feasibility
e14-preregister-post2005-taxonomy-proposal
e14-build-post2005-review-handoff
e14-ingest-post2005-independent-reviews
e14-revise-post2005-dossier
e14-ingest-post2005-targeted-review
e14-activate-post2005-scope
e14-preregister-post2005-source-acquisition
e14-gate-post2005-source-execution
e14-acquire-post2005-sources
e14-audit-post2005-vintage-fitness
e14-preregister-post2005-vintage-remediation
e14-preregister-post2005-policy-redesign
e14-audit-post2005-policy-redesign-handoff
e14-remediate-post2005-policy-redesign-review
e14-build-post2005-policy-redesign-review-handoff
e14-ingest-post2005-policy-redesign-reviews
e14-activate-post2005-policy-redesign
e14-preregister-post2005-source-acquisition-v2
e14-gate-post2005-source-execution-v2
e14-preflight-post2005-source-acquisition-v2
e14-preregister-post2005-acquisition-remediation
e14-preregister-fdic-publication-metadata
e14-gate-fdic-publication-metadata-execution
e14-preflight-fdic-publication-metadata-collection
e14-preregister-fdic-publication-metadata-request-catalog
e14-materialize-fdic-archive-quarter-map
e14-preregister-fdic-archive-evidence-collection
e14-remediate-fdic-archive-evidence-model
e14-implement-fdic-archive-atomic-producer
```

Questi comandi implementano una catena fail-closed. La loro presenza non autorizza acquisizione, pubblicazione o trasformazione. Devono essere eseguiti soltanto nell'ordine stabilito da contratto e checkpoint.

### 11.10 E14.8

E14.8 ha chiuso il disegno del futuro provisioning di un'autorità monotona esterna. Non esiste un normale comando operativo di provisioning autorizzato. Provider, credenziali, adapter, risorse remote e pubblicazione restano bloccati.

---

## 12. Fasi da completare per usare efficacemente il sistema

### 12.1 Attivazione iniziale, una sola volta

1. installare .NET 10 e Python 3.12+;
2. eseguire restore, build e test C#;
3. preparare l'ambiente Python e i test;
4. ottenere e proteggere la API key FRED;
5. definire cartelle operative e backup;
6. predisporre IPS, portafoglio, feature, modello e tilt versionati;
7. verificare help e configurazione Web.

### 12.2 Per ogni analisi informativa

1. scegliere l'as-of date;
2. acquisire o selezionare lo snapshot macro;
3. predisporre il portafoglio della stessa data;
4. validare in modalità strict;
5. risolvere errori e valutare warning;
6. eseguire la run;
7. leggere run e report;
8. confrontare con il run precedente;
9. registrare la decisione umana;
10. conservare gli artefatti.

### 12.3 Per ogni ciclo shadow mensile

1. attendere la chiusura del mese;
2. verificare ambiente e credenziale;
3. eseguire `shadow-operations --mode prepare-only`;
4. revisionare receipt, log, hash e preflight;
5. se `prepared`, eseguire `--mode full`;
6. verificare il ledger e l'indice;
7. non acquisire outcome anticipati;
8. in seguito produrre lo score;
9. registrare il GateDecision.

### 12.4 Fasi progettuali ancora aperte

Al 17 luglio 2026:

- E14.8 è chiusa `design-complete` e `safely blocked`;
- la fase E richiede ancora la prima esecuzione prospettica full E9 al cutoff del 31 luglio 2026 e il relativo closeout;
- la fase F non è iniziata;
- la selezione di un provider per l'autorità esterna è una fase futura separata e non autorizzata.

### 12.5 Fase F futura

Quando autorizzata, dovrà completare:

1. ottimizzazione allocativa vincolata;
2. stress test storici;
3. stress fattoriali;
4. reverse stress test.

Fino ad allora la proposta corrente resta rule-based e vincolata; non va descritta come ottimizzazione completa.

---

## 13. Output, cartelle e artefatti

### 13.1 Run ordinaria

```text
<output-dir>/
├── import-validation/
│   └── import-validation-yyyy-MM-dd.md
├── reports/
│   └── macro-regime-report-yyyy-MM-dd.md
└── runs/
    ├── regime-run-yyyy-MM-dd.json
    └── manifest.json
```

Il run JSON è la fonte autorevole del risultato storico. Il report Markdown è una rappresentazione leggibile. Il manifest è una vista di consultazione.

### 13.2 Corpus storico

```text
data/historical/
├── macro/
├── market/
├── dataset/
├── evaluation/
└── historical-data-corpus-manifest.json
```

### 13.3 Shadow Operations

```text
data/shadow-live-2026/
├── cycles/
│   └── yyyy-MM/
│       ├── source/
│       ├── dataset/
│       ├── evaluation/
│       ├── preflight/
│       ├── logs/
│       └── cycle-state.json
├── ledger/
│   ├── prediction-ledger-yyyy-MM-dd-....json
│   └── shadow-index.json
└── operations-audit/
    └── shadow-operations-....json
```

`cycle-state.json` è operativo e ricostruibile; preflight, ledger e receipt sono evidenze più forti e non devono essere sovrascritti.

### 13.4 Directory `.tmp`

`.tmp` contiene smoke test, output Web e chiavi Data Protection locali. È ignorata da Git e non è un archivio autorevole. Non usare `.tmp` per l'unica copia di un ledger o di una decisione.

---

## 14. Codici di uscita e gestione degli errori

### 14.1 CLI C#

| Codice | Significato |
|---:|---|
| `0` | Comando completato |
| `1` | Errore di sintassi o combinazione di opzioni |
| `2` | Validazione bloccante o errore operativo |

### 14.2 CLI Python

| Codice | Significato generale |
|---:|---|
| `0` | Esecuzione tecnica completata; leggere comunque lo stato nell'artefatto |
| `2` | Dataset non valido o copertura insufficiente |
| `3` | Gate non superato, no-go o capacità non autorizzata in diversi workflow di ricerca |
| `4` | `shadow-operations` terminato con stato `failed` |

Un codice non zero non va trasformato manualmente in successo. In particolare, `3` può essere un esito scientifico o di governance corretto.

### 14.3 Procedura dopo un errore

1. conservare messaggio, log e receipt;
2. identificare lo step che ha fallito;
3. non modificare artefatti write-once;
4. correggere input, configurazione o prerequisito;
5. ripetere soltanto il comando consentito;
6. verificare che il recovery riusi gli artefatti invariati;
7. documentare una deviazione materiale.

---

## 15. Controlli di qualità e manutenzione

### 15.1 Prima di un ciclo operativo

```powershell
dotnet build MacroRegime.slnx --no-restore
dotnet test MacroRegime.slnx --no-restore --no-build
```

```powershell
Set-Location research\regime-eval
python -m unittest discover -s tests -v
python -m compileall -q regime_eval tests
Set-Location ..\..
```

### 15.2 Verifica integrità

Controllare che:

- i file citati esistano;
- gli hash coincidano;
- il manifest punti ai file corretti;
- le date siano coerenti;
- non vi siano outcome nel ledger;
- il modello e la feature set version siano quelli approvati;
- i warning siano stati letti.

### 15.3 Backup

Eseguire backup versionati di:

- dati sorgente;
- configurazioni approvate;
- run JSON;
- manifest;
- ledger e score;
- GateDecision;
- checkpoint e review receipt.

Un backup locale non sostituisce l'autorità monotona esterna progettata in E14.8.

### 15.4 Aggiornamento delle dipendenze

Aggiornare .NET, Python o pacchetti soltanto come modifica controllata:

1. registrare versioni prima e dopo;
2. eseguire l'intera suite di test;
3. verificare fingerprint e riproducibilità;
4. non usare il nuovo ambiente su un ledger già preparato senza nuova review.

---

## 16. Procedure da non eseguire

Non:

- usare fallback demo in una run presentata come reale;
- cambiare la as-of date senza cambiare gli input;
- inserire forward return o ground truth in un PredictionLedger;
- eseguire `shadow-score` prima della disponibilità legittima dell'esito;
- sovrascrivere ledger, preflight o receipt;
- cancellare lo stato del ciclo per aggirare un conflitto;
- scegliere una baseline version dopo aver confrontato gli esiti;
- rilanciare challenger respinti e considerarli promossi;
- usare `e14-*` fuori dal contratto/checkpoint applicabile;
- interpretare E14.8 come autorizzazione al provisioning;
- avviare rete dal Web o dai layer core;
- salvare la API key nel repository;
- trasformare la proposta allocativa in ordine automatico;
- ignorare `UncertainTransition`, warning o gate bloccanti;
- passare alla fase F prima della chiusura formale della fase E.

---

## 17. Checklist operative

### 17.1 Analisi singola

- [ ] As-of date definita e periodo chiuso.
- [ ] Snapshot macro acquisito e ispezionato.
- [ ] Portafoglio corrente coerente con la data.
- [ ] Modello, feature, policy e tilt approvati.
- [ ] `--strict-data` e `--strict-config` attivi.
- [ ] `--validate-only` terminato con codice 0.
- [ ] Warning valutati.
- [ ] Run terminata con codice 0.
- [ ] Regime primario e operativo letti entrambi.
- [ ] Distribuzione, confidenza e segnali contrari letti.
- [ ] Proposta, turnover, costo e vincoli verificati.
- [ ] Run JSON, report e manifest conservati.
- [ ] Decisione umana registrata.

### 17.2 Shadow mensile

- [ ] Mese chiuso e nuovo mese eleggibile.
- [ ] Build e test verdi.
- [ ] API key disponibile senza esposizione.
- [ ] Configurazione baseline congelata.
- [ ] `prepare-only` completato.
- [ ] Receipt, log, hash e preflight verificati.
- [ ] Nessun outcome presente.
- [ ] `full` autorizzato ed eseguito.
- [ ] Ledger write-once presente.
- [ ] ShadowIndex ricostruito.
- [ ] Nessun file autorevole sovrascritto.
- [ ] Scoring rinviato al momento previsto.

### 17.3 Ricerca e promozione

- [ ] Ipotesi preregistrata.
- [ ] Dataset e manifest congelati.
- [ ] Piano walk-forward congelato.
- [ ] Train Gate eseguito prima dell'OOS.
- [ ] Baseline usata come confronto.
- [ ] Risultati negativi conservati.
- [ ] Model Card aggiornata.
- [ ] Review indipendente completata.
- [ ] GateDecision umano registrato.
- [ ] Aperte soltanto le capacità esplicitamente autorizzate.

---

## 18. Riferimenti

- [Descrizione generale e glossario](readme.md)
- [Piano operativo](docs/0001-piano-operativo.md)
- [Riepilogo del lavoro](docs/0002-riepilogo-lavoro-svolto.md)
- [Governance](docs/planning/0003-governance-progetto.md)
- [Architettura](docs/architecture/0001-architettura-sistema-scelte-letteratura-glossario.md)
- [ADR sulla persistenza](docs/adr/0003-persistenza-locale-file-based.md)
- [ADR sull'isolamento della rete](docs/adr/0004-isolamento-rete-adapter-fred.md)
- [Laboratorio Python](research/regime-eval/README.md)
- [Protocollo del laboratorio](research/regime-eval/PROTOCOL.md)
- [Checkpoint finale E14.8](docs/checkpoints/0145-fase-e14-8c-provisioning-design-review-accepted.md)

In caso di conflitto, prevalgono nell'ordine: contratto specifico applicabile, checkpoint più recente, help della versione del codice in esecuzione, questo manuale.

---

## Sequenza raccomandata in una riga

```text
prepara ambiente → scegli cutoff → acquisisci dati → valida strict → esegui → leggi e confronta → registra decisione → congela evidenze → valuta gli esiti soltanto quando maturi
```

Per il ciclo prospettico mensile:

```text
shadow-operations prepare-only → review preflight/receipt → shadow-operations full → attesa outcome → shadow-score → GateDecision umano
```
