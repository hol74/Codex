# Macro Regime - Fase E: cronologia stress non recessivi v1

Data di chiusura: 2026-07-13.

## Esito

E' stata versionata ed eseguita una cronologia multi-label degli stress
macro-finanziari che non ricadono in mesi recessivi NBER. L'artefatto resta
separato sia dalla ground truth recessiva sia dai ledger shadow-live e non entra
mai negli input del detector.

Il report reale produce un risultato negativo per la baseline v1.4: sui mesi
OOS etichettati, gli stress sono classificati quasi sempre come `Goldilocks` o
`Reflation`. Non viene modificata alcuna soglia o associazione dopo la lettura
del report.

## Astrazione

Una singola classe esclusiva non era sufficiente. La cronologia usa quattro
dimensioni sovrapponibili:

- `financial_stress`;
- `growth_scare`;
- `inflation_shock`;
- `monetary_tightening`.

Un episodio puo' avere piu' etichette. Ogni etichetta dichiara i regimi primari
semanticamente attesi prima dell'esecuzione. Il report misura soltanto
allineamento sulle date positive, distribuzione dei regimi e incertezza; non
calcola accuracy o metriche della classe negativa, perche' l'assenza di un
episodio curato non prova assenza di stress.

Il comando richiede anche `nber-us-recessions-v1.json` e rifiuta qualunque
episodio che intersechi un mese recessivo. Gli overlap fra diverse dimensioni di
stress restano invece ammessi e misurati.

## Cronologia v1

Sei episodi, documentati con fonti BIS, Federal Reserve e FRED/BLS:

1. stress sovrano area euro, settembre-dicembre 2011;
2. stress Cina/mercati emergenti, agosto 2015-febbraio 2016;
3. repricing del rischio, ottobre-dicembre 2018;
4. shock inflazionistico, aprile 2021-maggio 2023;
5. ciclo di rialzi Fed, marzo 2022-luglio 2023;
6. stress bancario regionale USA, marzo-maggio 2023.

La cronologia e' curata ex-post e non pretende di essere una datazione
istituzionale esaustiva. I confini, le policy e i limiti sono inclusi nel JSON.

## Risultato reale baseline v1.4

Date OOS uniche 2018-2025:

| Etichetta | Mesi | Primary atteso | Operational atteso | Incertezza |
|---|---:|---:|---:|---:|
| financial stress | 6 | 0,00% | 0,00% | 0,00% |
| growth scare | 3 | 0,00% | 0,00% | 0,00% |
| inflation shock | 26 | 3,85% | 3,85% | 3,85% |
| monetary tightening | 20 | 5,00% | 5,00% | 5,00% |

Durante i sei mesi OOS di stress finanziario la baseline produce tre mesi
`Goldilocks` e tre `Reflation`; non produce mai `DeflationBust`. I tre mesi di
growth scare Q4 2018 sono tutti `Goldilocks`. Lo shock inflazionistico e il
tightening sono quasi sempre `Reflation`.

L'esito evidenzia due problemi distinti:

- un probabile blind spot su stress finanziario non recessivo;
- una limitazione del mapping label-regime: una dimensione come inflazione non
  determina da sola un regime composito senza lo stato contemporaneo di crescita
  e rischio.

La prima evidenza e' una debolezza concreta della baseline. La seconda richiede
in futuro una modellizzazione dimensionale o per combinazioni di label, ma la v1
non viene riscritta dopo avere osservato il report.

## Artefatti e hash

- cronologia: `research/regime-eval/ground-truth/us-non-recession-stress-v1.json`,
  SHA-256 `31df71a38bc948a2b8219124a40244a2afe5a02b88eee91cb69f71125825c913`;
- report locale: `data/historical-real-v11-2008-2025/baseline/baseline-v1-4-non-recession-stress-report.json`,
  SHA-256 `e4091272c6b0081a7b612210c603739832d0c2ee35cedb34c7f12122da241150`.

Il report lega tramite SHA-256 dataset, evaluation v1.4, walk-forward plan,
cronologia stress e ground truth NBER.

## Implementazione

- nuovo modulo `regime_eval/stress.py`;
- validatore di schema, tassonomia, fonti, date, coverage e riferimenti;
- controllo automatico anti-overlap NBER;
- report full-dataset e OOS a date deduplicate;
- comando CLI `stress-report`;
- test su multi-label, assenza di accuracy negativa e rifiuto overlap NBER.

## Verifiche

- 240 test C# superati;
- 18 test Python superati;
- report deterministico byte-for-byte;
- `compileall` superato;
- `git diff --check` superato (restano solo warning line-ending del workspace).

## Decisione e prossimo passo

La cronologia v1 diventa evidenza di audit, non promotion gate e non set di
tuning. La baseline v1.4 resta invariata. Il prossimo ledger mensile potra'
essere creato solo alla chiusura di luglio; prima di nuove varianti di modello,
un eventuale stress contract v2 dovra' esprimere aspettative dimensionali sulle
feature o combinazioni preregistrate di label, usando nuovi episodi per la
validazione.
