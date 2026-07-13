# Macro Regime - Fase E - Slice 1: Research data gate - Done

Data: 2026-07-13

## Scopo della slice

Aprire il research lab della Fase E senza introdurre subito modelli avanzati. La
prima condizione e' rendere verificabile, riproducibile e point-in-time il dataset
storico prodotto dalla Fase D.

## Cosa e' stato realizzato

### Research lab isolato

Creata `research/regime-eval/` come area Python indipendente dalla solution C#.
Non sono state aggiunte dipendenze a Domain, Application, Infrastructure, CLI o
Web. La prima slice usa solo la standard library Python 3.12+.

### Protocollo

`PROTOCOL.md` formalizza:

- dataset gate e manifest obbligatorio;
- controlli anti-leakage sulle date point-in-time;
- walk-forward rolling 10 anni train / 2 anni test / step 1 anno;
- divieto di selezionare iperparametri sul test;
- confronto obbligatorio contro la baseline;
- conservazione dei risultati negativi;
- promozione solo tramite Model Gate e approvazione umana.

### Validazione dataset

Il package `regime_eval` legge `historical-dataset` schema v1 e controlla:

- intervallo dichiarato, righe ordinate e date uniche;
- observation/publication/availability date non successive all'as-of;
- simboli e valori numerici finiti;
- orizzonti forward return dichiarati;
- `fromDate` uguale all'as-of e `toDate` non precedente al target;
- coerenza di `(end / start) - 1` con il return salvato.

### Manifest riproducibile

Il comando `manifest` salva:

- SHA-256 e dimensione del dataset;
- versione schema;
- copertura dichiarata ed effettiva;
- numero righe, date mancanti e coverage ratio;
- simboli market e orizzonti forward return;
- esito del gate point-in-time.

Il manifest non contiene timestamp variabili, quindi a parita' di input e' stabile.

### Walk-forward planner

Il planner crea finestre rolling non sovrapposte tra train e test. Un dataset con
meno di 12 anni completi non produce fold: il sample demo non puo' quindi essere
scambiato per un dataset valido per Model Gate.

### CLI

Comandi disponibili dalla directory `research/regime-eval/`:

```text
python -m regime_eval validate <dataset>
python -m regime_eval manifest <dataset> --output <manifest.json>
python -m regime_eval plan-walk-forward <dataset>
```

## Verifiche eseguite

```text
python -m unittest discover -s tests -v
python -m compileall -q regime_eval tests
dotnet build MacroRegime.slnx --no-restore
dotnet test MacroRegime.slnx --no-restore --no-build
```

Esito:

- 6 test Python superati;
- compilazione moduli Python superata;
- build C# superata con 0 warning e 0 errori;
- 211 test C# superati, 0 falliti (Domain 80, Application 30,
  Infrastructure 76, Reporting 2, CLI 17, Web 6);
- nessun `HttpClient`/`System.Net.Http` nei sorgenti di
  Domain/Application/Web.

## Punti importanti mantenuti nel piano

- Il dataset reale pluriennale non e' ancora popolato: e' il prossimo gate.
- Il manifest implementato copre il singolo dataset; per corpus molto grandi
  restano da progettare indici operativi file-based.
- Il calendario release e' disponibile come client Infrastructure ma non e'
  ancora persistito o integrato nel dataset di ricerca.
- Backtesting, metriche composite, challenger e model card non sono inclusi in
  questa slice.
- Gli stress test restano previsti dopo la base walk-forward e non devono essere
  confusi con la validazione del dataset.

## Valutazione

La Fase E e' iniziata con un confine sicuro: il runtime C# produce artefatti e il
research lab Python li consuma in sola lettura. Il primo challenger puo' essere
introdotto solo dopo avere popolato un dataset reale sufficiente e superato questo
data gate.
