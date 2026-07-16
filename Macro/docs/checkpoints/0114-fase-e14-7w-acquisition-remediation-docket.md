# Checkpoint 0114 - E14.7w acquisition remediation docket

Data: 2026-07-16

## Esito

E14.7w ha materializzato un docket review-first, non un catalogo eseguibile:

- proposta remediation SHA-256 `184a4bfe22cb9774777299d2f1c24301d5ee5d45595b355c91727111bc637cef`;
- dossier G.5 SHA-256 `1a1b9ce20e21e8b3195530fe5e0af853f01c86d8095a554f2b86c37c0989b24d`;
- review queue SHA-256 `eac2dc1336a7240ab48565ede2e33a3c5f5d8c5cd17e059793e5b76f1c22c7cb`;
- audit SHA-256 `1a2bb20b6ef40a563fdc316ba8adee0ea214d5dda3d3faa3faf3ae4d30c62105`.

Il calendario provider-primary H.8 corregge esplicitamente il requisito
derivato da 1.043 a 1.042 release nel 2006-2025; la modifica richiede review e
non autorizza automaticamente il catalogo. L'archivio FDIC dimostra il roster
completo di 79 trimestri 2006Q1-2025Q3, ma il ledger delle date effettive di
pubblicazione resta `0/79` e bloccante.

Il dossier G.5 conserva tutte e quattro le release. Le catene proposte sono
`20240801 -> 20240807` e `20241001 -> 20241003`: l'originale resta efficace
fino alla correzione, che diventa utilizzabile soltanto dalla propria data.
Backdating e cancellazione dell'originale sono vietati.

Il reviewer indipendente ha inizialmente bloccato la materializzazione per
assenza non verificata del catalogo v3 e schema nested aperti. Dopo controllo
filesystem fail-closed, snapshot assente e schema ricorsivamente chiusi, ha
approvato senza finding residui. Sei test mirati e l'intera suite di 260 test
sono verdi.

## Decisione

E' autorizzata soltanto la review indipendente del docket. Catalogo v3,
network request, acquisizione, raw artifact, feature, candidati, evaluation e
outer OOS restano vietati. Il passo seguente deve valutare H.8, il roster/gap
FDIC e le catene G.5 usando lo schema receipt hash-bound; la raccolta
metadata-only delle 79 prove FDIC resta successiva e separata.
