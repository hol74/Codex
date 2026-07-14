# Checkpoint 0070 - E14.4d taxonomy v4 versioned

Data: 2026-07-14

## Obiettivo

Materializzare la proposta label-foundation E14.4c in una tassonomia v4
immutabile e mechanism-aware, preservando la v3 e mantenendo separata la
versione delle label dall'autorizzazione a generare candidati.

## Piano eseguito

1. congelare schema e contratto di materializzazione con gli hash esatti di
   tassonomia v3, proposta, audit E14.4c e contratti informativi;
2. mantenere una voce per dossier e meccanismo, senza fondere intervalli con
   confini temporali differenti;
3. introdurre una identita' di evento indipendente esplicita;
4. ricontare la copertura usando l'evento, non il numero di dossier;
5. scrivere una nuova v4 write-once e un audit separato;
6. lasciare candidati, outer OOS e promozione chiusi.

## Astrazione introdotta

Ogni nuovo episodio della foundation ha granularita' monomeccanismo e porta
`independentEventId = hypothesisId`. Gli episodi ereditati usano il proprio
`id`. Questo risolve due problemi distinti:

- i confini specifici del meccanismo non vengono allargati dalla fusione con
  altri dossier dello stesso evento;
- Brexit broad, funding e cross-border conta come un solo evento indipendente,
  cosi' come Russia/LTCM sui tre meccanismi positivi.

L'aggregato mensile resta una vista. La label primaria e' la coppia
`(mese, meccanismo)` e gli stati misti cross-meccanismo restano validi.

## Correzione durante la validazione

La prima materializzazione diagnostica ricavava `coverageTo` dall'ultimo
episodio etichettato e avrebbe ristretto la copertura ereditata a luglio 2023.
Prima del consolidamento il materializzatore e' stato corretto: v4 puo'
estendere il limite iniziale, ma non puo' ridurre il limite finale di v3. Un
test di regressione congela ora `coverageTo = 2025-12-31`.

## Esito reale

- ground truth id: `us-financial-stress-mechanism-aware-v4`;
- copertura: `1984-05-01`--`2025-12-31`;
- episodi ereditati: 8;
- nuove voci positive monomeccanismo: 8;
- nuove voci hard-negative monomeccanismo: 4;
- eventi positivi indipendenti: 11;
- eventi hard-negative indipendenti: 2;
- copertura positiva per broad/funding/banking/cross-border: 7/3/3/5;
- copertura hard-negative per meccanismo: 1/1/1/1;
- conflitti stesso mese/meccanismo: 0;
- candidati generati: 0.

Stato: `TAXONOMY_V4_VERSIONED_MORE_HARD_NEGATIVES_REQUIRED`.

## Identita' degli artefatti

- schema tassonomia v4 SHA-256:
  `1a7f4bb3e22e2bf287d4fe6773727e623fcd0345306d41328682c510fd663df5`;
- contratto materializzazione SHA-256:
  `84583adbbc81f8dfb2695ab3f08324d16b9997f7d879a1ea68f6aa7161840dfc`;
- tassonomia v4 SHA-256:
  `d7f11a0ecc2bf2856d89b2aeb897e87e34d37e745bb9fecc0d16ad6558fa40cc`;
- audit materializzazione SHA-256:
  `c8c5bfb8a2222a7fa45f00b9cd938c31faf82ecbafb0db3381ab0e30696cc3aa`;
- tassonomia v3 preservata SHA-256:
  `5c74072b70f6bc5c840b49e3937ffc0506db3a808adfd29138804e840fbf68b9`.

## Garanzie di governance

- la v3 non e' stata modificata;
- tutti gli input sono hash-bound;
- gli hash dei dossier restano nella `foundationEvidence`;
- nessun unlabeled e' diventato hard-negative;
- copertura e conflitti coincidono con la proposta E14.4c;
- dataset e feature outer OOS non sono stati letti;
- generazione candidati e promozione restano vietate.

## Verifiche

- test mirati taxonomy v4: 2/2 superati;
- suite Python completa: 79/79 test superati;
- compilazione bytecode Python: superata;
- suite .NET completa: 240/240 test superati;
- determinismo e write-once: verificati;
- contratto che apre i candidati: rifiutato dai test;
- restrizione accidentale della copertura finale: protetta da test.

## Prossimo passo

E14.4e deve curare ulteriori hard negative affermativi e indipendenti, fino ad
almeno 6 eventi totali e 2 per ciascun meccanismo. I nuovi dossier dovranno
seguire lo stesso ciclo di review hash-bound; soltanto gli accept potranno
entrare in una versione successiva e riaprire il coverage audit.
