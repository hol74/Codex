# Checkpoint 0113 - E14.7v acquisition discovery preflight

Data: 2026-07-16

## Esito

E14.7v ha eseguito soltanto i tre discovery request preregistrati nel catalogo
v2: landing H.8, landing FDIC QBP e calendario G.5. Manifest, catalogo e gate
E14.7u sono legati per hash canonico; URL e redirect restano sul provider host
originario. I payload sono stati validati in staging, hashati per audit e poi
eliminati prima della decisione.

L'audit immutabile
`e14-post2005-source-acquisition-execution-preflight-audit-v2.json`, SHA-256
`63e3a440d1f4756e05c9b278d220f322cf26441933b3504c2ec91c74ef13dee0`,
ha stato
`POST_2005_SOURCE_V2_ACQUISITION_BLOCKED_DISCOVERY_CATALOG_REMEDIATION_REQUIRED`.

Sono confermati quattro blocker:

- H.8: `0/1043` date di release direttamente presenti nella landing; la pagina
  usa un calendario JSON separato non preregistrato;
- FDIC: `0/79` documenti eleggibili nella landing congelata; l'archivio storico
  e' una pagina separata non preregistrata;
- FDIC: `0/79` prove provider-primary della data effettiva di pubblicazione;
  quarter-end non viene accettato come sostituto;
- G.5: 242 release coprono correttamente 240 mesi, ma `2024-08` e `2024-10`
  contengono duplicati/correzioni e richiedono adjudication separata.

Il reviewer indipendente ha inizialmente bloccato la materializzazione per
semantica insufficiente delle date FDIC, topologia output/staging e schema non
abbastanza vincolato. Dopo le correzioni ha approvato il preflight discovery
reale senza finding residui. Otto test mirati e l'intera suite di 254 test sono
verdi.

## Decisione

La full acquisition non e' autorizzata. Sono state effettuate tre sole
richieste discovery; richieste event-time e FRED, raw artifact pubblicati,
osservazioni, feature, candidati, evaluation e outer OOS restano a zero. Lo
snapshot v2 e lo staging sono assenti.

Il prossimo passo deve versionare il catalogo per preregistrare il calendario
H.8, l'archivio storico e le prove di pubblicazione FDIC, e produrre una
adjudication indipendente per i due mesi G.5 duplicati. Nessun endpoint puo'
essere seguito implicitamente dal catalogo v2 immutabile.
