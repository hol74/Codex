# Framework Macro Tattico (FMT)
*Documento operativo — Allocazione tattica basata su regimi macroeconomici*

---

| | |
|---|---|
| **Versione** | 1.0 |
| **Data di redazione** | 2025 |
| **Documento parent** | Investment Policy Statement v1.0 |
| **Prossima revisione** | I trimestre 2026 |

> *Il presente documento è il Framework Macro Tattico (FMT) richiamato alla Sezione 5.10 dell'IPS. Opera esclusivamente entro le bande di tolleranza definite alla Sezione 5.8 dell'IPS e non costituisce modifica del documento di governance principale. Le letture di regime e i tilt attivati sono documentati nel registro delle decisioni dell'IPS.*

---

## Sezione 1 — Scopo e principi del FMT

**1.1 Funzione del documento.** Il FMT disciplina le inclinazioni tattiche del portafoglio rispetto ai pesi target strategici definiti nella Sezione 5.3 dell'IPS. Il suo obiettivo non è produrre rendimento aggiuntivo attraverso il market timing, bensì rendere il portafoglio più robusto nei diversi scenari macroeconomici che il Sottoscrittore incontrerà nel corso dell'orizzonte di investimento.

**1.2 Rapporto con l'IPS.** Il FMT è subordinato all'IPS sotto ogni aspetto: non introduce strumenti non ammessi dalla Sezione 4, non viola le bande di tolleranza della Sezione 5.8, non sostituisce la revisione annuale prevista dalla Sezione 6.4. I tilt tattici sono variazioni di peso all'interno dei range già previsti dall'IPS, non deroghe alle sue regole.

**1.3 Principio di umiltà.** Il FMT riconosce esplicitamente che l'identificazione del regime corrente è sempre incerta. In presenza di segnali ambigui, di Composite Regime Score (CRS) in zona intermedia o di bassa convinzione, il portafoglio torna automaticamente ai pesi target strategici senza applicare alcun tilt. Il default del sistema è l'allocazione strategica, non il tilt tattico.

**1.4 Principio di asimmetria del costo degli errori.** Un errore di identificazione del regime in regime favorevole (tilt inutile) ha costo contenuto: il portafoglio strategico è già costruito per performare in quel contesto. Un errore in regime avverso severo (mancata protezione) ha costo elevato e può richiedere liquidazioni forzate incompatibili con la Sezione 2.5 dell'IPS. Il sistema è quindi calibrato per essere conservativo: meglio un falso negativo che un falso positivo.

---

## Sezione 2 — Il sistema di riconoscimento del regime

**2.1 Framework teorico.** Il FMT adotta il modello a quattro quadranti crescita/inflazione come struttura di riferimento primaria, integrata con le dimensioni della politica monetaria e delle condizioni finanziarie. I quattro regimi fondamentali — Goldilocks, Reflazione, Stagflazione, Deflazione/Bust — sono arricchiti da regimi ibridi rilevanti per il contesto attuale: ZIRP/QE e Repressione Finanziaria.

**2.2 Il Composite Regime Score (CRS).** Il CRS è un indicatore continuo compreso tra 0 e 1 che aggrega segnali macro e cross-asset tramite min-max normalizzazione su finestra storica mobile. È costruito su quattro sub-indici con i seguenti pesi:

| Sub-indice | Peso | Componenti principali |
|---|---|---|
| GrowthScore | 30% | ISM PMI, LEI (Δ6m), Credit Impulse, NFP 3mMA |
| Cross-Asset / InflationScore | 25% | Copper/Gold, XLY/XLP, TIP/IEF, Oil/Gold |
| Fixed Income Score | 25% | Yield Spread 10Y−2Y, LQD/IEF, JNK/LQD |
| Credito/FCI / MonetaryScore | 15% | HY OAS (inv.), NFCI (inv.), DXY (inv.), Fed Funds impliciti |
| Sentiment | 5% | VIX (inv.), Put/Call 21dMA (inv.) |

La formula di ranking applicata a ciascun indicatore è la min-max normalizzazione su finestra lookback di 5 anni (260 settimane) o 10 anni a seconda dell'indicatore. Un rank vicino a **1.0** segnala condizioni espansive/inflazionistiche/risk-on; vicino a **0.0** segnala condizioni recessivo/deflazionistiche/risk-off.

