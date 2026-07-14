# Checkpoint 0062 - E14.3 historical foundation feasibility

Data: 2026-07-14

## Obiettivo

Decidere se fonti storiche point-in-time e proxy compatibili rendono sensata
un'estensione pre-2008, prima di scaricare o popolare un nuovo corpus.

## Realizzato

- congelato un catalogo di 12 fonti ufficiali e quattro classi as-of;
- separati input strettamente point-in-time, pilot con snapshot/calendario,
  label evidence e benchmark diagnostici ricostruiti;
- riusata l'astrazione vintage FRED/ALFRED gia' presente nel progetto;
- esclusi NFCI, STLFSI4 e OFR FSI dalle feature rigorosamente point-in-time;
- registrate 5 ipotesi pre-2008, sempre `hypothesis-only`;
- implementato un gate deterministico, write-once e senza lettura del dataset;
- vietati splicing implicito LIBOR/SOFR, uso dei compositi revisionati,
  creazione di label e generazione di candidati.

## Evidenza

Le fonti disponibili rendono plausibile un pilot per almeno una feature e una
fonte di label per ciascun meccanismo. Combinando gli episodi correnti con le
ipotesi, i positivi proiettati sono 7 broad-market, 3 funding, 3 banking e 5
cross-border.

Non e' stata trovata prova sufficiente per alcun hard negative. Un indice
basso, l'assenza di interventi o un mese unlabeled non costituiscono prova
affermativa che uno specifico meccanismo sia rimasto ordinato.

## Decisione

`GO_FOR_EPISODE_DOSSIERS_ONLY`:

- go alla curation di dossier ufficiali e versionati;
- no-go alla popolazione completa del corpus;
- no-go a nuove label, candidati, ranking o promozioni;
- prossimo passo: E14.4, contratto per detector ed evidenza mechanism-specific.

L'exit code 3 del comando rappresenta il no-go alla popolazione, non un errore
tecnico.

## Identita' degli artefatti

- source catalog SHA-256:
  `e2da8ce5dfacb144871d9d152d2114a30ba4b16adea938a96fabc05031b69271`;
- feasibility contract SHA-256:
  `9c14041307a1839d69537fa4ac7b170fdca08ab5bf77a64bc7e9ffc3110ab158`;
- report SHA-256:
  `923020a3b3aea552f1bb4737ec1e724891f991c1ad9b8c433d297560b4b93f00`.

## Verifica

- test mirati E14.3: 2/2 superati;
- `dotnet test MacroRegime.slnx --no-restore`: 240/240 test superati;
- `python -m unittest discover -s tests -v`: 58/58 test superati;
- `python -m compileall -q regime_eval tests`: superato;
- report deterministico e write-once;
- dataset non letto e zero righe outer utilizzate;
- zero label scritte e zero candidati generati;
- rifiuto automatico di un indice ricostruito promosso a feature pilot.
