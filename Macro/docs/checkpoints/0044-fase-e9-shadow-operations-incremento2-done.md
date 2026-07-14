# Macro Regime - Fase E9: Shadow Operations, incremento 2

Data di implementazione: 2026-07-14.

## Esito

E' stato implementato l'orchestratore mensile end-to-end che collega i comandi
C# di population, dataset build ed evaluation v1.4 al preflight e, solo in
modalita' `full`, al freeze del ledger e alla ricostruzione dell'indice.

Il sistema non dipende piu' da una sequenza manuale di cinque comandi. La rete
resta confinata nella population C# Infrastructure e Python non entra nel
runtime applicativo C#.

## Prerequisito Git consolidato

Prima dello sviluppo e' stato congelato E4-E9.1. Un primo checkpoint
`bc549c9` includeva accidentalmente la cartella sorella `Macro - Copia/`; e'
stato sostituito, con autorizzazione esplicita e `force-with-lease`, dal commit
bonificato `52aaef2`. Il nuovo commit contiene soltanto il progetto `Macro/`,
la copia locale e' stata preservata ed e' ora esclusa dalla `.gitignore` della
radice. `main`, `origin/main` e `codex/e9-2` sono stati riallineati.

## Contratto dell'orchestratore

Il nuovo comando `shadow-operations` riceve root sorgenti, root operativa,
model config, timestamp, modalita' e path della receipt. Determina:

- ultimo mese informativo chiuso;
- ultimo cutoff presente nei ledger reali;
- mese immediatamente successivo, senza consentire buchi nella serie.

Se non esiste un mese eleggibile produce una receipt immutabile con stato
`no-eligible-month`, zero comandi e nessun outcome. Non crea directory di ciclo.

## Layout e stati

Per ogni mese eleggibile viene creato:

```text
cycles/yyyy-MM/
  source/macro/
  source/market/
  dataset/
  evaluation/
  preflight/
  logs/
  cycle-state.json
```

`cycle-state.json` e' atomico, aggiornabile e non autorevole. Per ogni comando
registra lista degli argomenti, hash del comando, timestamp, exit code, file di
stdout/stderr e relativi SHA-256. La chiave FRED non viene passata sulla command
line e non entra nello stato.

Gli stati finali sono:

- `prepared`: population, build, evaluation e preflight completati;
- `ledger-frozen`: anche ledger e indice completati;
- `failed`: errore operativo persistito;
- `no-eligible-month`: nessuna operazione necessaria.

## Recovery

Una retry valida gli hash degli artefatti degli step completati e li salta. Se
uno step e' fallito, il ciclo riparte da quello step e conserva tutti i
tentativi precedenti. Un artefatto completato ma assente o modificato blocca la
ripresa. Ledger e preflight non vengono mai sovrascritti.

I test iniettano un errore nel dataset build: population viene eseguita una
sola volta, il secondo tentativo riparte dal build e raggiunge `prepared`.
Un secondo test passa da `prepare-only` a `full` senza richiamare alcun comando
C# gia' completato.

## Smoke reale 2026-07-14

Comando eseguito in modalita' `prepare-only` sulla root
`data/shadow-live-2026/`:

- ultimo ledger: 2026-06-30;
- ultimo mese chiuso: 2026-06-30;
- risultato: `no-eligible-month`;
- comandi eseguiti: 0;
- outcome usati: `false`;
- nessun secondo ledger di giugno e nessuna directory di ciclo.

Receipt locale:
`data/shadow-live-2026/operations-audit/shadow-operations-2026-07-14-prepare-only.json`,
SHA-256 `7a1dd66c7d79e3603f1751df8ba55a13ad7c1f994714796f2959feaedf38578d`.

## Verifiche

- 240 test C# superati;
- 25 test Python superati;
- test su selezione mese, sequenza giugno-luglio, prepare/full e recovery;
- build .NET senza warning o errori;
- `compileall` e `git diff --check` superati;
- nessuna ground truth nei comandi o negli artefatti operativi.

## Stato della fase

E9.2 e' implementata, ma E9 resta operativamente in corso. Il prossimo evento
non e' un nuovo sviluppo o tuning: e' il primo ciclo prospettico `full` sul
cutoff 2026-07-31, dopo la chiusura di luglio e quando gli input richiesti sono
disponibili. Fino ad allora non deve essere creato alcun nuovo ledger.
