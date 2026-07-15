# Checkpoint 0074 - E14.4g expansion review ingested

Data: 2026-07-15

## Obiettivo

Eseguire una review indipendente dei quattro hard negative dell'espansione e
ingerire le ricevute senza riaprire i 12 dossier gia' accettati.

## Separazione dei ruoli

- autore pack/dossier: `codex-primary-source-review-2026-07-15`;
- reviewer: `codex-independent-evidence-reviewer-2026-07-15`;
- processo di ingestione: valida schema, indipendenza e hash, ma non produce o
  modifica le decisioni.

Il reviewer ha aperto tutti i 12 locator di evidence e counterevidence e non
ha consultato output di modello o risultati di coverage.

## Decisioni

| Dossier | Meccanismo | Decisione | Motivazione sintetica |
| --- | --- | --- | --- |
| Stock market break 1987 | banking-credit | accept | Evidenza sufficiente di assenza di una crisi bancaria nello stesso mese |
| Risk repricing 2018Q4 | funding-liquidity | accept | Funding di breve stabile nonostante il repricing broad-market |
| Regional bank stress 2023 | broad-market-repricing | needs-revision | Locator IMF `text.ashx` non direttamente accessibile |
| Repo stress 2019 | cross-border-growth | needs-revision | Spillover repo limitati non provano lo stato della crescita reale cross-border |

Non ci sono rigetti. I due `needs-revision` non negano necessariamente il
contrasto, ma indicano che il dossier corrente non soddisfa il livello di
evidenza necessario per l'accettazione.

## Esito ingestione

- ricevute attese e ricevute: 4/4;
- reviewer indipendenti: 1;
- accept nuovi: 2;
- needs-revision: 2;
- reject: 0;
- accept precedenti preservati: 12/12;
- queue v7 scritta: si;
- coverage gate E14.4h autorizzato: no;
- tassonomia o candidati autorizzati: no.

Stato: `EXPANSION_DOSSIER_REVISIONS_REQUIRED`.

## Impatto sulla copertura

La tassonomia v4 resta invariata a 2 hard negative indipendenti. Considerando
anche i due nuovi hash accettati, l'evidenza disponibile per un futuro gate
salirebbe a 4 eventi indipendenti. La distribuzione sarebbe:

- broad-market-repricing: 1;
- funding-liquidity: 2;
- banking-credit: 2;
- cross-border-growth: 1.

Le soglie 6 totali e 2 per meccanismo non sono quindi raggiunte: i due dossier
non accettati coincidono con i deficit broad-market e cross-border.

## Identita' degli artefatti

- queue v7 SHA-256:
  `0085272a6541d7115b130d7fa156ee3fe53ceb3a81541145fbd56c6aac2238bf`;
- ingestion audit v2 SHA-256:
  `8db6e1873790ef5e0a731a99a039a1ad6a4842e710ea0d640c70395b8965af27`;
- receipt 2023 broad-market SHA-256:
  `c376f634d0329b3becf2f55b27e4c11224033eb8d4aeb56be9057610ac159a6d`;
- receipt repo 2019 cross-border SHA-256:
  `76354a8ae79ea0316c16235b49df8fc92d4ab5ead91953c7c47fcc845463a024`;
- receipt 2018Q4 funding SHA-256:
  `5f64a97d2342ce63d0bbbcbff11938fe6fe78bc30250ce0c98c040af7135c4de`;
- receipt 1987 banking SHA-256:
  `c27fe57520ce3de899632d45f26094f5aea621d433d99c63ce6f45e2037f7e4a`.

## Garanzie verificate

- quattro hash unici e legati all'handoff;
- schema v2 e rationale conformi;
- reviewer diverso dall'autore;
- requisiti strict-accept rispettati per i due accept;
- ricevute non modificate dall'ingestione;
- 12 manifest precedenti preservati byte-identici;
- queue v7 scritta solo dopo completezza 4/4;
- nessuna mutazione di tassonomia o apertura candidati.

## Verifiche

- test mirati ingestione E14.4g: 3/3 superati;
- suite Python completa: 87/87 test superati;
- compilazione bytecode Python: superata;
- retry CLI reale con quattro ricevute: completato;
- `git diff --check`: superato.

## Prossimo passo

E14.4g2 deve revisionare soltanto regional-bank 2023 broad-market e repo 2019
cross-border. Il primo richiede un locator istituzionale direttamente
accessibile; il secondo richiede una fonte che misuri il meccanismo di crescita
transfrontaliera oppure un nuovo hard negative cross-border piu' difendibile.
I 14 dossier accettati devono restare byte-identici e fuori dalla nuova review.
