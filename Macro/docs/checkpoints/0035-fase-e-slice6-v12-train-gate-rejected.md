# Macro Regime - Fase E - Slice 6: v1.2 train gate rejected

Data: 2026-07-13.

## Incremento

E' stato introdotto un profilo di scoring archetipico versionato per la baseline
`1.2-candidate`, senza modificare demo, v1.0 o v1.1. Il profilo usa distanza da
cinque archetipi, score quadratici e confidence composta da fit e margine.

Prima dell'esecuzione e' stata congelata la configurazione
`research/regime-eval/models/baseline-v1-2-preregistered.json`, legata all'hash
del dataset v1.1.

## Gate train-only

Il nuovo comando `baseline-train-gate`:

- verifica hash di dataset, evaluation, piano e configurazione;
- usa gli ultimi due anni di ogni outer train come inner validation;
- esclude le righe outer test da tutti i diagnostici e gate;
- scrive il report anche quando la candidate non e' eleggibile;
- non adatta ne' seleziona alcun parametro.

Il report reale registra 0 fold eleggibili su 6, contro il minimo preregistrato
di 4. L'outer OOS non e' stato aperto per i report di performance.

## Decisione

La v1.2 e' respinta al preflight. Non si modificano soglia, archetipi o pesi dopo
l'esito. Prima di una v1.3 il protocollo dovra' separare i gate aggregati di
integrita'/copertura dai gate per-fold di confidence: una finestra biennale puo'
legittimamente contenere meno di tre regimi e non deve da sola invalidare la
copertura multiregime complessiva.

## Verifiche

- build completa: 0 warning, 0 errori;
- suite C# completa: 232 superati (Domain 90, Application 30,
  Infrastructure 85, Reporting 2, CLI 19, Web 6);
- test Python: 12 superati;
- compileall Python: superato;
- test anti-leakage del gate: la riga outer test non compare nel riepilogo inner;
- artefatto reale: `baseline-v1-2-train-gate.json`, gate negativo;
- nessun report OOS, audit OOS o confronto NBER generato per v1.2.

Il gate v2 previsto qui e' stato implementato nel checkpoint 0036. Ha separato
correttamente copertura e operativita', ma la candidate resta bloccata dalla
saturazione aggregata di `RISK_APPETITE`.
