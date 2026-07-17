# Checkpoint 0134 - E14.7aq FDIC archive atomic producer v4 remediated

Data: 2026-07-17

## Esito

E14.7aq implementa producer v4 senza modificare gli artefatti v3 reviewati.

La remediation introduce:

- registry dei contract hash compilato in un verifier separato: l'API del
  producer non riceve piu' un trusted hash dal caller;
- envelope v2 firmati con contract hash, catalog hash, acquisition run ID,
  nonce e collector receipt ID;
- collector receipt firmato, con catena append-only e distinzione esplicita tra
  `synthetic-test` e `provider-network-capture`;
- apertura descriptor-based con `O_NOFOLLOW` dove disponibile, controllo
  lstat/fstat e regular-file confinement;
- rilettura e confronto byte/hash di envelope, collector receipt, manifest,
  map e bundle audit prima del rename;
- test receipt v2 firmato, modulo/file derivati univocamente, runner hash-bound
  e transcript conservato e verificabile.

Il solo contract pinned e' esplicitamente synthetic-test; zero production
contract sono autorizzati. I 6 test producer e i 3 test audit sono verdi.
L'audit E14.7aq ha SHA-256
`0e45e5f8bf28d7422683c6ba4c91c2ef830257aa030f667de5a29756c69b14c3`.

## Decisione

Lo step ha eseguito zero rete, raccolto zero evidenze reali e pubblicato zero
bundle reali. Discovery catalog, execution gate operativo e source acquisition
restano chiusi. Il solo passo autorizzato e' E14.7ar: review indipendente della
trust boundary v4 e della distinzione tra integrita' firmata e attestazione di
rete.
