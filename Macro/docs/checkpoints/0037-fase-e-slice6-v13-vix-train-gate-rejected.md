# Macro Regime - Fase E - Slice 6: v1.3 VIX train gate rejected

Data: 2026-07-13.

## Incremento

E' stata preregistrata e implementata la `1.3-candidate`, limitando la modifica a
`RISK_APPETITE`. Il mapping VIX lineare con clipping della v1.2 e' sostituito da
una logistica inversa con midpoint 20 e scala 7.

Sono rimasti invariati scoring archetipico, confidence, threshold 0,55 e gate
v2. Demo, v1.0, v1.1 e v1.2 conservano il comportamento precedente. La CLI
storica espone la candidate separata con `--baseline-version v1.3` e suffisso
`-v1-3-candidate`.

## Sequenza anti-tuning

1. configurazione modello v1.3 congelata;
2. test di formula, compatibilita', factory e CLI;
3. evaluation reale generata senza leggerne le distribuzioni OOS;
4. SHA-256 evaluation congelato nella configurazione gate v2;
5. apertura del solo report train gate.

## Risultato

- feature integrity: superata;
- `RISK_APPETITE` boundary rate: 27,38% -> 1,19%;
- regime coverage: superata, 4 regimi e dominante 53,57%;
- operational robustness: fallita, 2 fold su 6 contro il minimo di 4;
- incertezza aggregata: 60,71%;
- esito: non eleggibile, OOS non aperto.

La correzione locale della saturazione e' riuscita, ma ha esposto il disallineamento
fra nuova scala VIX, coordinate archetipiche e formula confidence. Il prossimo
incremento deve riallinearli train-only in una nuova versione, senza abbassare la
soglia o modificare retroattivamente la v1.3.

## Verifiche

- build completa: 0 warning, 0 errori;
- suite C# completa: 234 test superati (Domain 91, Application 30,
  Infrastructure 86, Reporting 2, CLI 19, Web 6);
- suite Python: 13 test superati; compileall superato;
- compatibilita' v1.2 verificata esplicitamente sul mapping VIX precedente;
- nessun client HTTP nei layer Domain/Application/Web.
