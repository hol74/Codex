# Event-aware financial stress v1

Data di freeze: 2026-07-14

## Ruolo e stato

- model id: `event-aware-financial-stress-v1`;
- task: `financial-stress-signal`;
- lifecycle: `research-challenger`;
- esito E12.3: `REJECTED_FOR_SHADOW`;
- approvazione operativa: non autorizzata.

## Ipotesi

Un segnale mensile che conserva massimi intramese e drawdown puo' riconoscere
shock finanziari brevi che spariscono nel campionamento month-end. La formula
combina VIX massimo, drawdown SPY/HYG e credit spread; SOFR-EFFR e' un overlay
opzionale, mai imputato quando assente.

## Protocollo

La configurazione, il gate e il foundation lock sono stati congelati prima
dell'esecuzione. Il gate usa 84 date inner-validation uniche, aggregando con la
prima fold eleggibile; zero righe outer-test. Le metriche classificative usano
solo mesi con almeno una label della cronologia stress v2: `financial_stress`
e' positivo, le altre label curate sono comparison control. I mesi senza label
non vengono dichiarati veri negativi.

## Risultato

- recall financial stress: `0,28571429`;
- precision: `0,66666667`;
- F1: `0,4`;
- Brier: `0,17646004`;
- average precision: `0,46610797`;
- ECE: `0,17392527`;
- longest alert run: 3 mesi;
- protected episode hit rate: `1,0`;
- repo settembre-ottobre 2019: intercettato;
- risk repricing 2018 Q4: episodio intercettato, ma ottobre e novembre persi;
- regional bank stress 2023: non intercettato.

Il gate passa F1, Brier, ECE, protected episode, repo, durata, fold e chiusura
outer. Fallisce recall minimo `0,50` e average precision minima `0,50`.

## Decisione

Il modello non passa allo shadow. Formula e soglie non vengono modificate dopo
l'esito. Un'eventuale variante richiede un nuovo model id e una nuova
preregistrazione; non puo' essere presentata come correzione della v1.

Report SHA-256:
`adf2939eac5af5223aea312393409c96c5da4a060325e75f5b1f85cb58002174`.
