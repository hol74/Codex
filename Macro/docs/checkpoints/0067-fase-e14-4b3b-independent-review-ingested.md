# Checkpoint 0067 - E14.4b3b independent review ingested

Data: 2026-07-14

## Obiettivo

Eseguire e ingerire una seconda review separata dall'autore dei dossier,
registrando senza forzature sia le accettazioni sia le revisioni richieste.

## Piano eseguito

1. affidare il bundle congelato a un agente reviewer distinto e senza il
   ragionamento di costruzione dei dossier;
2. aprire le fonti ufficiali, valutare claim, confini e controevidenza;
3. produrre una ricevuta hash-bound per ciascuno dei 12 dossier;
4. correggere per versioning il difetto di rappresentazione dello schema v1;
5. validare schema, indipendenza, hash e decisioni `accept` strette;
6. congelare queue e audit senza scrivere label o candidati.

## Difetto schema v1 e correzione v2

La prima ingestione ha rifiutato correttamente una ricevuta `needs-revision`
con `sourceLocatorsOpened=false`: lo schema v1 imponeva `true` a ogni esito e
non poteva quindi rappresentare una revisione richiesta proprio per un locator
non accessibile. Nessuna ricevuta e' stata resa artificialmente positiva.

Lo schema v2:

- consente un locator non aperto per `reject` o `needs-revision`;
- continua a richiedere per `accept` fonti aperte, claim confermato e confini
  confermati;
- mantiene obbligatori controevidenza, esclusione dei modelli e indipendenza.

Il reviewer ha risottomesso le stesse decisioni e checklist cambiando soltanto
`schemaVersion` da 1 a 2.

## Esito della review

- `accept`: 8;
- `needs-revision`: 4;
- `reject`: 0;
- ricevute valide: 12/12;
- reviewer distinti dall'autore: 1;
- stato: `DOSSIER_REVISIONS_REQUIRED`.

Revisioni richieste:

- Continental Illinois: onset maggio supportato, ma luglio non e' dimostrato
  come fine; prelievi e implementazione del piano proseguono oltre;
- Messico broad-market: shock dicembre supportato, end boundary marzo 1995 no;
- Messico cross-border: trasmissione supportata, end boundary marzo 1995 no;
- Messico banking hard-negative: resilienza supportata, ma marzo non provato e
  PDF FDIC non direttamente renderizzabile.

## Limite dell'indipendenza

La review e' stata svolta da un'istanza agente distinta che non ha costruito i
dossier. Questo soddisfa la separazione autore-reviewer implementata, ma non
equivale a validazione istituzionale o peer review umana; il limite resta
esplicito nella governance.

## Identita' degli artefatti

- review schema v2 SHA-256:
  `77310369e3ba33a6a5dbde84ce6cc445a6a87c7e9e03ba3842718a684822dd58`;
- ingestion contract SHA-256:
  `4ef595eeb03fd33c50bb825799eafc6afa8bb54c942f8cfdaa7e82f4b4fd8859`;
- reviewed queue v3 SHA-256:
  `ad9878cc9a33a2d337a17726f9f5243cfafa0284fff6579c91c094eb3966fe2d`;
- review ingestion audit SHA-256:
  `300280d64e6cb9f40240b5adde9f307c0d5acb079408e54756de7b0883b4fed5`.

## Verifiche

- test mirati ingestion review: 2/2 superati;
- suite Python completa: 69/69 test superati;
- suite .NET completa: 240/240 test superati;
- compilazione bytecode Python: superata;
- output deterministico e write-once: verificato dai test;
- un esito `accept` con fonte non aperta viene rifiutato: verificato dai test;
- `git diff --check`: superato, salvo i soli avvisi attesi sulla futura
  normalizzazione LF/CRLF dei file gia' tracciati.

Il codice di uscita non-zero dell'ingestione reale e' intenzionale: segnala
che il gate non puo' aprirsi finche' restano dossier `needs-revision`, non un
errore tecnico dell'esecuzione.

## Prossimo passo

E14.4b4 deve produrre nuovi dossier soltanto per i quattro
`needs-revision`, mantenendo immutati gli otto accettati. I dossier aggiornati
avranno nuovi hash e saranno gli unici da sottoporre nuovamente al reviewer.
