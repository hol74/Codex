# Checkpoint 0144 - E14.8b operational protocol remediated

Data: 2026-07-17

## Esito

E14.8b risolve i due blocker della review E14.8a. Le dieci evidenze di
provisioning sono ora proprieta' individualmente obbligatorie di un oggetto
chiuso: la rimozione di ciascuna viene respinta dai test.

Il protocollo provider-neutral congela state machine ABSENT/PENDING/COMMITTED,
read, CAS pending, commit e recovery; definisce identita' e ruoli, idempotency
key, errori e retry, receipt chain, crash/rollback recovery, cross-volume,
directory durability, descriptor no-follow, process-start lock identity e
read-after-write. Una matrice di 14 test di conformita' e' obbligatoria prima
di qualunque futura capability.

## Gate

Zero rete, provider, credenziali, risorse, authority e pubblicazioni. Il solo
passo aperto e' E14.8c, review indipendente della remediation.

Audit SHA-256:
`f50bc59038e165601fe906486a8e88600386ea9636b9f9d4e12c31d4e9076f6f`.
