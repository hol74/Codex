# Checkpoint 0102 - E14.7k snapshot raw atomico

Data: 2026-07-16

## Esito

Le sette fonti autorizzate sono state acquisite in staging e pubblicate con un
singolo rename atomico. Il primo tentativo ha ricevuto HTTP 400 da FRED per il
limite di 2.000 vintage dates; lo staging e' stato eliminato integralmente. Le
quattro serie sono state quindi congelate in quattro tranche real-time ciascuna.

Lo snapshot finale contiene:

- 23 raw artifact;
- 13.451.891 bytes complessivi;
- 16 JSON FRED initial-release;
- 20.810 osservazioni validate soltanto per finestra e metadati realtime;
- 2 bulk ZIP Federal Reserve;
- 2 spreadsheet FDIC e il relativo indice QBP;
- 2 pagine ufficiali di release/metodologia.

Tutti gli SHA-256 corrispondono all'indice. I quattro container ZIP/XLSX sono
integri e nessun valore della credenziale FRED e' presente nello snapshot.
L'indice ha SHA-256
`79cbe527e0435980ce2b89f24585b62b6939937e5baf4ac4a1ad04c8cad967d9`;
l'audit ha SHA-256
`1bd44b531ff72eecddefde4d7da74ea2096d5afb50678a25155353fbe701fd55`.

## Limiti e prossimo passo

Sedici artifact FRED sono event-time initial-release. I bulk H.8/H.10 e gli
spreadsheet FDIC che possono contenere revisioni restano `raw-only` e non sono
ancora trasformabili. Feature, candidati, evaluation e outer OOS sono chiusi.
Il prossimo passo ammesso e' l'audit di completezza e vintage fitness per ogni
famiglia, senza calcolare feature.
