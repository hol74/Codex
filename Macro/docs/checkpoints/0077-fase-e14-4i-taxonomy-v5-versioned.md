# Checkpoint 0077 - E14.4i taxonomy v5 versioned

Data: 2026-07-15

## Obiettivo

Materializzare i quattro hard negative accettati da E14.4h in una nuova
tassonomia immutabile, preservando integralmente la v4 e mantenendo separata
l'autorizzazione alla generazione dei candidati.

## Contratto e invarianti

Il contratto `e14-taxonomy-v5-materialization-contract-v1.json` congela gli
hash di tassonomia v4, coverage gate, queue v11, schemi e contratti label e
meccanismo. La materializzazione e' fail-closed e write-once.

Sono obbligatori:

- conservazione strutturale di tutti gli episodi e delle 12 evidenze v4;
- un nuovo episodio per ciascuno dei quattro dossier accettati;
- `hypothesisId` come identita' dell'evento indipendente;
- stati coerenti sulla chiave `(mese, meccanismo)`;
- copertura identica a quella accettata da E14.4h;
- candidate generation, outer OOS e promozione disabilitati.

## Materializzazione reale

E' stata creata `ground-truth/us-financial-stress-v5.json`, derivata da
`us-financial-stress-mechanism-aware-v4`. La v4 non e' stata modificata e
mantiene SHA-256
`d7f11a0ecc2bf2856d89b2aeb897e87e34d37e745bb9fecc0d16ad6558fa40cc`.

Inventario v5:

| Voce | Quantita' |
| --- | ---: |
| episodi positivi indipendenti | 11 |
| hard negative indipendenti | 6 |
| entry hard-negative materializzate | 8 |
| evidenze di fondazione | 16 |
| hard negative per meccanismo | 2 |
| conflitti `(mese, meccanismo)` | 0 |

La tassonomia v5 ha SHA-256
`d141416d08b68e932bc6cd2a25b9cd0eab06d159b8904907b7fff29d8c637d50`.

## Esito e autorizzazioni

L'audit reale termina con
`TAXONOMY_V5_VERSIONED_CANDIDATE_READINESS_REQUIRED` e SHA-256
`95322cb3b0952c85dae1b9f8edbb90193a2caaf44271bdc4cbb026addea42391`.

Sono veri `taxonomyV5Ready`, sufficienza positiva, sufficienza hard-negative e
autorizzazione al solo candidate-readiness gate. Restano falsi:

- candidate generation;
- lettura outer OOS;
- promozione.

## Implementazione e verifiche

- schema: `models/e14-financial-stress-taxonomy-v5-schema.json`;
- contratto: `models/e14-taxonomy-v5-materialization-contract-v1.json`;
- modulo: `regime_eval/e14_taxonomy_v5.py`;
- comando: `e14-materialize-taxonomy-v5`;
- test mirati: 2/2;
- suite Python completa: 99/99;
- compilazione bytecode: superata;
- test .NET: superati;
- `git diff --check`: superato.

## Prossimo passo

E14.4j deve essere un gate separato di candidate readiness. Dovra' verificare
hash, copertura, assenza di conflitti e compatibilita' del protocollo di
generazione con la tassonomia v5. Solo tale gate potra' autorizzare la
generazione; outer OOS e promozione resteranno decisioni successive.
