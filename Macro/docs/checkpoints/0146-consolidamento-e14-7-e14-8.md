# Checkpoint 0146 - Consolidamento E14.7-E14.8

Data: 2026-07-17

## Esito

Il perimetro tecnico delle fasi E14.7 ed E14.8 e' consolidato. La catena dei
checkpoint 0122-0145 e' coerente, i contratti e gli artefatti JSON sono validi,
le suite C# e Python sono verdi e i confini fail-closed restano invariati.

Il consolidamento non abilita nuove capacita'. E14.7 resta chiusa come
`safely blocked`; E14.8 resta `design-complete` e `safely blocked`. Non sono
stati selezionati provider, create credenziali o risorse, implementati adapter
production, effettuati accessi di rete, pubblicati target o aperti downstream.

## Perimetro consolidato

- 24 checkpoint, dal 0122 al 0145;
- 146 file di implementazione, test, modelli e storia documentale nel payload
  consolidato, escluso questo checkpoint e i tre manuali indicati sotto;
- 235 documenti JSON E14 verificati nel complesso tra modelli ed evidenze;
- 32 evidenze locali della catena E14.7ae-E14.8, conservate sotto
  `data/historical-real-v12-2008-2025/challengers/` secondo la convenzione
  esistente che esclude `data/` dal versionamento Git.

I documenti `readme.md`, `istructions.md` e
`piano_consigliato_finoalcutoff.md` sono deliberatamente esclusi dal payload
tecnico: restano deliverable documentali separati e non modificano i contratti
E14.

## Verifiche eseguite

- `dotnet restore MacroRegime.slnx`: completato;
- `dotnet build MacroRegime.slnx --configuration Release --no-restore`:
  completato con 0 warning e 0 errori;
- `dotnet test MacroRegime.slnx --configuration Release --no-restore --no-build`:
  240 test superati, 0 falliti;
- `python -m compileall -q regime_eval tests`: completato;
- `python -m unittest discover -s tests -q`: 413 test superati, 0 falliti;
- parsing di 235 file JSON E14: 235 validi, 0 invalidi;
- `git diff --check -- Macro`: nessun errore di whitespace.

Totale suite automatiche: 653 test superati, 0 falliti.

## Integrita' e riproducibilita'

Gli hash aggregati sono calcolati ordinando i file per percorso relativo e
costruendo per ciascuno la riga `<percorso>\\t<SHA-256-file>`, codificata UTF-8,
con terminatore LF. L'hash SHA-256 e' quindi calcolato sull'intero elenco con
LF finale.

- payload versionabile consolidato, escluso questo checkpoint:
  `03052748e239cca4712947b05e401c2aa0fe71155c7ed9b535ca7432acba81f0`;
- 32 evidenze locali E14.7ae-E14.8:
  `df709ac5a64174bbe3054668a3d529560b2463bf43137c3c045c1d02798e3285`;
- guard aggregate baseline/E9:
  `39a7a037559820157f30354ddca7bd94a802771d056439b3b7b20fe510b2997f`.

Guard individuali rimaste immutate:

- `research/regime-eval/models/baseline-v1-4-preregistered.json`:
  `eb8da8dd1a29bc3fa23e94498d2576b8f9a2567d232fea663b583ba2e3b7cc70`;
- `research/regime-eval/regime_eval/shadow_ops.py`:
  `8b847e18d5c55f944ed75b7cc2b497807131819a4b303aa51981c7f97ab9011e`;
- `research/regime-eval/regime_eval/shadow_orchestrator.py`:
  `56363fe3358cd06f1f89dc7f37e9cec561b2eedc56a305eff3f669872ddfb818`.

Non risultano modifiche nel runtime `src/`, nei test di dominio, nella baseline
v1.4 o nei due moduli E9 protetti dagli hash sopra.

## Evidenze locali e limite operativo

Le 32 evidenze locali non sono incluse nel repository perche' `data/` e'
ignorata intenzionalmente. L'hash aggregato ne identifica esattamente il set
verificato, ma non ne costituisce una copia: prima di cambiare macchina o
ripulire il workspace deve essere mantenuto un backup del dataset locale.

Questo checkpoint non modifica la policy dati, non autorizza l'inclusione di
raw data in Git e non sostituisce una futura decisione esplicita su storage,
retention e distribuzione degli artefatti di evidenza.

## Stato finale

`CONSOLIDATED_READY_FOR_COMMIT`

Il perimetro e' pronto per un commit tecnico dedicato. Il commit non viene
creato da questo checkpoint e dovra' escludere i tre manuali separati, salvo
successiva indicazione esplicita.
