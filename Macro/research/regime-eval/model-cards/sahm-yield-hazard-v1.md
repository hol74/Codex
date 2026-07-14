# SAHM yield hazard v1

Data di freeze: 2026-07-14

## Ruolo e stato

- model id: `sahm-yield-hazard-v1`;
- task: `recession-signal`;
- lifecycle: `research-challenger`;
- esito E12.4: `REJECTED_FOR_SHADOW`;
- approvazione operativa: non autorizzata.

## Ipotesi

SAHM real-time e deterioramento della produzione descrivono conferma ciclica,
mentre inversione e successivo irripidimento della curva descrivono hazard
anticipato. La formula e' causale, stateless e usa soltanto il minimo della
curva corrente e delle 23 osservazioni precedenti.

## Protocollo

Configurazione, gate e foundation lock sono stati congelati prima
dell'esecuzione. Il gate usa 84 date inner-validation uniche e zero righe
outer-test. Le probabilita' sono prodotte prima di collegare la cronologia NBER.

## Risultato

- mesi recessivi inner: 2;
- recall: `0,5`;
- precision: `0,07692308`;
- F1: `0,13333333`;
- Brier: `0,11911666`;
- average precision: `0,0625`;
- ECE: `0,13514533`;
- longest false-positive run: 12 mesi;
- marzo 2020 perso;
- primo segnale aprile 2020, detection lag di un mese.

Passano recall, Brier, ECE, detection lag, fold, copertura positiva e chiusura
outer. Falliscono F1, average precision e durata dei falsi positivi. SAHM e
INDPRO confermano il deterioramento, ma restano elevati dopo la brevissima
recessione COVID-19.

## Decisione

Il candidato non passa allo shadow. Non viene aggiunta post-hoc una policy di
durata o uscita: una variante richiederebbe nuovo model id e preregistrazione.

Report SHA-256:
`15d935f8dbbcaccca6b23b37b172b6cdcbba19114b8c17375e90e9f1b294ab2a`.
