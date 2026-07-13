# Macro Regime - Fase E - Slice 2: Dataset reale pluriennale - Done

Data: 2026-07-13

## Scopo

Superare il gate rimasto aperto nella Slice E1: costruire, manifestare e validare
un dataset reale abbastanza lungo per il walk-forward 10 anni train / 2 anni test
/ step 1 anno, mantenendo la ricostruibilita' point-in-time e l'isolamento della
rete in Infrastructure.

## Implementazione

Sono stati aggiunti:

- `FredHistoricalDataClient`, con richieste bulk FRED e finestre ALFRED di cinque
  anni per rispettare il limite delle vintage date;
- ricostruzione `INDPRO_YOY` dai livelli initial-release `INDPRO`;
- ricostruzione `SAHM` dalle initial release `UNRATE`;
- `YahooHistoricalMarketDataClient`, una richiesta range per simbolo;
- `HistoricalDataPopulator`, snapshot mensili macro, snapshot market giornalieri
  e manifest aggregato SHA-256;
- CLI `--populate-historical-data` e `--corpus-manifest`;
- output file per `plan-walk-forward` nel research lab.

Il runtime Domain/Application/Web resta privo di client HTTP.

## Corpus prodotto

Intervallo richiesto: 2008-04-01 / 2025-12-31.

- prima/ultima riga mensile: 2008-04-30 / 2025-12-31;
- campionamento: ultimo giorno di mercato con tutti i simboli disponibili;
- snapshot macro: 213;
- snapshot market completi: 4.536;
- serie macro: 6;
- simboli market: `SPY`, `ACWI`, `IEF`, `GLD`, `BIL`, `HYG`;
- forward return: 3.834, agli orizzonti 28/56/91 giorni;
- dimensione dataset: 1.982.402 byte;
- SHA-256 dataset: `3cac7d9b290b149f6529fea80e326ff83f8e44abaf907eb91fb4a368099a288a`;
- SHA-256 aggregato corpus: `f1718e2ef81bce252497e70ad083cf6661be15f308363934ece1d99288c3c7ca`.

Gli artefatti sono locali sotto `data/historical-real-2008-2025/`; `data/` e'
esclusa da Git per non versionare download voluminosi o dati di provider esterni.

## Politica point-in-time

- serie macro mensili revisionabili: initial release ALFRED;
- serie finanziarie giornaliere FRED: storia corrente, con date di disponibilita'
  pari alla data osservata; non sono vintage;
- market: adjusted close Yahoo, con fallback al close;
- per ogni snapshot sono selezionate solo osservazioni pubblicate entro l'as-of.

Il validatore Python verifica `observationDate`, `publicationDate` e
`vintageDate`/`availabilityDate`, oltre alla coerenza temporale e matematica dei
forward return.

## Deviazione HY_OAS documentata

FRED limita `BAMLH0A0HYM2` agli ultimi tre anni a partire da aprile 2026, quindi
non puo' coprire il periodo scelto. Il corpus storico usa `BAA10Y`, spread Baa
corporate meno Treasury decennale, disponibile giornalmente dal 1986. Il codice
funzionale resta `HY_OAS` per compatibilita' col modello, ma nome e sorgente nei
record dichiarano il proxy (`FRED:BAA10Y`).

Il proxy preserva un segnale di stress creditizio in percentuale, ma non e'
semanticamente identico all'high-yield option-adjusted spread. Questo limite deve
essere riportato in ogni confronto di modello.

Riferimenti ufficiali:

- https://fred.stlouisfed.org/docs/api/fred/series_observations.html
- https://alfred.stlouisfed.org/help/downloaddata
- https://fred.stlouisfed.org/series/BAA10Y
- https://fred.stlouisfed.org/series/SAHMREALTIME

## Data gate e walk-forward

Il dataset ha superato il validatore con `pointInTimeValidation: passed` e ha
generato 6 fold completi rolling 10/2/1. Il gate di disponibilita' dati e' quindi
chiuso. Non sono ancora stati eseguiti backtest, metriche composite o challenger.

## Verifiche

```text
dotnet build MacroRegime.slnx --no-restore
dotnet test MacroRegime.slnx --no-restore --no-build
python -m unittest discover -s tests -v
python -m compileall -q regime_eval tests
python -m regime_eval validate <dataset>
python -m regime_eval manifest <dataset> --output <manifest>
python -m regime_eval plan-walk-forward <dataset> --output <plan>
```

Esito:

- build: 0 warning, 0 errori;
- C#: 216 test superati, 0 falliti;
- Python: 7 test superati, 0 falliti;
- 213 righe validate e 6 fold completi;
- nessun `HttpClient`/`System.Net.Http` nei sorgenti Domain/Application/Web.

## Limiti residui e prossimo passo

- le serie finanziarie giornaliere non sono vintage;
- il calendario release non e' persistito nel corpus;
- Yahoo resta un provider non ufficiale e sostituibile;
- il manifest e' deterministico, ma manca un indice incrementale per corpus molto
  grandi;
- lo storico inizia nel 2008 e non copre gli stress 1973-74 o 2000-02.

Il prossimo passo e' eseguire e documentare la baseline rule-based sui sei fold,
definendo le prime metriche out-of-sample prima di introdurre un challenger.
