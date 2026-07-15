# Checkpoint 0089 - E14.6g LOEO v2 no-go

Data: 2026-07-15

## Obiettivo

Eseguire trasformazioni causali, fitting delle soglie e valutazione dei 28
candidati sui 140 fold LOEO preregistrati, applicando i gate assoluti senza
ranking, composizione o accesso all'outer OOS.

## Realizzato

- aggiunti schema e contratto hash-bound del report LOEO v2;
- aggiunto il comando `e14-loeo-evaluate-v2`;
- implementato il percentile causale con midrank per gestire correttamente i
  pareggi, in particolare gli zeri FDIC;
- escluso il valore held-out dalla storia futura della trasformazione, pur
  consentendone la trasformazione causale come input corrente;
- implementata missingness esplicita che interrompe la persistenza senza zero
  imputation;
- selezionate q80/q90/q95 sui soli training score secondo l'ordine di obiettivi
  congelato;
- calcolati hit/recall per episodio, onset, recovery, hard-negative alert,
  threshold range e alert non etichettati non sottoposti a scoring;
- prodotta sensitivity funding full/pre-2019 con tutte le tre soglie, shift
  normalizzato per IQR, alert rate e metriche episodio pre/post.

## Esito reale

- candidati valutati: 28/28;
- fold consumati una volta: 140/140;
- candidati che superano tutti i gate: 0;
- miglior banking: `e14-banking-v2-fafdbc5dab63`, hit rate 0,66666667,
  mean recall 0,50, worst recall 0 e hard-negative alert 0,06666667;
- miglior broad: `e14-broad-1d3f9292459f`, hit rate e mean recall 0,16666667;
- miglior cross-border: `e14-cross-border-v2-4c42c1cfbe69`, hit rate 0,40 e
  mean recall 0,17142857;
- miglior funding: `e14-funding-v2-b06890d7383a`, hit rate e recall zero;
- report funding completi: 12/12;
- SHA-256 report:
  `e0912b017aaeddb15c1f218107c1aa7a58df2643b55293a0354bc769ea59e855`;
- ranking, shortlist, composizione, outer OOS e promozione: non autorizzati.

## Interpretazione

I candidati controllano generalmente bene gli hard negative e mostrano soglie
stabili, ma non generalizzano tra episodi positivi: worst episode recall e'
zero per tutti i profili. Abbassare post-hoc soglie o gate sullo stesso
benchmark violerebbe la preregistrazione e non e' autorizzato.

## Verifiche

- test mirati E14.6g: 4/4;
- regressione Python: 136/136;
- `compileall`: superato;
- test .NET: superati;
- source hash, input hash e diff check: superati;
- righe outer usate: 0.

## Decisione e prossimo passo

E14.6g e' concluso con no-go. E14.6h deve decomporre i fallimenti per episodio,
profilo e meccanismo e decidere tra chiusura E14 o una nuova ipotesi
informativa preregistrata. Ranking rescue, tuning post-hoc, composizione e outer
OOS restano vietati.
