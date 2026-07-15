# Checkpoint 0085 - E14.6c readiness v2 passed

Data: 2026-07-15

## Obiettivo

Rieseguire il gate strutturale sui dati reali di foundation v2, includendo
missingness interna e disponibilita' mensile, e congelare il passaggio dai 40
candidati v1 a un roster v2 di 28 ingressi senza generare o fittare modelli.

## Regole applicate

- almeno 60 osservazioni non-missing prima della prima scoring row eleggibile;
- lag di disponibilita' derivato da `period` e `availableOn` della foundation;
- nessun carry attraverso un calendar slot esplicitamente missing;
- una scoring row comune a tutte le serie del profilo dentro l'episodio;
- almeno tre episodi positivi e due hard negative per meccanismo;
- nessun carry oltre il termine metodologico e nessun uso di mesi unlabeled
  come negativi.

I lag osservati sono zero mesi per VIX, BAA10Y e FDIC e un mese per
`TWEXBMTH` e Fed funds meno T-bill. Le prime scoring row mature sono
rispettivamente 1994-12, 1990-12, 1944-05, 1978-02 e 1959-07.

## Transizione degli ID

| Meccanismo | Ingressi | Origine |
| --- | ---: | --- |
| broad-market-repricing | 16 | ID v1 preservati esattamente |
| banking-credit | 4 | nuovi ID readiness v2 |
| cross-border-growth | 4 | nuovi ID readiness v2 |
| funding-liquidity | 4 | nuovi ID readiness v2 |

I 24 ID v1 non-broad sono ritirati e non possono essere riusati. I 12 nuovi
ID contengono il namespace `-v2-`, sono univoci e hanno lifecycle
`readiness-planned-not-generated-not-fit`. Il roster non e' un manifest di
candidati generati.

## Copertura reale

| Meccanismo | Positivi | Hard negative | Ingressi eleggibili |
| --- | ---: | ---: | ---: |
| banking-credit | 3 | 2 | 4/4 |
| broad-market-repricing | 6 | 2 | 16/16 |
| cross-border-growth | 5 | 2 | 4/4 |
| funding-liquidity | 3 | 2 | 4/4 |

La readiness completa a quattro meccanismi e' quindi confermata anche con i
vincoli temporali piu' rigorosi di E14.6c.

## Sensitivity funding 2019

Il confine resta 2019-01-01. La futura evaluation inner deve riportare:

- soglie q80/q90/q95 full contro training pre-2019;
- shift delle soglie normalizzato per IQR pre-2019;
- alert rate prima e dopo il confine;
- metriche per episodi pre e post confine;
- insufficienza dei positivi nel solo tratto pre-2019.

Il tratto pre-2019 contiene un solo episodio funding positivo e non puo'
diventare un gate di eleggibilita' alternativo. L'assenza del sensitivity
report blocchera' il ranking futuro. Non si afferma equivalenza distributiva.

## Esito

Stato:
`FOUR_DETECTOR_READINESS_V2_PASSED_PROTOCOL_V2_DESIGN_AUTHORIZED_FITTING_CLOSED`.

- readiness a quattro meccanismi: superata;
- progettazione protocollo v2: autorizzata;
- candidate manifest generation: non autorizzata;
- fitting, evaluation, ranking e composizione: non autorizzati;
- outer OOS e promozione: non autorizzati;
- strict vintage: falso.

Roster SHA-256:
`82f556f92fbdf0967b4b7c43c0edf75c59d165e7c3b0beab1b88529b1331105d`.

Audit SHA-256:
`e297db22a11903294fb6c27af65711a77762ffe50e87b67ef4fbbbe16c5e497e`.

## Verifiche

- test mirati E14.6c: 3/3;
- suite Python completa: 123/123;
- determinismo e write-once verificati;
- riapertura della generation e riuso degli ID ritirati respinti;
- outer feature row usate: 0.

## Prossimo passo

E14.6d deve congelare il protocollo v2 sui 28 ID del roster, incorporando le
regole temporali e la sensitivity 2019. Potra' autorizzare soltanto la futura
materializzazione del manifest v2, non fitting o evaluation.
