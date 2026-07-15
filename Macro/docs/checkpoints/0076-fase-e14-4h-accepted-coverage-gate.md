# Checkpoint 0076 - E14.4h accepted hard-negative coverage gate

Data: 2026-07-15

## Obiettivo

Verificare formalmente che i dossier hard-negative accettati raggiungano le
soglie informative congelate, senza mutare la tassonomia v4 e senza aprire la
generazione dei candidati.

## Input congelati

- queue v11 con 16/16 dossier accettati;
- targeted ingestion audit v2;
- tassonomia `us-financial-stress-mechanism-aware-v4`;
- schema dossier e contratti label/meccanismo/espansione;
- sei directory dossier trattate come un unico content-addressed store.

Ogni manifest deve risolversi contro esattamente un file con hash e dimensione
corretti. La duplicazione dello stesso path o l'assenza dell'hash atteso e'
fail-closed.

## Separazione tra fondazione ed espansione

I 12 `foundationEvidence` della tassonomia v4 devono mantenere gli hash della
queue. I quattro manifest accettati non presenti nella fondazione costituiscono
l'espansione:

| Evento | Meccanismo | Intervallo |
| --- | --- | --- |
| Stock market break 1987 | banking-credit | ottobre 1987 |
| Flash Crash 2010 | cross-border-growth | maggio 2010 |
| Risk repricing 2018Q4 | funding-liquidity | ottobre-dicembre 2018 |
| Regional-bank stress 2023 | broad-market-repricing | marzo-maggio 2023 |

Gli eventi sono contati tramite `hypothesisId`; dossier multipli dello stesso
evento non possono gonfiare la copertura.

## Risultato della copertura

| Meccanismo | Positivi | Hard negative | Soglie superate |
| --- | ---: | ---: | --- |
| broad-market-repricing | 7 | 2 | si |
| funding-liquidity | 3 | 2 | si |
| banking-credit | 3 | 2 | si |
| cross-border-growth | 5 | 2 | si |

- episodi positivi indipendenti: 11;
- episodi hard-negative indipendenti: 6;
- conflitti `(mese, meccanismo)`: 0;
- coverage complessiva sufficiente: si.

Stato: `ACCEPTED_HARD_NEGATIVE_COVERAGE_READY`.

## Autorizzazioni

Il gate autorizza soltanto E14.4i a produrre una nuova proposta/versione
immutabile della tassonomia. Restano false:

- mutazione in-place della v4;
- candidate generation;
- lettura outer OOS;
- promozione.

Il protocollo registra zero label scritte, zero dataset row lette e nessun
candidato generato.

## Artefatti e verifiche

- contratto: `models/e14-hard-negative-coverage-gate-contract-v1.json`;
- modulo: `regime_eval/e14_hard_negative_coverage_gate.py`;
- audit: `e14-hard-negative-coverage-gate-audit-v1.json`;
- audit SHA-256:
  `a0caa0643d1a46c57bc45e7ac08e547789f42642a055214c445063344ba905c9`;
- test mirati: 3/3;
- suite Python completa: 97/97;
- compilazione bytecode: superata;
- test .NET: superati;
- `git diff --check`: superato.

## Prossimo passo

E14.4i deve materializzare i quattro nuovi hard negative in una tassonomia v5
separata, conservando provenienza, hash e stati misti. Un gate successivo dovra'
decidere se la nuova tassonomia e' sufficiente ad aprire la generazione dei
candidati; E14.4h non concede tale autorizzazione.
