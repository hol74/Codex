# Checkpoint 0088 - E14.6f LOEO v2 preregistered

Data: 2026-07-15

## Obiettivo

Congelare prima del fitting la valutazione leave-one-independent-episode-out
dei 28 candidati v2, includendo fold, trasformazioni train-only, gate assoluti,
sensitivity funding 2019 e controllo del rischio di revisione.

## Realizzato

- aggiunti schema, piano e contratto hash-bound della preregistrazione v2;
- verificata la catena completa taxonomy -> foundation/lock/audit ->
  protocollo/audit -> manifest/audit;
- congelate 140 assegnazioni candidato-episodio con label held-out non
  disponibili a trasformazioni o selezione soglia;
- preregistrate q80/q90/q95 calcolate sui soli training score;
- congelati gate assoluti uguali e indipendenti per i quattro meccanismi;
- resa obbligatoria la sensitivity funding sul confine `2019-01-01`;
- reso obbligatorio il confronto hash degli snapshot prima della valutazione;
- aggiunto il comando `e14-preregister-loeo-v2` e tre test di regressione.

## Esito reale

- stato:
  `INNER_LOEO_V2_PREREGISTERED_FULL_READINESS_FITTING_EVALUATION_AUTHORIZED_OUTER_OOS_CLOSED`;
- candidati eleggibili: 28/28;
- fold: 140 totali, con 12 banking, 96 broad, 20 cross-border e 12 funding;
- SHA-256 audit:
  `db28f35a8165ea6a50d165a28e4652b98c6b9540f64cb4cfcf53a7c0add8c15a`;
- trasformazioni, fitting e valutazioni eseguite: nessuna;
- righe outer usate: 0;
- ranking, composizione e promozione: non autorizzati.

## Gate assoluti congelati

- almeno 3 positivi e 2 hard negative osservabili;
- episode hit rate almeno 0,67;
- mean episode recall almeno 0,50;
- worst episode recall almeno 0,25;
- hard-negative alert rate al massimo 0,20;
- mediana onset delay al massimo 2 mesi;
- mediana recovery lag al massimo 3 mesi;
- threshold range al massimo 0,15.

Ogni requisito deve passare indipendentemente. Ranking relativo e risultato di
un altro meccanismo non possono recuperare un gate fallito.

## Verifiche

- test mirati E14.6f: 3/3;
- regressione Python: 132/132;
- `compileall`: superato;
- test .NET: superati;
- controllo source hash e diff Git: superato.

## Decisione e prossimo passo

E14.6f e' completato. E14.6g puo' eseguire le trasformazioni causali, il
fitting e la valutazione LOEO esclusivamente sui 140 fold preregistrati.
Ranking, composizione, outer OOS e promozione restano chiusi.
