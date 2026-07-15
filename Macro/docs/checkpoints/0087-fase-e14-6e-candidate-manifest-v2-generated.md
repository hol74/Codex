# Checkpoint 0087 - E14.6e candidate manifest v2 generated

Data: 2026-07-15

## Obiettivo

Materializzare in modo immutabile i 28 candidati gia' definiti dal roster e
dal protocollo v2, senza trasformare feature, fittare soglie o consultare
l'outer OOS.

## Realizzato

- aggiunti schema e contratto hash-bound del manifest v2;
- aggiunto il comando `e14-materialize-candidate-manifest-v2`;
- copiati i 28 candidati nello stesso ordine del roster e del protocollo;
- verificato che ID, detector, meccanismo, profilo, feature binding,
  persistenza, eligibility e identity policy restino invariati;
- applicata la sola transizione di lifecycle da
  `readiness-planned-not-generated-not-fit` a `research-generated-not-fit`;
- prodotti manifest e generation audit write-once.

## Esito reale

- stato: `GENERATED_V2_NOT_TRANSFORMED_NOT_FIT_NOT_EVALUATED_OUTER_OOS_CLOSED`;
- generation ID: `1c9829675e0fba3101029b5c`;
- candidati: 28, ripartiti in 4 banking-credit, 16 broad-market-repricing,
  4 cross-border-growth e 4 funding-liquidity;
- SHA-256 manifest: `a41040eca75e9f7009c03efc9ee850979fd1776a98fb28d5e2b30128defadccb`;
- SHA-256 audit: `3ab76146a05ce1860f774e98b3c6c557d96e58350cc002e27826343039fe9c6f`;
- feature trasformate: 0;
- righe outer usate: 0;
- fitting, evaluation, ranking, composizione e promozione: non autorizzati.

## Verifiche

- test mirati E14.6e: 3/3;
- regressione Python: 129/129;
- `compileall`: superato;
- test .NET: superati;
- controllo whitespace/diff Git: superato.

La prima prova manuale con `python -m regime_eval.cli` ha restituito zero senza
eseguire il comando, perche' quel modulo non invoca direttamente `main`.
L'artefatto reale e' stato quindi prodotto tramite l'entry point pubblico e
documentato `python -m regime_eval`; presenza, contenuto e hash degli output
sono stati verificati esplicitamente.

## Decisione e prossimo passo

E14.6e e' completato. E14.6f deve preregistrare l'esecuzione inner-only del
fitting e della valutazione leave-one-episode-out v2, includendo gate assoluti
per meccanismo e sensitivity funding 2019. Outer OOS, composizione e promozione
restano chiusi.
