# Checkpoint 0071 - E14.4e hard-negative expansion curated

Data: 2026-07-15

## Obiettivo

Colmare il deficit informativo della tassonomia v4 curando quattro hard
negative affermativi e indipendenti, senza confondere la copertura potenziale
con evidenza accettata e senza riaprire candidati o outer OOS.

## Piano eseguito

1. ricontare la copertura v4 per evento indipendente e meccanismo;
2. scegliere quattro eventi distinti senza stati opposti sulla stessa coppia
   `(mese, meccanismo)`;
3. verificare fonti istituzionali favorevoli e controevidenza;
4. congelare pack e contratto con gli hash di tutti gli input;
5. generare quattro dossier write-once e una queue v6 che preserva i 12
   manifest gia' accettati;
6. misurare separatamente copertura corrente e potenziale;
7. mantenere chiuse tassonomia, candidate generation, outer OOS e promozione.

## Modellizzazione dei contrasti

| Evento indipendente | Mese | Hard negative per | Stato distinto preservato |
| --- | --- | --- | --- |
| Stock market break 1987 | 1987-10 | banking-credit | broad-market positivo |
| Risk repricing 2018Q4 | 2018-12 | funding-liquidity | broad-market positivo |
| Repo stress 2019 | 2019-09 | cross-border-growth | funding positivo |
| Regional bank stress 2023 | 2023-03 | broad-market-repricing | banking/funding positivi |

Lo stesso evento puo' mostrare stress in un meccanismo e comportamento
ordinato in un altro. Questo non e' un errore di label: il contratto vieta
stati opposti soltanto sulla stessa coppia `(mese, meccanismo)`.

## Evidenza e limiti

Ogni dossier contiene prova affermativa del comportamento ordinato per il
meccanismo dichiarato, almeno due gruppi di provider, una osservazione
quantitativa o narrativa istituzionale e controevidenza. Le fonti principali
includono Federal Reserve e GAO per il 1987, Federal Reserve/FSOC e BIS per il
2018Q4, Bank of England/IMF e Federal Reserve per il repo 2019, Federal
Reserve/IMF e GAO per il 2023.

La stabilita' puo' essere stata assistita da interventi di policy e le
conclusioni restano sensibili ai confini temporali. Per questo i dossier sono
`reviewed`, non `accepted`, e devono essere riesaminati da un soggetto diverso
dall'autore.

## Esito reale

- dossier nuovi: 4;
- eventi indipendenti nuovi: 4;
- manifest accettati precedenti preservati: 12/12;
- voci totali nella queue v6: 16;
- conflitti stesso mese/meccanismo: 0;
- copertura hard-negative corrente: 2 eventi, 1 per meccanismo;
- copertura potenziale se tutti accettati: 6 eventi, 2 per meccanismo;
- ricevute indipendenti nuove: 0;
- label accettate o tassonomie mutate: 0;
- candidati generati: 0.

Stato: `INDEPENDENT_REVIEW_REQUIRED`.

## Identita' degli artefatti

- expansion pack SHA-256:
  `83a87e96afd4a9e298f3e3e1baa571f6594b635e810e0203590b4158c398cbe4`;
- expansion contract SHA-256:
  `c917db0b7ee9a2a32095b6b6c06ca1ff08ede44e12c52f66515ccf7b1a57d44d`;
- review queue v6 SHA-256:
  `c4eb4b7763db757e1f5290238efcb4f0c97ba3221063e763d8730f4dc1f59c02`;
- curation audit SHA-256:
  `cda82f4dfe613db2f93de5bae8c7a96ace9da3ef5cc4df9ccca61d2681a67e47`.

## Garanzie di governance

- tutti gli input sono hash-bound;
- i 12 manifest accettati nella queue v5 sono copiati senza variazioni;
- i quattro nuovi dossier non possono auto-accettarsi;
- un output gia' esistente viene rifiutato;
- nessun dataset, feature outer o label outer e' stato letto;
- la tassonomia v4 resta byte-identica;
- raggiungere la soglia potenziale non autorizza candidati.

## Verifiche

- test mirati E14.4e: 2/2 superati;
- suite Python completa: 81/81 test superati;
- compilazione bytecode Python: superata;
- suite .NET completa Debug/net10.0: 240/240 test superati;
- test rifiuto di un contratto che apre candidate generation: superato;
- determinismo e write-once: verificati;
- esecuzione reale: completata con exit code 0 per il solo gate potenziale.

## Prossimo passo

E14.4f deve costruire un handoff immutabile limitato ai quattro nuovi dossier.
La review e l'ingestione restano un incremento successivo: soltanto gli
`accept` potranno alimentare un nuovo coverage gate e una successiva versione
della tassonomia.
