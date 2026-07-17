# Checkpoint 0143 - E14.8a provisioning design review needs changes

Data: 2026-07-17

## Esito

La review indipendente E14.8a termina con `needs_changes`. Il boundary corrente
resta safely blocked, ma il disegno non e' ancora accettabile: lo schema rende
omissibili due delle dieci evidenze dichiarate congelate e le capacita' tecniche
sono boolean label prive di un protocollo operativo provider-neutral.

## Remediation autorizzata

E14.8b deve rendere obbligatorie tutte le evidenze e definire state machine,
CAS autenticato, versioni monotone, idempotency key, identita', errori/retry,
recovery crash/rollback e verifiche di durability/no-follow/lock identity.
Ogni altra capacita' resta chiusa.

Review receipt SHA-256:
`7b5a1a00b2e795fbb7a4d0e1789f42f8bcfd59a7e2938b5f431bcea2f2bbd177`.
