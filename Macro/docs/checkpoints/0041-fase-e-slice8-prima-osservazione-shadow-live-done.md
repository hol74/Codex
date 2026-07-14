# Macro Regime - Fase E - Slice 8: prima osservazione shadow-live

Data di esecuzione: 2026-07-13.

## Esito

E' stata congelata la prima previsione realmente `shadow-live` della baseline
v1.4. L'information cutoff e' il 2026-06-30, ultimo mese completo disponibile;
la previsione e' stata generata il 2026-07-13 alle 12:59:41 UTC, dopo il freeze
del modello e senza ground truth o forward return disponibili al comando.

Il risultato e' `Goldilocks`, con probabilita' recessiva 9,152222% e decisione
binaria non recessiva. Il ledger e' write-once e non e' stato prodotto alcun
`PredictionScore`.

## Incidente dati intercettato prima del freeze

La prima acquisizione candidata non e' stata manifestata come previsione. Un
controllo manuale delle date informative ha rilevato che SAHM era fermo a
settembre 2025, mentre le altre serie arrivavano a maggio/giugno 2026.

La causa era un singolo mese mancante nella storia initial-release di `UNRATE`:
la ricostruzione della media mobile SAHM richiede continuita' mensile e il buco
impediva di calcolare tutte le osservazioni successive. Il detector non emetteva
warning, quindi il difetto sarebbe rimasto silenzioso.

La correzione preserva la semantica del corpus di sviluppo:

- usa SAHM ricostruito dalle initial release `UNRATE` dove computabile;
- usa le initial release ufficiali `SAHMREALTIME` solo per colmare i buchi;
- mantiene la provenienza della serie provider nei file JSON;
- rifiuta automaticamente uno snapshot se una serie mensile e' piu' vecchia di
  tre mesi rispetto all'as-of;
- copre il fallback e la provenienza alternativa con test di regressione.

Il tentativo scartato resta sotto `data/shadow-live-2026/source/`, `dataset/` ed
`evaluation/` come diagnostica locale, ma non ha un ledger e non fa parte della
catena finale.

## Catena finale

Artefatti locali, esclusi da Git:

- corpus `data/shadow-live-2026/source-v2/`, aggregate SHA-256
  `4f8acef0b03790ea26f10a6c81bea65988cfc132deaa4903db8d57c1772f7f97`;
- dataset `data/shadow-live-2026/dataset-v2/historical-dataset-2026-06-30-2026-06-30.json`,
  SHA-256 `9b5229152657e9aa506352b635a33adf6fb830f96d8e3a1af1bce756191ed831`;
- evaluation `data/shadow-live-2026/evaluation-v2/baseline-evaluation-2026-06-30-2026-06-30-v1-4-candidate.json`,
  SHA-256 `339675be4576832bb1dcc971766e27e2ed4186efb69cea8d08db1f5d5b790b76`;
- ledger `data/shadow-live-2026/ledger/prediction-ledger-2026-06-30-v1-4.json`,
  SHA-256 `7fbcae3ca6ace977e4914edbc609003fcced936228b4a29cf9f0fdac20a520fa`.

Il ledger lega inoltre la configurazione preregistrata al dataset di sviluppo
`1a2db1c7540a2419757b37d01717de258548f9bcf301994dfcd5c83f47f17649`,
mentre registra separatamente il dataset live. Questa distinzione evita di
richiedere erroneamente che ogni osservazione futura abbia l'hash del corpus di
sviluppo.

## Verifiche

- validazione dataset: `pointInTimeValidation: passed`;
- una riga al 2026-06-30, zero date scartate e zero forward return;
- SAHM finale: osservazione 2026-05-01, pubblicazione 2026-06-05, valore 0,10;
- ledger: una previsione, `runMode: shadow-live`, `immutable: true`;
- nessun campo ground truth, actual, outcome o forward return nel ledger;
- test C#: 240 superati, inclusi fallback SAHM, provenienza provider e rifiuto
  automatico delle serie mensili obsolete;
- test Python: 16 superati; compileall superato.

## Interpretazione e prossimo passo

La prima osservazione dimostra che il protocollo intercetta un difetto reale
prima del freeze e produce una previsione auditabile. Non dimostra ancora
efficacia predittiva: e' un solo punto e non possiede una label maturata.

Il prossimo incremento deve aggiungere le nuove osservazioni mensili come
ledger separati e immutabili. Lo scoring resta vietato finche' la ground truth
versionata non e' disponibile; in parallelo resta da costruire la cronologia
separata degli stress non recessivi.
