# Checkpoint 0110 - E14.7s policy redesign attivata

Data: 2026-07-16

## Esito

Il gate separato E14.7s ha attivato l'overlay immutabile
`e14-post2005-active-source-vintage-policy-v2`, preservando byte-identiche la
taxonomy post-2005 attiva e le label gia' accettate.

La policy attiva congela due decisioni revisionate:

- `cross-border-growth`: H.10 e' ritirato, G.5 e' la sorgente candidata attiva
  e i regimi legacy Broad/OITP e Broad/AFE/EME restano separati, senza splice o
  backcast event-time;
- `banking-credit`: H.8/FDIC restano vincolati all'ultima release realmente
  pubblicata entro ogni as-of date e il quarter-end non prova disponibilita'.

Il vecchio manifest e lo snapshot H.10 non sono validi per la policy v2 e non
sono stati modificati o reinterpretati. Gli output sono:

- active policy SHA-256 `94db6eb64b83ea3d54ca36c8d3311f983ab48f998c4b6bb9e7218df8aad049fd`;
- activation audit SHA-256 `0c86c0545cddc580680804b4b3c0b701718450fd818381a19d435d94071c3d2f`.

Un subagent di design ha verificato la separazione overlay/taxonomy. Un secondo
subagent reviewer ha bloccato la prima versione dello schema audit perche'
troppo permissiva; dopo la chiusura completa dello schema e l'aggiunta della
validazione deterministica ha approvato esplicitamente senza blocker. I sette
test mirati e l'intera suite di 229 test, compileall e diff-check sono verdi.

## Decisione

La source-vintage policy v2 e' attiva. E' autorizzato esclusivamente un nuovo
step separato che preregistri un manifest di acquisizione e request catalog
versionati e legati a questa policy. Il catalogo non e' ancora generato;
acquisizione, trasformazione, candidati, evaluation e outer OOS restano chiusi.