**2.3 I quattro sub-indici e la loro lettura combinata.**

```
GrowthScore = Rank(ISM)·0.30 + Rank(LEI_Δ)·0.25 + Rank(CreditImpulse)·0.25 + Rank(NFP)·0.20

InflationScore = Rank(TIP/IEF)·0.30 + Rank(Oil/Au)·0.25 + Rank(M2_yoy)·0.25 + Rank(Cu/Au)·0.20

RiskScore = (1−Rank(HY_spread))·0.30 + Rank(XLY/XLP)·0.25 + Rank(JNK/LQD)·0.25 + (1−Rank(VIX))·0.20

MonetaryScore = (1−Rank(FFR−Taylor))·0.40 + (1−Rank(DXY))·0.30 + Rank(Yield_Spread_10−2)·0.30
```

I sub-indici sono lo strumento primario di classificazione del regime specifico; il CRS aggregato è utile per una vista sintetica e per il tracking della transizione.

**2.4 Identificazione del regime.** La matrice seguente mappa le combinazioni di sub-indici ai regimi macroeconomici rilevanti per il portafoglio:

| Regime | GrowthScore | InflationScore | RiskScore | MonetaryScore | CRS tipico |
|---|---|---|---|---|---|
| Goldilocks | > 0.60 | 0.30 – 0.55 | > 0.65 | > 0.55 | 0.55 – 0.70 |
| Reflazione | > 0.55 | > 0.60 | > 0.55 | 0.40 – 0.65 | 0.65 – 0.82 |
| Stagflazione | < 0.45 | > 0.65 | < 0.40 | < 0.40 | 0.40 – 0.60 |
| Deflazione / Bust | < 0.30 | < 0.35 | < 0.25 | variabile | 0.05 – 0.30 |
| ZIRP / QE | 0.30 – 0.55 | < 0.35 | > 0.70 | < 0.30 | 0.45 – 0.65 |
| Repressione Finanziaria | 0.40 – 0.60 | > 0.55 | > 0.60 | < 0.25 | 0.50 – 0.70 |

> *I confini sono orientativi. I regimi sono zone di densità probabilistica, non stati discreti. In presenza di segnali ibridi o di un CRS in zona intermedia, il portafoglio torna ai pesi target strategici.*

**2.5 Segnali di transizione.** Il sistema rileva una transizione imminente o in corso in presenza di uno o più dei seguenti segnali:

- *Segnale primario:* CRS attraversa soglie critiche (0.25, 0.45, 0.65, 0.80) con momentum sostenuto per 4+ settimane consecutive.
- *Segnale di divergenza:* GrowthScore e InflationScore si muovono in direzioni opposte per 6+ settimane — possibile stagflazione in formazione.
- *Segnale di velocità:* variazione del CRS superiore a 0.15 in 4 settimane — transizione accelerata, valutare ribilanciamento straordinario.
- *Segnale di conferma:* il CRS concorda con almeno 3 dei 4 sub-indici — affidabilità elevata del segnale.

Tre dei quattro segnali attivi, o un solo segnale di velocità, attivano la valutazione di un tilt tattico secondo la procedura della Sezione 3.

---

## Sezione 3 — I tilt tattici per regime

**3.1 Principio di costruzione dei tilt.** I tilt sono variazioni di peso all'interno delle bande di tolleranza dell'IPS (Sezione 5.8). Nessun tilt può portare una componente al di fuori delle bande. I tilt non implicano vendita di strumenti: sono realizzati prevalentemente dirottando i versamenti mensili verso le componenti da sovrappesare e posticipando gli acquisti nelle componenti da sottopesare. Un acquisto diretto o una vendita esplicita a scopo di tilt è ammessa solo in presenza di un segnale di alta convinzione (tre o più segnali di transizione attivi).

