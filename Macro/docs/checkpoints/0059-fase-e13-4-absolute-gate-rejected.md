# Checkpoint 0059 - E13.4 gate assoluto

Data: 2026-07-14

## Obiettivo

Applicare requisiti assoluti e indipendenti ai due candidati finanziari
shortlistati, consentendo esplicitamente che entrambi vengano respinti.

## Realizzato

- congelato `e13-financial-absolute-gate-v1`, legato a shortlist e report LOEO;
- richiesti congiuntamente almeno 3 episodi, hit rate `1,0`, recall medio e
  worst-case almeno `0,5`, falsi allarmi non oltre `0,15`, threshold range non
  oltre `0,15` e complexity score non oltre 6;
- vietati confronto relativo, fallback al meno peggio, rescue tramite outer
  OOS e fusione;
- eseguite decisioni indipendenti e write-once;
- mantenuto il ramo recessivo fuori dal gate per evidenza insufficiente.

## Esiti

- `e13-financial-8ec8415452` (`coverage`): `REJECTED_FOR_SHADOW`.
  Supera copertura, recall, stabilita' e complessita', ma fallisce
  `maximumMeanControlFalsePositiveRate`: `0,7826087` contro massimo `0,15`.
- `e13-financial-7452a93533` (`precision`): `REJECTED_FOR_SHADOW`.
  Supera falsi allarmi, stabilita' e complessita', ma fallisce hit rate
  (`0,66666667`), recall medio (`0,27777778`) e worst recall (`0`).

E13 termina con zero candidati eleggibili per shadow review.

## Identita' degli artefatti

- gate SHA-256:
  `a3fe7dd2b628fe2c269f60d7b97f25a47245eb6fe8b5c141022ef58c22f8a12f`;
- decisioni SHA-256:
  `9f0d061319f5bece558c5572f0f02ecf222bf97d10125cab08231d93fe2b6db0`.

## Decisione

Nessun tuning post-gate e nessun passaggio automatico all'outer OOS. Il nuovo
percorso ha migliorato la disciplina di generazione e ha reso esplicito il
trade-off, ma non ha prodotto un segnale finanziario contemporaneamente
sensibile e selettivo. Il limite recessivo resta la scarsita' di episodi.

## Verifica

- `dotnet test MacroRegime.slnx --no-restore`: 240/240 test superati;
- `python -m unittest discover -s tests -v`: 52/52 test superati;
- `python -m compileall -q regime_eval tests`: superato;
- decisioni deterministiche byte-per-byte e write-once;
- fallimenti metrici verificati candidato per candidato;
- zero fallback, zero righe outer-test e zero fusioni;
- rifiuto di un contratto che riapre l'outer OOS.
