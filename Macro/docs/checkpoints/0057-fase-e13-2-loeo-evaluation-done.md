# Checkpoint 0057 - E13.2 valutazione LOEO

Data: 2026-07-14

## Obiettivo

Valutare la popolazione E13 con leave-one-episode-out esclusivamente sulle
finestre inner, separando la capacita' di generalizzare tra eventi dalla
semplice aderenza media alla cronologia osservata.

## Realizzato

- congelato `e13-loeo-evaluation-contract-v1` prima del report definitivo;
- fissato un minimo di tre episodi osservabili per task;
- selezionata la soglia, per ogni leaveout, soltanto sugli altri episodi e sui
  controlli curati non finanziari;
- implementate persistenze distinte di ingresso e recupero;
- valutati gli 8 candidati finanziari su 3 episodi e 23 mesi di controllo;
- marcati gli 8 candidati recessivi `INSUFFICIENT_EPISODES`: nell'inner e'
  osservabile soltanto la recessione COVID-19;
- mantenuti zero utilizzi delle righe outer-test e nessuna shortlist.

## Risultati

Il ramo finanziario non presenta ancora un vincitore dominante:

- `noisy-or`, ingresso 2 e recupero 2, colpisce 3/3 episodi e ha worst recall
  `0,6667`, ma segnala il `78,26%` dei mesi di controllo;
- `top-two-mean`, ingresso 1 e recupero 1, riduce i falsi positivi al `4,35%`,
  ma colpisce solo 2/3 episodi e ha worst recall zero;
- le altre configurazioni si collocano tra questi estremi o sono dominate;
- il range delle soglie scelte e' zero per sette candidati su otto: la
  principale instabilita' viene dalla struttura del segnale, non dal tuning
  della soglia.

Il ramo recessivo non viene ordinato: con un solo episodio un LOEO reale non
puo' stimare generalizzazione tra recessioni. Aprire l'outer per aggirare il
limite violerebbe il contratto.

## Identita' degli artefatti

- evaluation contract SHA-256:
  `71c1e3ce297b79be295435e254c9803e073292cf0d6ea6cabb1d6f49cbdc4e47`;
- report SHA-256:
  `1c2352d7731901c57618389780d330152dc789a62da4cf3f40879c408cd24317`.

## Decisione

E13.2 e' completata come diagnostica. E13.3 puo' costruire una shortlist Pareto
solo per il task finanziario, conservando almeno un candidato orientato alla
copertura e uno alla precisione. Il task recessivo resta bloccato finche' non
esiste una foundation con almeno tre episodi osservabili; non deve ricevere una
shortlist surrogata.

## Verifica

- `dotnet test MacroRegime.slnx --no-restore`: 240/240 test superati;
- `python -m unittest discover -s tests -v`: 48/48 test superati;
- `python -m compileall -q regime_eval tests`: superato;
- determinismo byte-per-byte del report;
- semantica write-once;
- controllo contrattuale di manifest, protocollo, lock, dataset e piano;
- zero righe outer-test utilizzate;
- test dedicati su persistenza, copertura episodi e insufficienza recessiva.
