# Checkpoint 0080 - E14.4l four-detector protocol ready

Data: 2026-07-15

## Obiettivo

Sostituire il protocollo E13 non compatibile con una grammatica research
finita, separata per i quattro meccanismi e legata alla tassonomia v5 e alla
feature foundation E14.4k.

## Fondazione congelata

Il protocollo lega esplicitamente:

- tassonomia v5 SHA-256
  `d141416d08b68e932bc6cd2a25b9cd0eab06d159b8904907b7fff29d8c637d50`;
- feature foundation SHA-256
  `bca70e5f5ca224fe23e4b29970dc651a2b708c047e3364a3575a235ae80a64b9`;
- foundation lock SHA-256
  `34448522085f5949e341cc62cda3b8088a47eac9a7f01ea9c5f0a7220d9a61dc`.

Il protocollo stesso ha SHA-256
`21a36f0f6df344215830135108edfe890d2553b4879aa3c5d861181862592047`.

## Grammatica finita

| Meccanismo | Profili | Candidati |
| --- | ---: | ---: |
| broad-market-repricing | 4 | 16 |
| funding-liquidity | 1 | 4 |
| banking-credit | 4 | 16 |
| cross-border-growth | 1 | 4 |
| totale | 10 | 40 |

Ogni profilo combina due opzioni di persistenza in ingresso e due di recovery.
Le soglie `[0.80, 0.90, 0.95]` non moltiplicano il manifest: sono selezionate
esclusivamente nel train inner di ciascun fold leave-one-episode-out.

## Controlli ereditati e sostituzioni

Sono riusati da E13:

- enumerazione deterministica;
- feature causali e transform train-only;
- missingness esplicita;
- selezione leave-one-episode-out inner;
- divieto di outer OOS.

Sono sostituiti:

- lock E12 con il lock E14.4k;
- due task aggregati con quattro grammatiche indipendenti;
- metriche aggregate con metriche episodio/mese per meccanismo.

## Evaluation e confini

Il protocollo richiede episode hit/recall, worst-episode recall, onset delay,
recovery lag, hard-negative alert rate e conteggio separato degli alert nei
mesi unlabeled. I mesi unlabeled non diventano negativi impliciti.

I limiti vintage della foundation sono accettati soltanto per generazione e
sviluppo research. Una sensitivity analysis sulle revisioni resta obbligatoria
prima di qualunque promozione operativa.

## Esito

Stato: `RESEARCH_CANDIDATE_GENERATION_READY_OUTER_OOS_CLOSED`.

- protocollo congelato: si;
- generazione research del solo manifest: autorizzata;
- fitting ed evaluation: non autorizzati;
- composizione cross-meccanismo: non autorizzata;
- strict vintage ready: no;
- outer OOS e promozione: non autorizzati.

L'audit ha SHA-256
`a20f0f6861506ca863d33d53767da2d6bd1b4eeb299279c93e3650e408de35fe`.

## Implementazione e verifiche

- schema: `models/e14-four-detector-candidate-protocol-schema-v1.json`;
- protocollo: `models/e14-four-detector-candidate-generation-protocol-v1.json`;
- readiness contract: `models/e14-four-detector-protocol-readiness-contract-v1.json`;
- modulo: `regime_eval/e14_candidate_protocol.py`;
- comando: `e14-freeze-candidate-protocol`;
- test mirati: 3/3;
- suite Python completa: 108/108;
- compilazione bytecode: superata;
- test .NET: superati;
- `git diff --check`: superato.

## Prossimo passo

E14.5 deve generare deterministicamente un manifest write-once di 40 candidati
legati al protocollo. Non deve leggere label o dataset, applicare transform,
stimare soglie, eseguire fitting/evaluation, comporre detector o aprire outer
OOS. Queste operazioni richiederanno gate successivi separati.
