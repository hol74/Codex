# Checkpoint 0078 - E14.4j candidate readiness blocked

Data: 2026-07-15

## Obiettivo

Determinare con un gate separato se la tassonomia v5, la feature foundation e
il protocollo di generazione consentono di aprire i candidati senza leakage e
senza coinvolgere outer OOS o promozione.

## Input congelati

Il contratto `e14-candidate-readiness-gate-contract-v1.json` lega tramite hash:

- tassonomia v5 e relativo audit di materializzazione;
- contratto dei quattro detector e catalogo storico delle fonti;
- protocollo candidato E13 esistente;
- lock della foundation E12 usato dal protocollo E13.

Il gate e' read-only, write-once e fail-closed. Non accetta modifiche alla
tassonomia e non usa righe del dataset.

## Controlli superati

- hash e provenienza della tassonomia v5 coerenti;
- 11 eventi positivi e 6 hard negative indipendenti;
- soglie di copertura raggiunte, inclusi 2 hard negative per meccanismo;
- zero conflitti `(mese, meccanismo)`;
- quattro detector, uno per ciascun meccanismo;
- fonti proposte presenti nel catalogo;
- policy E13 inner-only, causali, train-only e missingness-explicit riusabili;
- outer OOS chiuso.

## Blocker rilevati

| Codice | Evidenza |
| --- | --- |
| `DETECTOR_FEATURES_NOT_POPULATED` | 0/6 feature risultano `populated-manifested` |
| `FEATURE_FOUNDATION_NOT_MATERIALIZED` | non esiste ancora un lock point-in-time E14 |
| `GENERATION_PROTOCOL_FOUNDATION_MISMATCH` | E13 punta al lock E12, non alla tassonomia v5 |
| `GENERATION_PROTOCOL_TASK_GRAMMAR_MISMATCH` | E13 ha due task; E14 richiede quattro detector indipendenti |

L'esito e' quindi
`CANDIDATE_READINESS_BLOCKED_FOUNDATION_AND_PROTOCOL`.

## Autorizzazioni

Restano falsi:

- candidate generation;
- accesso outer OOS;
- promozione;
- mutazione della tassonomia.

Il processo registra zero righe lette, zero candidati generati e nessuna
decisione di promozione. L'esito bloccato e' il comportamento corretto, non un
fallimento tecnico.

## Artefatti e verifiche

- contratto: `models/e14-candidate-readiness-gate-contract-v1.json`;
- modulo: `regime_eval/e14_candidate_readiness.py`;
- comando: `e14-candidate-readiness-gate`;
- audit: `e14-candidate-readiness-gate-audit-v1.json`;
- audit SHA-256:
  `019e7df71066c0407e48860efa57635a8f7bd8aca976ae5544d4a71f3ff05f95`;
- test mirati: 3/3;
- suite Python completa: 102/102;
- compilazione bytecode: superata;
- test .NET: superati;
- `git diff --check`: superato.

## Modifica del piano

Il singolo passo generico successivo e' stato separato in due incrementi:

1. E14.4k materializza e manifesta la feature foundation point-in-time dei
   quattro detector senza generare candidati;
2. E14.4l congela un protocollo a quattro detector legato alla tassonomia v5 e
   alla nuova foundation, quindi riesegue la readiness.

Questa separazione evita che l'atto di popolare i dati modifichi anche la
grammatica di ricerca e mantiene distinguibili integrita', informazione e
autorizzazione.
