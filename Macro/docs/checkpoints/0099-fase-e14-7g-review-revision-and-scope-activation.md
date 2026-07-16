# Checkpoint 0099 - E14.7g review, revisione mirata ed E14.7h

Data: 2026-07-16

## Esito

Un subagent reviewer distinto ha aperto le fonti ufficiali dei due dossier.
London Whale e' stato accettato; Archegos ha ricevuto `needs-revision` per il
locator FDIC non direttamente apribile e per il confine maggio 2021 non
supportato dalla fonte trimestrale.

La revisione mirata ha sostituito il locator con il PDF FDIC ufficiale e ha
esteso il confine a giugno 2021. Il nuovo dossier Archegos ha SHA-256
`73953a3a52a08685d1b06c28f5f63f0bb1b6b962d9f1ebb2f5959d338e2d8230`;
London Whale conserva SHA-256
`2454b7091464fc5547c391e9cb37c89502ead391e15f184cc9445580da4a7158`.

Il reviewer ha riesaminato soltanto il nuovo hash, riaperto Federal Reserve e
FDIC e prodotto `accept` con tutti i check stretti veri. La queue finale ha
SHA-256 `6a2e9228e346adcfcaa961b457efa2f9bda311a333d6798d6864a8a7f4d1c2c6`;
l'audit di ingestion mirata ha SHA-256
`24ef12abe4ed05f8bee448970889e79071b0a542579e9807d92f09f09576c3e7`.

E14.7h ha materializzato `us-financial-stress-post2005-v1` con SHA-256
`3f69670e43315904e47a9bcae1957c62d780665b047355230198bb7a129e9d58`.
La taxonomy legacy v5 resta invariata. Scope e label post-2005 sono attivi;
nessuna osservazione e' stata acquisita e foundation, candidati, evaluation e
outer OOS restano chiusi. Il prossimo passo ammesso e' un manifest separato di
preregistrazione dell'acquisizione fonti.

## Verifica

- Python: 176 test superati dopo l'attivazione.
- .NET: suite completata con exit code 0.
- `compileall`: completato con exit code 0.