**3.2 Pesi target strategici e bande di tolleranza (riepilogo dall'IPS).**

| Componente | Peso target | Banda minima | Banda massima |
|---|---|---|---|
| Componente difensiva totale | 35% | 30% | 40% |
| — DBMFE (Managed Futures) | 15% | 10% | 20% |
| — CRRY (Carry/Alt. Risk Premia) | 5% | 3% | 8% |
| — GOLD (Oro) | 5% | 3% | 8% |
| — BOND (Gov. EUR) | 10% | 7% | 15% |
| Equity Complement totale | 10% | 5% | 15% |
| — ZPRV (US Small Cap Value) | 7.5% | — | — |
| — ZPRX (EU Small Cap Value) | 2.5% | — | — |
| Equity Substitute (VWCE) | 55% | 45% | 65% |

**3.3 Tilt per regime: Goldilocks.**

*Segnale di regime:* GrowthScore > 0.60, InflationScore 0.30–0.55, RiskScore > 0.65, CRS 0.55–0.70.

*Interpretazione:* contesto ideale per il portafoglio azionario. La componente difensiva ha rendimento atteso inferiore alla sua media storica in questo regime; la componente azionaria esprime il suo pieno potenziale. Non è necessario alcun intervento: il portafoglio strategico è già costruito per questo scenario.

*Tilt indicativo:* nessuno. Mantenere i pesi target. Se la componente difensiva si è ridotta naturalmente sotto il 33% per l'apprezzamento azionario, il ribilanciamento annuale la riporterà al target senza necessità di anticipo.

*Indicatori di allerta:* XLY/XLP in deterioramento prolungato, Credit Impulse in calo, HY spread in allargamento accelerato — possibile transizione verso Reflazione o inversione del ciclo.

**3.4 Tilt per regime: Reflazione.**

*Segnale di regime:* GrowthScore > 0.55, InflationScore > 0.60, RiskScore > 0.55, CRS 0.65–0.82.

*Interpretazione:* le commodity e gli asset ciclici outperformano. I tassi reali salgono, la duration lunga perde valore. La componente obbligazionaria BOND è sotto pressione se realizzata tramite VGEA (durata media elevata); la ladder 1–5 anni è strutturalmente più resiliente grazie alla durata media di ~3 anni.

*Tilt indicativo:*

| Componente | Pesi target | Tilt reflattivo | Note |
|---|---|---|---|
| DBMFE | 15% | 15%–18% | I managed futures tendono a catturare i trend rialzisti delle commodity |
| CRRY | 5% | 5% | Invariato — il carry funziona in mercati calmi con trend definiti |
| GOLD | 5% | 5%–7% | L'oro beneficia di inflazione ma può ritardare rispetto alle commodity industriali |
| BOND | 10% | 7%–8% | Ridurre moderatamente; privilegiare la ladder rispetto a VGEA |
| ZPRV + ZPRX | 10% | 10%–12% | Small cap value outperforma in regime reflattivo |
| VWCE | 55% | 55%–60% | Mantenere o incrementare leggermente |

*Azione pratica:* dirottare i versamenti mensili verso DBMFE e ZPRV/ZPRX; sospendere temporaneamente i nuovi acquisti di VGEA a favore della ladder con scadenze brevi.

**3.5 Tilt per regime: Stagflazione.**

*Segnale di regime:* GrowthScore < 0.45, InflationScore > 0.65, RiskScore < 0.40, CRS 0.40–0.60.

*Interpretazione:* il regime più difficile per il portafoglio bilanciato. Azioni e obbligazioni perdono simultaneamente in termini reali. Le commodity (oro e petrolio) sono l'unico rifugio. La componente difensiva del portafoglio — in particolare DBMFE e GOLD — è stata progettata esattamente per questo scenario.

*Tilt indicativo:*

| Componente | Peso target | Tilt stagflattivo | Note |
|---|---|---|---|
| DBMFE | 15% | 18%–20% | Massimizzare entro la banda; i managed futures catturano i trend rialzisti delle commodity e ribassisti dell'azionario |
| CRRY | 5% | 3%–4% | Ridurre; il carry soffre in regime di stress e deleveraging |
| GOLD | 5% | 7%–8% | Massimizzare entro la banda |
| BOND | 10% | 10%–12% | Preferire scadenze brevi (ladder 1–2 anni) per ridurre il rischio tasso; evitare VGEA |
| ZPRV + ZPRX | 10% | 7%–9% | Ridurre; il value protegge parzialmente ma lo small cap soffre in recessione |
| VWCE | 55% | 47%–52% | Ridurre verso il minimo della banda |

*Azione pratica:* questo è l'unico regime in cui il FMT autorizza vendite esplicite di componente azionaria per finanziare il tilt verso DBMFE e GOLD, a condizione che siano attivi tre o più segnali di transizione e che il CRS sia inferiore a 0.45 con trend calante per almeno 4 settimane. L'operazione è documentata nel registro delle decisioni con indicazione precisa dei segnali attivi.

> *Nota comportamentale: la stagflazione è il regime in cui la pressione emotiva a "fare qualcosa" è massima. Il tilt verso la difensiva è già incorporato strutturalmente nel portafoglio tramite la presenza di DBMFE e GOLD. Il rischio principale è il sovra-tilt: ridurre l'esposizione azionaria oltre i limiti della banda in un momento di massimo pessimismo, precludendo il recupero quando il regime cambia.*

**3.6 Tilt per regime: Deflazione / Bust.**

*Segnale di regime:* GrowthScore < 0.30, InflationScore < 0.35, RiskScore < 0.25, CRS 0.05–0.30.

*Interpretazione:* crisi sistemica con correlazioni convergenti a 1 su tutti gli asset rischiosi. La componente DBMFE è il principale stabilizzatore del portafoglio: le strategie trend following tendono a generare rendimento positivo nelle crisi prolungate. Le obbligazioni governative a breve termine e il cash diventano asset di riserva preziosi. L'oro mantiene valore come riserva sistemica.

*Tilt indicativo:*

| Componente | Peso target | Tilt deflattivo | Note |
|---|---|---|---|
| DBMFE | 15% | 18%–20% | Massimizzare; è il motore di protezione primario in questo regime |
| CRRY | 5% | 3% | Ridurre al minimo; correlazione con l'azionario in fase di deleveraging acuto |
| GOLD | 5% | 7%–8% | Massimizzare; l'oro in termini nominali tende a tenere nelle crisi deflazionistiche |
| BOND | 10% | 13%–15% | Massimizzare; preferire scadenze brevi (1–3 anni) per evitare rischio credito sovrano periferico |
| ZPRV + ZPRX | 10% | 5%–7% | Ridurre; lo small cap soffre in modo sproporzionato nelle crisi di liquidità |
| VWCE | 55% | 47%–50% | Ridurre verso il minimo della banda |

*Azione pratica:* sospendere i versamenti mensili su ZPRV/ZPRX e CRRY; dirottarli integralmente su BOND (scadenze brevi) e DBMFE. Non vendere VWCE a meno che non si verifichino esigenze straordinarie di liquidità documentate — le fasi di crisi sono quelle in cui le vendite forzate dell'azionario risultano più distruttive per il portafoglio di lungo periodo.

*Trigger di revisione straordinaria dell'IPS:* se il drawdown totale del portafoglio supera il 30%, scatta la revisione obbligatoria prevista dalla Sezione 6.7 dell'IPS. Questa è una soglia di riflessione, non uno stop-loss.

**3.7 Tilt per regime: ZIRP / QE.**

*Segnale di regime:* GrowthScore 0.30–0.55, InflationScore < 0.35, RiskScore > 0.70, MonetaryScore < 0.30, CRS 0.45–0.65.

*Interpretazione:* banche centrali in modalità straordinariamente accomodante. Il "Fed Put" sopprime la volatilità. Le azioni growth e gli asset a lunga duration outperformano. La componente difensiva DBMFE tende a sottoperformare in assenza di trend direzionali sostenuti.

*Tilt indicativo:*

| Componente | Peso target | Tilt ZIRP | Note |
|---|---|---|---|
| DBMFE | 15% | 11%–13% | Ridurre; i managed futures soffrono in mercati a bassa volatilità e senza trend |
| CRRY | 5% | 6%–7% | Incrementare leggermente; il carry beneficia di spread stabili e bassa vol |
| GOLD | 5% | 6%–7% | L'oro in regime ZIRP con tassi reali negativi tende a performare bene |
| BOND | 10% | 8%–9% | Ridurre; le obbligazioni hanno rendimento atteso molto basso in questo regime |
| ZPRV + ZPRX | 10% | 8%–9% | Ridurre leggermente; in ZIRP il mercato premia il growth rispetto al value |
| VWCE | 55% | 58%–62% | Incrementare verso la banda massima |

*Azione pratica:* in questo regime il rischio principale è la complacency — la soppressione artificiale della volatilità non elimina il rischio sottostante ma lo accumula. Non ridurre la componente DBMFE al di sotto del 10% della banda: è l'assicurazione contro il "Minsky moment" che tipicamente chiude questo regime.

**3.8 Regime ambiguo o di transizione.**

Quando il CRS si trova in zona intermedia (0.40–0.60) con sub-indici discordanti, o quando il momentum del CRS è inferiore a 0.05 nelle ultime 4 settimane, il sistema è in stato di incertezza. In questo caso il portafoglio rimane ai pesi target strategici. Non è ammessa l'applicazione di un tilt basato su previsioni narrative o su raccomandazioni esterne: il segnale quantitativo deve essere chiaro prima di qualsiasi azione tattica.

---

## Sezione 4 — Procedura operativa

**4.1 Frequenza di aggiornamento del CRS.** Il CRS è aggiornato con cadenza settimanale ogni lunedì, utilizzando le chiusure dei mercati del venerdì precedente per i dati ad alta frequenza (ratio cross-asset, spread, VIX, futures). I dati macro mensili (ISM, LEI, Credit Impulse, NFP) sono integrati alla prima disponibilità e richiedono il ricalcolo dei rank su finestra mobile.

**4.2 Procedura settimanale (60–90 minuti ogni lunedì).**

1. Aggiornare i dati ad alta frequenza: VIX e term structure, Put/Call ratio, Copper/Gold, XLY/XLP, JNK/LQD, Yield Spread 2Y–10Y, DXY, Fed Funds Futures 12m.
2. Applicare la formula min-max a ciascun indicatore sulla finestra lookback prescritta.
3. Calcolare i quattro sub-indici e il CRS aggregato. Verificare che tutti i rank siano nell'intervallo [0,1] e che la somma dei pesi sia 1.00.
4. Confrontare il CRS con le soglie critiche (0.25, 0.45, 0.65, 0.80) e calcolare la variazione nelle ultime 4, 8 e 13 settimane.
5. Classificare il regime corrente tramite la matrice della Sezione 2.4. Documentare la classificazione con data e valori dei sub-indici.
6. Verificare se il posizionamento corrente del portafoglio è coerente con il regime identificato. Se la deviazione supera 5 punti percentuali su una componente, pianificare l'azione nelle prossime settimane (non necessariamente immediata).

**4.3 Procedura mensile (aggiuntiva).**

Una volta al mese, in occasione dell'uscita dei principali dati macro: integrare ISM PMI, Conference Board LEI, Credit Impulse, NFP nel dataset. Costruire lo scenario tree mensile: scenario base (50–60%), scenario ottimista (20–25%), scenario pessimista (15–25%), ciascuno con CRS atteso e risposta di portafoglio predefinita. Documentare nel registro delle decisioni.

**4.4 Soglie di azione.** Il FMT opera secondo un principio di gradualità:

- *CRS stabile, regime confermato da 4+ settimane:* nessuna azione necessaria. Il portafoglio è già correttamente posizionato.
- *Segnale di transizione (1–2 segnali attivi):* dirottare i versamenti mensili verso le componenti coerenti con il regime emergente. Nessuna vendita.
- *Transizione confermata (3+ segnali attivi, CRS ha attraversato una soglia critica):* ribilanciamento attivo tramite versamenti e, se necessario, acquisti mirati. Vendite esplicite solo in caso di tilt stagflattivo o deflattivo con CRS < 0.30.
- *Transizione accelerata (Δ CRS > 0.15 in 4 settimane):* valutare ribilanciamento immediato. Applicare la regola delle 48 ore della Sezione 6.2 dell'IPS per qualsiasi operazione straordinaria.

**4.5 Stack tecnologico minimo.** Il sistema è implementabile con strumenti gratuiti o a basso costo:

| Strumento | Utilizzo |
|---|---|
| FRED API | Dati macro gratuiti: ISM, LEI, Treasury yields, M2, Credit Impulse |
| Yahoo Finance / yfinance | Dati di mercato giornalieri: ETF ratio, VIX, futures |
| Google Sheets / Excel | Dashboard manuale con formule MINIFS/MAXIFS per min-max rank |
| CFTC.gov | COT Report gratuito ogni venerdì (posizionamento asset manager) |

*Formula Excel per min-max rank su finestra 5 anni (1825 giorni):*
```
=(B2−MINIFS(B:B,A:A,">="&A2-1825))/(MAXIFS(B:B,A:A,">="&A2-1825)−MINIFS(B:B,A:A,">="&A2-1825))
```
Per indicatori con polarità inversa (VIX, HY spread, DXY): `=1−formula_sopra`

---

## Sezione 5 — Implicazioni per gli strumenti specifici del portafoglio

**5.1 DBMFE nei diversi regimi.** DBMFE è il cuore della componente difensiva e il suo comportamento varia significativamente per regime. In Goldilocks e ZIRP (mercati poco direzionali, bassa volatilità) tende a produrre rendimento contenuto o leggermente negativo — questo è il "costo dell'assicurazione". In Reflazione (trend commodity chiari) e in Stagflazione/Deflazione (trend azionari ribassisti sostenuti) è atteso un contributo positivo. Il Sottoscrittore accetta strutturalmente la sottoperformance di DBMFE nei regimi favorevoli come condizione necessaria della sua protezione nei regimi avversi.

**5.2 GOLD nei diversi regimi.** L'oro è l'asset con il comportamento più robusto in un numero elevato di scenari avversi: Stagflazione, Deflazione, Repressione Finanziaria, crisi geopolitiche. Il suo limite è il costo opportunità in regime Goldilocks (nessun reddito corrente, crescita zero). Il peso contenuto del 5% riflette questo trade-off: abbastanza per avere un impatto significativo nei momenti critici, non abbastanza da penalizzare il portafoglio nei lunghi periodi di calma.

**5.3 BOND nei diversi regimi.** La componente obbligazionaria è quella con maggiore flessibilità implementativa. Il FMT raccomanda di privilegiare la ladder diretta (scadenze 1–5 anni) rispetto a VGEA nelle fasi di regime inflattivo o stagflattivo, per ridurre l'esposizione alla duration. In regime Goldilocks o Deflazione, VGEA con duration più lunga può essere più efficiente per catturare l'apprezzamento obbligazionario. La scelta tra le due modalità è una decisione operativa del FMT, non dell'IPS, e non richiede revisione formale.

**5.4 ZPRV e ZPRX nei diversi regimi.** I fattori size e value mostrano la loro ciclicità nei diversi regimi: outperformano in regime reflattivo e late cycle, sottoperformano in Goldilocks dominato da growth e in ZIRP. Il Sottoscrittore si impegna a mantenere l'esposizione fattoriale per l'intero orizzonte indipendentemente dalla performance di breve periodo, coerentemente con la Sezione 5.5 dell'IPS. I tilt sul peso di ZPRV/ZPRX sono limitati a ±3 punti percentuali rispetto al target e non costituiscono rinuncia al premio fattoriale.

**5.5 CRRY nei diversi regimi.** CRRY è lo strumento con il comportamento meno prevedibile in condizioni di stress. Il FMT tratta CRRY con il peso più contenuto (5%) e lo riduce ulteriormente (fino a 3%) in tutti i regimi caratterizzati da RiskScore < 0.40, ovvero nei contesti in cui il deleveraging rapido può causare la correlazione temporanea con l'azionario descritta nella Sezione 5.4 dell'IPS.

---

## Sezione 6 — Governance del FMT

**6.1 Documentazione delle letture di regime.** Ogni lettura settimanale del CRS è registrata in un foglio di monitoraggio dedicato con data, valori dei quattro sub-indici, CRS aggregato e classificazione del regime. Le letture che attivano una variazione di tilt sono marcate e riportate nel registro delle decisioni dell'IPS con la motivazione e l'azione intrapresa.

**6.2 Limiti di revisione del FMT.** Il FMT è un documento operativo che può essere aggiornato dal Sottoscrittore senza revisione formale dell'IPS, purché le modifiche non alterino i pesi target strategici, le bande di tolleranza, gli strumenti ammissibili o i vincoli della Sezione 4 dell'IPS. Modifiche alla struttura del CRS, ai pesi dei sub-indici o agli indicatori utilizzati sono documentate con data e motivazione nella sezione 8.3.

**6.3 Guardrail comportamentali specifici del FMT.** In aggiunta ai guardrail della Sezione 7.7 dell'IPS, il Sottoscrittore si impone le seguenti regole nell'utilizzo del FMT:

Non attivare un tilt tattico basandosi su un singolo indicatore o su una singola settimana di dati, indipendentemente dall'intensità del segnale. Il CRS deve mostrare un segnale sostenuto per almeno 4 settimane prima di qualsiasi azione.

Non mantenere un tilt tattico dopo che i segnali che lo hanno attivato si sono dissipati. Il portafoglio torna ai pesi target strategici entro due cicli di versamento mensile dalla normalizzazione del CRS.

Non aumentare la frequenza di monitoraggio del CRS oltre il settimanale nelle fasi di volatilità elevata. Il valore del sistema è nella disciplina del processo, non nella reattività alle singole sessioni di mercato.

**6.4 Revisione annuale del FMT.** Il FMT è incluso nell'agenda di revisione annuale dell'IPS prevista dalla Sezione 6.4. In tale sede il Sottoscrittore valuta: la qualità delle letture di regime effettuate nell'anno (confronto ex ante/ex post); l'impatto dei tilt attivati sulla performance rispetto al portafoglio strategico puro; eventuali modifiche agli indicatori o ai pesi del CRS sulla base dell'evidenza accumulata.

---

## Sezione 7 — Sintesi operativa per regime

| Regime | CRS | Azione principale | DBMFE | GOLD | BOND | Equity | Convinzione richiesta |
|---|---|---|---|---|---|---|---|
| Goldilocks | 0.55–0.70 | Nessun tilt | Target | Target | Target | Target | — |
| Reflazione | 0.65–0.82 | Leggero tilt pro-risk | +2/3% | 0/+1% | −2/3% (ladder) | +3/5% | Media |
| Stagflazione | 0.40–0.60 | Tilt difensivo | Max banda | Max banda | Ladder breve | −5/8% | Alta (3+ segnali) |
| Deflazione/Bust | 0.05–0.30 | Protezione massima | Max banda | Max banda | +3/5% (breve) | Min banda | Alta (3+ segnali) |
| ZIRP/QE | 0.45–0.65 | Ridurre DBMFE | −3/4% | +1/2% | −1/2% | +3/5% | Media |
| Ambiguo/Transizione | Intermedio | Nessun tilt | Target | Target | Target | Target | — |

---

## Sezione 8 — Appendici

### 8.1 Glossario integrativo

**CRS (Composite Regime Score)**
Indicatore continuo compreso tra 0 e 1 che aggrega 38 indicatori macro e cross-asset in un unico punteggio di regime. Zero segnala condizioni recessivo/deflazionistiche; 1 segnala condizioni espansive/inflazionistiche. È aggiornato settimanalmente.

**GrowthScore**
Sub-indice del CRS che cattura la forza del ciclo economico reale. Componenti principali: ISM Manufacturing PMI, Conference Board LEI (variazione a 6 mesi), Credit Impulse USA, Nonfarm Payrolls media 3 mesi.

**InflationScore**
Sub-indice del CRS che misura le pressioni inflazionistiche. Componenti principali: TIP/IEF ratio (breakeven inflazione), Oil/Gold ratio, M2 YoY%, Copper/Gold ratio.

**Min-Max Normalizzazione**
Formula universale applicata a ogni indicatore: Rank(x) = (x_t − x_min) / (x_max − x_min), dove min e max sono calcolati sulla finestra lookback di riferimento. Per indicatori con polarità inversa (VIX, spread creditizi, DXY) si applica 1 − Rank(x).

**Minsky Moment**
Il punto di svolta in cui il ciclo del credito si inverte bruscamente: gli investitori liquidano posizioni per coprire le perdite, innescando una spirale ribassista dei prezzi del collaterale. Tipicamente chiude il regime ZIRP/QE e apre un regime di Deflazione/Bust.

**MonetaryScore**
Sub-indice del CRS che cattura la stance della politica monetaria. Componenti principali: Fed Funds Rate rispetto alla Taylor Rule (inv.), DXY (inv.), Yield Spread 10Y−2Y.

**RiskScore**
Sub-indice del CRS che misura l'appetito per il rischio nel sistema finanziario. Componenti principali: HY OAS spread (inv.), XLY/XLP ratio, JNK/LQD ratio, VIX (inv.).

**Tilt**
Variazione del peso di una componente rispetto al peso target strategico dell'IPS, realizzata all'interno delle bande di tolleranza. I tilt sono implementati principalmente attraverso il dirottamento dei versamenti mensili, non attraverso vendite esplicite.

### 8.2 Indicatori e fonti

| Indicatore | Frequenza | Fonte | Lookback |
|---|---|---|---|
| ISM Manufacturing PMI | Mensile | ISM / FRED (NAPM) | 5 anni |
| Conference Board LEI (Δ6m) | Mensile | Conference Board | 5 anni |
| Credit Impulse USA | Mensile | Fed H.8 / calcolo derivato | 10 anni |
| Nonfarm Payrolls 3mMA | Mensile | BLS / FRED | 5 anni |
| Sahm Rule Indicator | Mensile | Fed / BLS | 10 anni |
| Initial Jobless Claims 4wMA | Settimanale | DOL / FRED | 5 anni |
| Copper/Gold Ratio | Giornaliero | Yahoo Finance (HG=F / GC=F) | 5 anni |
| Oil/Gold Ratio | Giornaliero | Yahoo Finance (CL=F / GC=F) | 5 anni |
| XLY/XLP Ratio | Giornaliero | Yahoo Finance | 3 anni |
| XLK/XLU Ratio | Giornaliero | Yahoo Finance | 3 anni |
| IWM/SPY Ratio | Giornaliero | Yahoo Finance | 3 anni |
| Yield Spread 10Y−2Y | Giornaliero | FRED (T10Y2Y) | 10 anni |
| TIP/IEF Ratio | Giornaliero | Yahoo Finance | 5 anni |
| LQD/IEF Ratio | Giornaliero | Yahoo Finance | 5 anni |
| JNK/LQD Ratio | Giornaliero | Yahoo Finance | 5 anni |
| HY OAS Spread | Settimanale | FRED (BAMLH0A0HYM2) | 10 anni |
| NFCI (Chicago Fed) | Settimanale | FRED (NFCI) | 5 anni |
| VIX | Giornaliero | Yahoo Finance (^VIX) | 5 anni |
| VIX Term Structure (VIX3M/VIX) | Giornaliero | CBOE / Yahoo Finance | 3 anni |
| Put/Call Ratio 21dMA | Giornaliero | CBOE | 3 anni |
| DXY | Giornaliero | Yahoo Finance (DX-Y.NYB) | 5 anni |
| Fed Funds Futures 12m | Giornaliero | CME FedWatch | 3 anni |
| M2 YoY% | Mensile | FRED (M2SL) | 5 anni |

### 8.3 Storico delle modifiche al FMT

| Versione | Data | Natura della modifica |
|---|---|---|
| 1.0 | 2025 | Prima stesura |
| | | |
| | | |

### 8.4 Registro delle letture di regime

*Da compilare settimanalmente. Formato minimo: Data — GrowthScore — InflationScore — RiskScore — MonetaryScore — CRS — Regime classificato — Tilt attivo (sì/no) — Azione intrapresa.*

| Data | Growth | Inflation | Risk | Monetary | CRS | Regime | Tilt | Azione |
|---|---|---|---|---|---|---|---|---|
| | | | | | | | | |
| | | | | | | | | |
| | | | | | | | | |
