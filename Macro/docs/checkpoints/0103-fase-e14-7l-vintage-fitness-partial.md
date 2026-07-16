# Checkpoint 0103 - E14.7l vintage fitness parziale

Data: 2026-07-16

## Esito

L'audit fail-closed dello snapshot raw E14.7k e' stato completato senza
calcolare feature. Tutti i 23 hash e i quattro container sono stati verificati.
Le 20.810 osservazioni FRED sono state usate soltanto per riconciliare conteggi,
estremi, unicita', tranche realtime, cronologia initial-release e lag congelati.

Due famiglie su quattro risultano vintage-fit:

- `broad-market-repricing` tramite DGS2 e DGS10;
- `funding-liquidity` tramite DCPF3M e DTB3.

Due famiglie richiedono remediation:

- `banking-credit`: H.8 e FDIC sono `raw-only`; gli XLSX FDIC arrivano soltanto
  al 2011Q4 e non conservano i vintage delle pubblicazioni trimestrali;
- `cross-border-growth`: il bulk H.10 corrente non conserva i vintage delle
  singole release.

L'audit immutabile ha SHA-256
`8dc95ac6f6155f09fa25b713cee893bf5e065c93745d019c717cc230d8db1ecb`.

## Decisione

La trasformazione richiede quattro famiglie vintage-fit su quattro e resta
quindi non autorizzata. Sono vietati anche generazione candidati, evaluation e
lettura outer OOS. Il prossimo passo ammesso e' una remediation mirata che
acquisisca artifact datati di release per H.8/H.10 e FDIC, seguita dalla
ripetizione di questo audit.
