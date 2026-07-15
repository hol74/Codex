# Checkpoint 0075 - E14.4g2 targeted expansion accepted

Data: 2026-07-15

## Obiettivo

Correggere esclusivamente i due dossier E14.4g non accettati, preservare i 14
manifest accept e ottenere una nuova decisione indipendente hash-scoped.

## Decisioni di modellizzazione

- Regional-bank stress 2023 resta un hard negative `broad-market-repricing`:
  il problema era il locator IMF, sostituito con il capitolo PDF ufficiale.
- Repo stress 2019 viene ritirato: stabilita' dei repo esteri non dimostra lo
  stato della crescita reale cross-border e non deve essere relabelled.
- Il sostituto e' Flash Crash 2010 `cross-border-growth`: CPB e WTO misurano
  la tenuta del commercio reale, mentre CFTC/SEC preserva il forte shock di
  mercato come counterevidence.

## Due cicli di rereview

Il primo ciclo ha prodotto:

- regional-bank 2023: `accept`;
- Flash Crash 2010: `needs-revision`, perche' il PDF CPB indicizzato
  restituiva HTTP 404 al controllo diretto.

Il gate e' rimasto chiuso. La seconda revisione ha cambiato soltanto l'hash
Flash Crash, usando la pagina CPB live e il download XLS ufficiale. Il reviewer
ha verificato:

- indice world trade aprile 2010: 154,0;
- indice world trade maggio 2010: 157,4;
- variazione mensile implicita: circa +2,2%;
- crescita Q2 implicita: circa +3,4%;
- fonti WTO e CFTC/SEC accessibili e coerenti.

La seconda decisione e' `accept`.

## Esito

- manifest accettati preservati nel primo retry: 14/14;
- manifest accettati preservati nel secondo retry: 15/15;
- queue v11: 16/16 accept;
- eventi hard-negative indipendenti potenziali accettati: 6;
- hard negative per meccanismo: 2;
- stato: `READY_FOR_HARD_NEGATIVE_COVERAGE_GATE`;
- E14.4h autorizzato: si;
- tassonomia aggiornata: no;
- candidate generation, outer OOS e promozione: no.

## Artefatti principali

- pack mirati v1 e v2 in `research/regime-eval/models/`;
- queue v8-v11 e audit mirati in
  `data/historical-real-v12-2008-2025/challengers/`;
- bundle e receipt indipendenti separati per i due cicli;
- moduli `e14_hard_negative_targeted_revision.py` e
  `e14_hard_negative_targeted_review_ingestion.py`;
- comandi CLI dedicati e test retry-safe/immutabili.

Identita' finali:

- queue v11 SHA-256:
  `fb77f001f22d981d42eb29d1fc7e4397bf4a5ebde8729179436aea322516c264`;
- targeted ingestion audit v2 SHA-256:
  `a4d076d1555c412c634ef7f8d63c3cf9b83a4b6d5cabf6a2942108b39b6a80c4`;
- receipt Flash Crash retry SHA-256:
  `d2b09fa7bf607753ddcf06562f8d2d44fe086e1862cd5a0f782a1f2ad816e865`.

## Verifiche

- suite Python completa: 94/94;
- compilazione bytecode: superata;
- test .NET `MacroRegime.slnx`: superati;
- nessuna lettura outer OOS, label scritta, tassonomia mutata o candidato
  generato.

## Prossimo passo

E14.4h deve ricontare la copertura usando soltanto queue v11, receipt accettate
e tassonomia v4 immutata. Anche in caso di successo, l'eventuale merge in una
nuova tassonomia e l'apertura dei candidati restano decisioni separate.
