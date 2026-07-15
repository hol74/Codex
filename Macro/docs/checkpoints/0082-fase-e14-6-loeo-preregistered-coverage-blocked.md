# Checkpoint 0082 - E14.6 LOEO preregistered, structural coverage blocked

Data: 2026-07-15

## Obiettivo

Preregistrare il protocollo leave-one-episode-out inner per i 40 candidati
E14.5 e verificare, prima del fitting, che ogni profilo disponga di episodi
positivi e hard negative osservabili in quantita' sufficiente.

## Protocollo congelato

- unita': evento indipendente entro il singolo meccanismo;
- fold: un episodio positivo held-out, tutti gli altri positivi osservabili
  dello stesso meccanismo nel train;
- controlli: soltanto hard negative documentati dello stesso meccanismo;
- mesi unlabeled: riportati, mai trattati come negativi;
- quantili: `[0.80, 0.90, 0.95]`, calcolati e selezionati solo sui train;
- feature: causali, parametri train-only, missingness esplicita;
- storia minima: 60 mesi;
- nessuno splicing o carry oltre il confine metodologico della serie;
- outer OOS: chiuso.

La soglia minima e' tre eventi positivi osservabili, quindi almeno due restano
nel train di ogni fold, e due hard negative indipendenti osservabili.

## Esito strutturale

| Meccanismo | Label positive | Hard negative | Candidati eleggibili | Candidati bloccati |
| --- | ---: | ---: | ---: | ---: |
| banking-credit | 3 | 2 | 0 | 16 |
| broad-market-repricing | 7 | 2 | 16 | 0 |
| cross-border-growth | 5 | 2 | 0 | 4 |
| funding-liquidity | 3 | 2 | 0 | 4 |
| totale | 18 | 8 | 16 | 24 |

La copertura nominale delle label non equivale alla copertura osservabile:

- banking perde gli eventi piu' antichi dopo l'applicazione della storia
  minima e dispone anche di un solo hard negative osservabile;
- DTWEXB parte nel 1995 e, dopo 60 mesi di storia, lascia solo due positivi
  cross-border osservabili;
- TEDRATE termina nel gennaio 2022, quindi il positivo funding del 2023 non e'
  osservabile e restano soltanto due positivi;
- broad-market conserva sei positivi osservabili e due hard negative.

## Decisione

Stato: `INNER_LOEO_PREREGISTERED_STRUCTURAL_COVERAGE_BLOCKED`.

- preregistrazione congelata: si;
- fitting globale: non autorizzato;
- fitting parziale broad-only: non autorizzato;
- evaluation e ranking: non autorizzati;
- composizione, outer OOS e promozione: non autorizzati.

Bloccare anche il sottoinsieme broad evita di trasformare un obiettivo a
quattro detector in un esperimento diverso senza una decisione esplicita.

## Artefatti

- schema: `models/e14-four-detector-loeo-preregistration-schema-v1.json`;
- protocollo: `models/e14-four-detector-loeo-preregistration-v1.json`;
- contratto: `models/e14-four-detector-loeo-readiness-contract-v1.json`;
- modulo: `regime_eval/e14_loeo_preregistration.py`;
- comando: `e14-preregister-loeo`;
- audit: `e14-four-detector-loeo-preregistration-audit-v1.json`;
- test: `tests/test_e14_loeo_preregistration.py`.

Audit SHA-256:
`8a222c7fbfbadcbd08de9992df494d6e9cb1b0bdb82a8aa9a31df53afcf29474`.

## Verifiche

- test mirati E14.6: 3/3;
- suite Python completa: 114/114;
- compilazione bytecode: superata;
- test .NET: superati;
- `git diff --check`: superato, con soli avvisi LF/CRLF gia' noti.

## Prossimo passo

E14.6a deve confrontare tre opzioni, senza tuning retrospettivo:

1. aggiungere serie storiche point-in-time semanticamente coerenti;
2. motivare e preregistrare una diversa storia minima solo se supportata dalla
   letteratura e dalla stabilita' del transform;
3. ritirare i profili o i meccanismi che restano informativamente non
   identificabili.

Foundation e protocollo dovranno ricevere nuove versioni; E14.6 andra'
rieseguito prima di qualsiasi fitting.
