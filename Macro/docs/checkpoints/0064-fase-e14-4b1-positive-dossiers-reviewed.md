# Checkpoint 0064 - E14.4b1 dossier positivi reviewed

Data: 2026-07-14

## Obiettivo

Curare le cinque ipotesi positive storiche in dossier separati per meccanismo,
usando fonti primarie indipendenti e senza trasformare la revisione iniziale in
una modifica prematura della ground truth.

## Piano eseguito

1. congelare un pack di asserzioni con locator, sintesi, provider e ruolo;
2. coprire esattamente ogni coppia ipotesi-meccanismo del catalogo E14.3;
3. validare narrativa ufficiale, osservazione quantitativa, indipendenza delle
   fonti, controevidenza e confini temporali;
4. generare dossier e audit deterministici, hash-bound e write-once;
5. mantenere ogni dossier nello stato `reviewed` fino alla seconda revisione;
6. lasciare chiusi ground truth, corpus, outer OOS e candidati.

## Realizzato

- curati 8 dossier da 5 ipotesi: 3 broad-market, 1 funding-liquidity, 1
  banking-credit e 3 cross-border-growth;
- collegata ogni asserzione a un digest SHA-256 di locator e sintesi curata;
- manifestati separatamente gli 8 file dossier nell'audit finale;
- verificato che nessun confine ecceda la relativa ipotesi congelata;
- registrata controevidenza per ogni dossier;
- implementate validazioni fail-closed e scrittura immutabile;
- aggiunto il comando CLI `e14-curate-positive-dossiers`;
- aggiunti test di determinismo, write-once e indipendenza dei provider.

## Correzione informativa rilevante

Il catalogo E14.3 associava il VIX all'episodio del 1987, ma la serie storica
indicata inizia nel 1990. Il catalogo congelato non e' stato riscritto: il
dossier del crash usa invece fonti ufficiali Federal Reserve e CFTC e l'audit
espone il mismatch come finding. Il digest certifica l'asserzione locale e il
locator, non una copia immutabile dei byte remoti.

## Esito

Stato: `SECOND_REVIEW_AND_HARD_NEGATIVES_REQUIRED`.

- dossier positivi `reviewed`: 8;
- dossier `accepted`: 0;
- hard negative: 0;
- reviewer indipendenti per dossier: 1;
- righe outer utilizzate: 0;
- label scritte: 0;
- candidati generati: 0.

Il risultato migliora la tracciabilita' della foundation positiva, ma non
sblocca ancora la modellizzazione. E14.4b2 deve svolgere una seconda revisione
indipendente e cercare hard negative con evidenza affermativa di funzionamento
ordinato per singolo meccanismo.

## Identita' degli artefatti

- positive dossier pack SHA-256:
  `a0a12f188ac8540a08e729bf5db5b7077ebf428c6d2b68157e77701c427f7b84`;
- curation audit SHA-256:
  `8ee285e84d5ed5ab78529c4ce3e88b0bb4ff2e835a25edb6a0b3e58bf04d7685`;
- gli hash dei singoli 8 dossier sono inclusi nel curation audit.

## Prossimo passo

E14.4b2: revisione indipendente dei dossier positivi e ricerca/adjudication di
hard negative. Soltanto un successivo label-foundation gate potra' autorizzare
un aggiornamento della ground truth.

## Verifica

- test mirati E14.4b1: 2/2 superati;
- `python -m unittest discover -s tests -v`: 62/62 superati;
- `dotnet test MacroRegime.slnx --no-restore`: 240/240 superati;
- `python -m compileall -q regime_eval tests`: superato;
- seconda generazione in directory temporanee byte-identica;
- riuso dello stesso output rifiutato dal vincolo write-once;
- dossier con provider non indipendenti rifiutato.
