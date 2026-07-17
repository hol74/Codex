# Checkpoint 0136 - E14.7as FDIC archive atomic producer v5 remediated

Data: 2026-07-17

## Esito

E14.7as implementa producer v5 senza modificare gli artefatti v4 reviewati.
La remediation introduce:

- signer ID del test runner risolto esclusivamente da un registry statico; il
  receipt v3 non contiene una chiave pubblica auto-dichiarata;
- ledger append-only nello stesso publication root, lock esclusivo, verifica
  del chain head e unicita' di acquisition run, nonce e receipt;
- commit durevole del ledger prima del rename del bundle, mantenendo il nonce
  consumato anche se la pubblicazione finale fallisce;
- receipt schema v2 e bundle audit schema v5 con roster esatti e valori
  SHA-256, senza proprieta' arbitrarie;
- rifiuto strutturale di `provider-network-capture`: v5 supporta soltanto il
  contract synthetic-test pinned e non pretende di provare attivita' di rete;
- qualifica esplicita Windows `descriptor-identity-fallback`, con symlink
  precheck, lstat/fstat device-inode e regular-file descriptor check.

Gli 8 test producer e i 4 test audit sono verdi. Il test receipt e' verificato
con chiave esternamente pinned e transcript conservato. L'audit E14.7as ha
SHA-256
`1fd38f5e834ace2a17f7de32e72460aa32d8842b89144fd8ca90d7a2ca233a8f`.

## Decisione

Lo step ha eseguito zero rete, raccolto zero evidenze reali, pubblicato zero
bundle reali e pinned zero contract di produzione. Discovery catalog,
execution gate operativo e source acquisition restano chiusi.

Il solo passo autorizzato e' E14.7at: review indipendente di trust anchor del
test runner, scope del ledger, semantica crash/replay, schemi chiusi e qualifica
Windows.
