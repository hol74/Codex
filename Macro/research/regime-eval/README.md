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
python -m unittest discover -s tests -v
```

Il laboratorio usa solo la standard library Python. Le dipendenze scientifiche
verranno introdotte in una slice successiva, insieme al primo challenger e alla
relativa model card.

## Gate prima dei challenger

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
