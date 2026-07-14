# Macro Regime - Fase E9: Shadow Operations, incremento 1

Data di chiusura: 2026-07-13.

## Esito

Il protocollo E8 e' stato trasformato in un primo contratto operativo
eseguibile. Prima di un nuovo ledger `shadow-live` e' ora obbligatorio un
`ShadowPreflight` immutabile; il ciclo e' idempotente e l'elenco dei ledger e'
una vista derivata ricostruibile.

Questo incremento non modifica la baseline v1.4, non esegue scoring e non
orchestra ancora i processi C# di acquisizione e costruzione degli input.

## Contratti introdotti

`ShadowPreflight` verifica e congela:

- mese informativo chiuso rispetto al timestamp di esecuzione;
- dataset point-in-time legato all'evaluation tramite SHA-256;
- assenza di forward return;
- presenza delle nove serie macro richieste;
- lag macro compreso fra zero e tre mesi;
- corrispondenza fra model config ed evaluation;
- fingerprint deterministici delle sorgenti C# responsabili di
  population/build/evaluation e del research lab Python.

Il ledger `shadow-live` registra l'hash del preflight. `shadow-cycle`, se trova
gia' il path di destinazione, restituisce l'artefatto solo quando date e quattro
hash di input coincidono; ogni conflitto viene rifiutato. Il timestamp di una
retry non riscrive l'evidenza originale.

`ShadowIndex` scansiona i ledger immutabili, richiede una sola previsione per
file e una sola entry per cutoff, ordina deterministicamente le date e dichiara
esplicitamente `authoritative: false`.

## Comandi

- `shadow-preflight`: prepara l'evidenza write-once;
- `shadow-cycle`: crea o recupera idempotentemente il ledger e aggiorna la
  vista derivata;
- `shadow-index`: ricostruisce la sola vista dai ledger presenti.

`shadow-predict --run-mode shadow-live` richiede anch'esso `--preflight`; il
dry-run E8 resta disponibile senza preflight.

## Audit retrospettivo del cutoff 2026-06-30

Il nuovo gate e' stato applicato agli input reali di giugno dopo la creazione
del primo ledger. Tutte le nove serie passano: cinque hanno lag zero e quattro
lag un mese. Sono stati prodotti localmente:

- `data/shadow-live-2026/operations-audit/shadow-preflight-2026-06-30-retrospective.json`,
  SHA-256 `1f3ef96a8dbd9aed799bc62ffefc4b7bc0f31ddd40f8780bd41eeb6365d540dc`;
- `data/shadow-live-2026/ledger/shadow-index.json`, SHA-256
  `22b426d86695d60b7176044c3f442dc044dfdda508745412e4e271960b6862f3`.

Il preflight e' dichiaratamente retrospettivo e non viene collegato al ledger
del 2026-06-30. Il ledger resta invariato con SHA-256
`7fbcae3ca6ace977e4914edbc609003fcced936228b4a29cf9f0fdac20a520fa`.
Questa scelta evita di riscrivere o reinterpretare ex-post l'evidenza live.

## Verifiche

- 22 test Python superati;
- coperti preflight positivo, mese aperto, serie obsoleta, retry identica,
  conflitto di input e indice deterministico;
- 240 test C# superati;
- `compileall` superato;
- build .NET senza warning o errori;
- ledger reale di giugno verificato byte-per-byte invariato.

## Limiti e prossimo incremento

E9 non e' ancora un orchestratore end-to-end: population, dataset build ed
evaluation C# devono essere avviati separatamente. Il prossimo incremento deve
aggiungere l'orchestrazione esplicita, una modalita' `prepare-only` quando non
esiste un nuovo mese chiuso, un layout mensile stabile e la gestione dei
fallimenti parziali. Il primo vero uso prospettico del preflight avverra' sul
cutoff successivo eleggibile; fino ad allora non va creato un secondo ledger di
giugno.
