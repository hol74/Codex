# Macro-Regime - Release E9.2 e CI

Data di completamento: 2026-07-14.

## Esito

Il branch `codex/e9-2` e' stato preparato per l'integrazione in `main` come
release tecnica verificabile. E' stata aggiunta una GitHub Actions workflow che
esegue build e test C# e i controlli del research lab Python senza richiedere
segreti o accesso alle fonti esterne.

La release e' descritta in `docs/releases/macro-regime-e9.2.md` e verra'
identificata dal tag annotato `macro-regime-e9.2` dopo il merge fast-forward.

## Confine della release

La release dichiara completo E9.2 dal punto di vista tecnico. Non dichiara
completa l'evidenza prospettica: il cutoff 2026-07-31 non e' ancora eleggibile e
la baseline v1.4 resta congelata.

## Gate

- working tree pulito prima dell'integrazione;
- differenza `main..codex/e9-2` interamente revisionata;
- build Release e test locali superati;
- CI equivalente configurata su GitHub;
- merge solo fast-forward;
- tag creato soltanto sul commit integrato in `main`.

Risultati locali: build Release con 0 warning e 0 errori, 240 test C# e 25
test Python superati, `compileall` superato.
