# Checkpoint 0090 - E14.6h no-go diagnostic

Data: 2026-07-15

## Obiettivo

Spiegare il no-go E14.6g per gate, episodio, profilo e persistenza senza
ritoccare soglie, rilassare gate o rieseguire candidati.

## Realizzato

- aggiunti schema e contratto hash-bound del diagnostico;
- aggiunto il comando `e14-diagnose-loeo-no-go`;
- aggregati fallimenti gate complessivi e per meccanismo;
- calcolati hit rate e recall per ogni episodio attraverso tutti i candidati;
- confrontati profili informativi e combinazioni entry/recovery;
- congelata una conclusione per meccanismo e una decisione globale di
  governance.

## Evidenza

- candidati e fold letti dal report immutabile: 28 e 140;
- worst episode recall: zero per tutti i candidati;
- fallimenti hard-negative alert gate: 0;
- fallimenti threshold range gate: 0;
- banking: euro-sovereign-stress-2011 mancato da tutti;
- broad: mancati 5 episodi su 6; solo russia-ltcm-1998 ha almeno un hit;
- cross-border: mancati china-eme, russia-ltcm e taper-tantrum;
- funding: mancati regional-bank, repo-stress e russia-ltcm;
- SHA-256 diagnostico:
  `0f491c7882a95b5d801e0f64d1981219c0407f6076f2ea3be43f30d0b6f2fa78`.

## Decisione

La famiglia candidata v2 e' esaurita sotto il protocollo congelato e viene
chiusa con no-go. L'evidenza non giustifica retuning, rilassamento gate o
ranking rescue. Giustifica invece il design di una nuova ipotesi informativa:

- banking: firme complementari di solvibilita', deterioramento credito e
  intensita' evento oltre il solo conteggio/asset FDIC;
- broad: breadth, liquidita' e price dislocation oltre VIX/BAA10Y;
- cross-border: domanda estera, funding e dislocazione FX congiunti;
- funding: spread di funding e market-function al posto del solo livello
  Fed funds meno T-bill.

E14.7 puo' soltanto preregistrare queste famiglie, le firme attese per episodio,
le direzioni, le trasformazioni e le ablation. Taxonomy, materializzazione dati,
generation, fitting, evaluation, ranking, composizione e outer OOS restano
chiusi.

## Verifiche

- test mirati E14.6h: 3/3;
- regressione Python: 139/139;
- `compileall`: superato;
- test .NET: superati;
- source hash, input hash e diff check: superati;
- righe outer usate: 0.
