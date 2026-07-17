# Checkpoint 0123 - E14.7af FDIC archive quarter map review blocked

Data: 2026-07-17

## Esito

La review indipendente hash-bound di E14.7ae ha restituito `needs_changes`.
Sono stati confermati:

- hash esatti di contratto, mappa, audit, piano, schemi e implementazione;
- roster ordinato 79/79 e URL trimestrali preservati;
- zero rete, zero record ID inventati e guard fail-closed;
- eliminazione della discovery archivio discrezionale a runtime.

La review ha pero' rilevato quattro finding bloccanti:

- le 79 entry provano soltanto assenza di evidenza locale, non inesistenza del
  record provider-primary;
- la mappa contiene zero record ID o URL `archive.fdic.gov` risolti ed e'
  quindi operativamente incompleta;
- lo schema E14.7ae puo' rappresentare soltanto entry irrisolte e non dispone
  di campi per record ID o archive URL risolti;
- l'audit afferma `archiveExpansionsFrozen = true`, ma il relativo schema e'
  troppo permissivo e non vincola le sezioni probatorie.

Il receipt della review ha SHA-256
`5241e4b3f3a1eff1ba408c50d4ef4d7d9cded1093a949df6ff0fe534f9873051`.
I 3 test mirati verificano schema chiuso, hash e decisione; l'intera suite di
294 test Python e' verde.

## Decisione

La mappa E14.7ae e' sicura soltanto come artefatto bloccante. Non autorizza un
gate sostitutivo.

Il prossimo passo consentito deve preregistrare una raccolta separata di
evidenza provider-primary che, per ciascun quarter, congeli un record ID o URL
`archive.fdic.gov` esatto oppure dimostri con evidenza hash-bound che il record
non esiste. La remediation deve inoltre versionare uno schema capace di
rappresentare entrambi gli esiti e un audit schema chiuso.

Rete, catalogo v3, source acquisition, snapshot v2, trasformazioni, candidati,
evaluation e outer OOS restano chiusi.
