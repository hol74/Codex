# Checkpoint 0127 - E14.7aj FDIC archive evidence remediation review blocked

Data: 2026-07-17

## Esito

La review indipendente hash-bound di E14.7ai ha restituito `needs_changes`.
Sono stati confermati hash, zero rete e miglioramenti reali su roster 79/79,
unicita' di quarter/evidence, coerenza outcome/hash e riconciliazione dei
conteggi audit.

Prove dirette di bypass hanno pero' rilevato cinque finding bloccanti:

- il validator non apre, misura o calcola l'hash dei file raw; accetta metadata
  coerenti che puntano a file inesistenti;
- request ID duplicati, redirect non continui, source catalog inesistente e URL
  trimestrali non legati al catalogo possono essere accettati;
- schema validation e semantic validation non sono integrate: versioni schema
  errate e campi schema-invalid possono superare il validator;
- manca un producer atomico che validi e pubblichi insieme manifest, map e audit
  soltanto dopo tutti i controlli;
- i test negativi non coprono questi bypass, ne' il ramo confirmed-absent.

Il receipt della review ha SHA-256
`3b1840e9b07ae7f2005487a3abcf60f8440624b357b70bde17a0e4780a000ac5`.
I 3 test mirati verificano schema chiuso, hash e decisione; l'intera suite di
313 test Python e' verde.

## Decisione

E14.7ai migliora la coerenza dichiarativa, ma non verifica ancora evidence raw
provider-primary e non implementa pubblicazione atomica fail-closed. Il design
del discovery catalog non e' autorizzato.

Il prossimo passo deve integrare schema e semantic validation, leggere e
verificare i bytes raw, imporre request ID univoci e redirect continuity,
legare ogni URL trimestrale al source catalog hash-bound, coprire l'esito
confirmed-absent e introdurre un producer atomico con test di failure.

Rete, discovery catalog, execution gate, catalogo v3, source acquisition,
snapshot v2, trasformazioni, candidati, evaluation e outer OOS restano chiusi.
