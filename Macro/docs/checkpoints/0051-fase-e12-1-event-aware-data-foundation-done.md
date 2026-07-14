# Checkpoint 0051 - E12.1 event-aware data foundation

Data: 2026-07-14

## Obiettivo

Rimuovere il blind spot causato dal campionamento del solo ultimo valore
mensile e definire lifecycle separati per segnale recessivo e stress
finanziario, prima di provare altri modelli.

## Realizzato

- aggiunte le sorgenti giornaliere FRED `SOFR` ed `EFFR` al solo population
  storico, senza modificare le sette serie della baseline operativa;
- calcolate point-in-time quattro feature intramese:
  `VIX_MONTHLY_MAX`, `SOFR_EFFR_MONTHLY_MAX`,
  `SPY_MONTHLY_MAX_DRAWDOWN` e `HYG_MONTHLY_MAX_DRAWDOWN`;
- limitata ogni finestra al mese corrente e alle osservazioni disponibili entro
  la data campionata; publication/vintage delle feature derivate coincidono con
  la data di calcolo;
- espresso lo spread SOFR-EFFR in basis point e i drawdown come percentuale
  positiva dal massimo progressivo del mese;
- mantenuto il dataset schema v1: le feature entrano come osservazioni macro
  aggiuntive, quindi baseline ed evaluator esistenti restano compatibili;
- versionato a 2 il manifest del corpus e aggiunti conteggi di copertura per
  feature; l'assenza di SOFR prima dell'avvio della serie resta assenza, senza
  backfill o zero-imputation;
- congelato `e12-task-lifecycle-v1`: gate distinti `recession-signal` e
  `financial-stress-signal`, con fusione vietata prima delle valutazioni
  indipendenti.

## Scelte operative

L'aggregazione avviene in population, non nel modello. In questo modo il dato
che il candidato vede e' manifestato, hashato e verificabile. Il contratto non
pretende che un rilevatore di stress finanziario superi il gate NBER: quel
modello deve prima dimostrare copertura degli episodi finanziari protetti e
controllo dei falsi positivi. Un candidato recessivo conserva invece la
cronologia NBER come verita' primaria.

## Verifica

- fixture con spread SOFR-EFFR massimo di 300 bp;
- fixture con drawdown SPY intramese di 9,090909%;
- controllo che publication date non superi l'as-of;
- `dotnet test MacroRegime.slnx --no-restore`: 240/240 test superati;
- `python -m unittest discover -s tests -v`: 35/35 test superati;
- `python -m compileall -q regime_eval tests`: superato;
- gate architetturale: nessun `HttpClient` nei sorgenti Domain, Application o
  Web;
- baseline series catalog invariato; nessun outer OOS aperto e nessun modello
  promosso.

## Prossimo incremento

E12.2 deve ripopolare un corpus reale separato, costruire il dataset, produrre
un coverage report per feature/fold e congelarne gli hash. Solo dopo si
implementano `event-aware-financial-stress-v1` e `sahm-yield-hazard-v1` con gate
inner-only specifici per task.
