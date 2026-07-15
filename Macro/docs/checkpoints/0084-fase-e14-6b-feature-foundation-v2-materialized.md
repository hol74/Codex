# Checkpoint 0084 - E14.6b feature foundation v2 materialized

Data: 2026-07-15

## Obiettivo

Scaricare e congelare le tre fonti preregistrate in E14.6a, materializzare una
foundation v2 separata e verificare sui dati reali copertura, missingness, zeri
osservati e confini metodologici, senza aprire candidate generation o fitting.

## Snapshot congelati

| Fonte | File | SHA-256 |
| --- | --- | --- |
| FDIC BankFind failures/assistance API | `fdic-failures-assistance.json` | `7fcc4440ed6341413e5f007f64e0ced9c5966c6b60d93e380712ac5c6a8fa9f7` |
| FRED `TWEXBMTH` | `fred-twexbmth.csv` | `d6def672e0087f56907bbd2bdf76379310a9b17c0d09b223d01c97bd87e4e1a2` |
| FRED `TB3SMFFM` | `fred-tb3smffm.csv` | `4f364347223adf81281b1183edb4dc795df784b04477be3adf557d7ceb4b5778` |

Il cutoff resta 2025-12-31. Due record FDIC e sei mesi `TB3SMFFM` successivi al
cutoff presenti negli snapshot correnti non entrano nella foundation.

## Materializzazione

La foundation v2 contiene cinque serie attive:

| Serie | Osservazioni | Missing | Copertura |
| --- | ---: | ---: | --- |
| VIX massimo mensile, carry-forward v1 | 432 | 0 | 1990-01 / 2025-12 |
| BAA10Y massimo mensile, carry-forward v1 | 480 | 0 | 1986-01 / 2025-12 |
| FDIC failed/assisted assets mensili | 1.104 | 69 | 1934-01 / 2025-12 |
| `TWEXBMTH` variazione assoluta mensile | 563 | 0 | 1973-02 / 2019-12 |
| Fed funds meno T-bill | 858 | 0 | 1954-07 / 2025-12 |

Foundation v1 non e' stata modificata. I suoi due binding broad-market sono
riportati per contenuto esatto; i quattro binding v1 dei tre meccanismi
bloccati sono marcati come ritirati e sostituiti da tre binding v2.

## Missingness e zeri FDIC

L'API dichiara 4.115 record e ne sono stati scaricati 4.115, senza ID duplicati.
Prima del cutoff ricadono 4.113 record. In 154 transazioni, distribuite su 69
mesi e con ultima data 1981-11-20, `QBFASSET` manca: l'intero mese resta missing
anche se contiene altre transazioni valorizzate. I 556 mesi senza alcuna
transazione sono invece zeri osservati solo perche' l'inventario API completo
e' stato verificato. Non e' stata applicata imputazione a zero.

## Copertura strutturale reale

Applicando 60 mesi di storia, missingness interna e intersezione delle serie:

| Meccanismo | Positivi osservabili | Hard negative osservabili |
| --- | ---: | ---: |
| banking-credit | 3 | 2 |
| broad-market-repricing | 6 | 2 |
| cross-border-growth | 5 | 2 |
| funding-liquidity | 3 | 2 |

La riparazione strutturale prevista da E14.6a e' quindi confermata sui dati
materializzati.

## Diagnostiche metodologiche e revisioni

- `TWEXBMTH` termina a dicembre 2019 e non viene collegata a un successore.
- `TB3SMFFM` ha 774 mesi prima del confine 2019 e 84 dopo; le statistiche dei
  due segmenti sono congelate, ma non si afferma equivalenza distributiva. La
  futura evaluation inner deve riportare risultati con e senza il segmento
  post-2018.
- le tre fonti restano snapshot current-history. Non erano preregistrati
  snapshot point-in-time precedenti con cui misurare revisioni storiche; per
  questo `strictVintageReady` resta falso e il limite e' vincolante.

## Esito

Stato:
`FEATURE_FOUNDATION_V2_MATERIALIZED_RESEARCH_ONLY_REVISION_LIMITATIONS_CANDIDATE_GENERATION_CLOSED`.

- foundation v2 materializzata: si';
- foundation v1 mutata: no;
- copertura strutturale riparata: si';
- strict vintage: no;
- candidate generation, fitting, evaluation, outer OOS e promozione: no.

Foundation SHA-256:
`c069de82199f203786c405ef65c559f232f92053d47a8da4280cfde2b14f3127`.

Lock SHA-256:
`110cec532fa0a479a975c36d927f36a08bf8daa4e53dafd598b8c5306fcecf85`.

Audit SHA-256:
`9940caae99522c994ec6ae5405af5b173fb2b75ca980195ecc90d707d9ded735`.

## Verifiche

- test mirati E14.6b: 3/3;
- suite Python completa: 120/120;
- output deterministico e write-once verificato;
- tampering di snapshot e riapertura della mutazione v1 respinti.

## Prossimo passo

E14.6c deve costruire un readiness gate v2 hash-bound sulla foundation reale,
rieseguire l'eleggibilita' dei 28 candidati previsti e congelare la sensitivity
policy 2019. Puo' autorizzare solo la successiva versione del protocollo e del
manifest; fitting, evaluation e outer OOS restano separati.
