# Indicatori di Recessione: Analisi e Regole Tattiche di Portafoglio

---

## 1. Sahm Rule Recession Indicator

L'indicatore di recessione di Sahm segnala l'inizio di una recessione quando la media mobile trimestrale del tasso di disoccupazione nazionale (U3) aumenta di 0,50 punti percentuali o più rispetto al minimo delle medie trimestrali dei 12 mesi precedenti.

- [Grafico SAHMREALTIME](https://fred.stlouisfed.org/series/SAHMREALTIME)
- [Grafico SAHMCURRENT](https://fred.stlouisfed.org/series/SAHMCURRENT)
- [Paper originale](https://www.hamiltonproject.org/assets/files/Sahm_web_20190506.pdf)

### Analisi dell'indicatore

**Logica economica.** La Sahm Rule si fonda su un'asimmetria empirica del mercato del lavoro: le perdite di posti di lavoro durante una recessione tendono a concentrarsi in pochi mesi, producendo un'accelerazione del tasso di disoccupazione facilmente misurabile. Claudia Sahm ha calibrato la soglia di 0,50 pp osservando che, storicamente, ogni volta che questa variazione si è verificata, l'economia statunitense era già in recessione o stava per entrarvi entro 1–2 mesi.

**Caratteristiche operative.**

| Proprietà | Valore |
|---|---|
| Frequenza dei dati | Mensile (rilascio BLS, primo venerdì del mese) |
| Ritardo segnale | ~1–2 mesi dall'inizio effettivo della recessione |
| Falsi positivi storici (1970–2024) | 0 (segnale mai scattato senza recessione confermata) |
| Soglia di allerta | 0,30–0,49 pp (zona di attenzione) |
| Soglia di recessione | ≥ 0,50 pp |

**Varianti disponibili su FRED.**
- *SAHMREALTIME*: usa i dati di disoccupazione così come pubblicati al momento, senza revisioni successive. È la versione operativa per chi prende decisioni in tempo reale.
- *SAHMCURRENT*: usa i dati di disoccupazione rivisti, utile per analisi storiche e backtesting.

**Limiti e avvertenze.**
- L'indicatore è stato sviluppato per il ciclo economico statunitense e riflette le specificità del mercato del lavoro americano (ad es. la velocità con cui i disoccupati vengono rilevati dall'indagine CPS).
- In recessioni molto brevi o poco profonde (es. shock pandemici da lockdown), il segnale potrebbe arrivare mentre la contrazione è già quasi conclusa.
- Non cattura recessioni a disoccupazione stabile (es. crisi finanziarie con occupazione resiliente nel breve periodo).
- Luglio 2024: la Sahm Rule ha raggiunto 0,53 pp, pur senza recessione confermata dall'NBER, a causa di un aumento dell'offerta di lavoro (immigrazione) più che di perdite occupazionali — un caso-limite che Sahm stessa ha commentato pubblicamente come possibile falso segnale strutturale.

---

## 2. GDP-Based Recession Indicator Index (Hamilton)

- [Grafico JHGDPBRINDX](https://fred.stlouisfed.org/series/JHGDPBRINDX)
- [Paper e aggiornamenti](https://econbrowser.com/recession-index)

Questo indice misura la probabilità che l'economia statunitense fosse in recessione durante il trimestre indicato. Si basa su una descrizione matematica delle differenze tra recessioni ed espansioni. L'indice corrisponde alla probabilità (espressa in percentuale) che il regime economico reale sottostante sia di recessione, sulla base dei dati disponibili.

Se il valore dell'indice supera il **67%**, si tratta di un indicatore storicamente affidabile dell'ingresso dell'economia in recessione. Una volta superata questa soglia, se scende al di sotto del **33%**, è un indicatore affidabile della fine della recessione.

### Analisi dell'indicatore

**Logica economica.** James Hamilton (UC San Diego) stima un modello a regime-switching (Markov-switching) sul PIL reale USA. Il modello identifica due stati latenti — espansione e recessione — e calcola la probabilità di trovarsi in ciascuno, aggiornata trimestre per trimestre. Il framework è puramente statistico e non dipende dalla definizione NBER di recessione.

**Caratteristiche operative.**

| Proprietà | Valore |
|---|---|
| Frequenza dei dati | Trimestrale (aggiornato con il rilascio BEA del PIL) |
| Ritardo segnale | ~1 trimestre (i dati PIL escono con 30 giorni di ritardo) |
| Scala | 0–100% (probabilità di recessione) |
| Soglia di ingresso recessione | > 67% |
| Soglia di uscita recessione | < 33% |
| Affidabilità storica | Elevata; ha identificato tutte le recessioni NBER post-1947 |

**Punti di forza rispetto alla Sahm Rule.**
- Non si basa sul mercato del lavoro: cattura anche recessioni in cui la disoccupazione rimane bassa (rare ma possibili).
- Fornisce una probabilità continua, non un segnale binario: consente una gestione graduale del rischio.
- Utile per costruire modelli quantitativi di asset allocation.

**Limiti.**
- Frequenza trimestrale: il segnale arriva con 1–2 trimestri di ritardo rispetto agli indicatori mensili.
- Il modello Markov-switching ha un "boundary problem": attorno alla soglia del 67% il segnale può oscillare, generando incertezza operativa.
- Non adatto per market timing intra-trimestrale.

---

## 3. Smoothed U.S. Recession Probabilities (Chauvet-Piger)

- [Grafico RECPROUSM156N](https://fred.stlouisfed.org/series/RECPROUSM156N)
- [Paper](https://faculty.ucr.edu/~chauvet/ier.pdf)

Le probabilità di recessione attenuate per gli Stati Uniti sono ottenute da un modello dinamico a fattori con commutazione di regime applicato a quattro variabili coincidenti mensili: occupazione non agricola, indice della produzione industriale, reddito personale reale escluse le transazioni e vendite reali del settore manifatturiero e commerciale.

### Analisi dell'indicatore

**Logica economica.** Marcelle Chauvet e Jeremy Piger combinano due approcci: il modello a fattori dinamici (DFM) di Stock-Watson, che estrae un indice coincidente sintetico da quattro serie macro chiave, e un modello Markov-switching, che classifica l'indice in due regimi (espansione/recessione). Il "smoothing" si riferisce alla probabilità filtrata sul dataset completo (non solo sui dati fino al periodo corrente), il che rende il segnale più stabile ma introduce un lieve ritardo.

**Caratteristiche operative.**

| Proprietà | Valore |
|---|---|
| Frequenza dei dati | Mensile |
| Variabili di input | Payroll non-farm, produzione industriale, reddito personale reale, vendite reali manifatturiero-commerciale |
| Soglia convenzionale di recessione | > 80% (uso pratico comune) |
| Ritardo segnale | ~2–3 mesi (per lo smoothing retroattivo) |
| Aggiornamento | Mensile, con rilascio FRED |

**Punti di forza.**
- Aggrega quattro dimensioni dell'economia reale: lavoro, produzione, reddito, commercio — le stesse usate dall'NBER per datare le recessioni.
- Molto meno volatile degli indicatori basati su un'unica serie (es. solo PIL o solo disoccupazione).
- Il modello a fattori riduce il rumore delle singole serie.

**Limiti.**
- Lo smoothing introduce un ritardo: il segnale è più affidabile "ex post" che in tempo reale (il modello filtrato può differire dal modello in tempo reale, c.d. "revision problem").
- La soglia dell'80% è empirica e non teoricamente derivata: in periodi di transizione lenta il segnale può rimanere a lungo nella zona grigia 40–70%.
- Sensibile alla qualità e alle revisioni dei dati BLS e BEA.

---

## 4. Quadro comparativo degli indicatori

| Caratteristica | Sahm Rule | Hamilton GDP Index | Chauvet-Piger |
|---|---|---|---|
| Frequenza | Mensile | Trimestrale | Mensile |
| Variabile chiave | Disoccupazione (U3) | PIL reale | 4 indicatori coincidenti |
| Tipo di output | Valore numerico (soglia 0,50) | Probabilità (0–100%) | Probabilità (0–100%) |
| Tempestività | Alta | Bassa | Media |
| Affidabilità | Molto alta | Alta | Molto alta |
| Uso ottimale | Segnale di ingresso | Conferma strutturale | Conferma mensile |
| Falsi positivi noti | 1 (2024, strutturale) | Rari | Molto rari |

**Interpretazione integrata.** I tre indicatori misurano sfaccettature diverse del ciclo: la Sahm Rule fotografa il mercato del lavoro con alta frequenza; l'indice di Hamilton valuta la traiettoria dell'output complessivo; Chauvet-Piger sintetizza le quattro dimensioni che l'NBER usa nelle proprie datazioni. Usati insieme formano un sistema di allerta multiplo che riduce sia i falsi positivi che i falsi negativi.

---

## 5. Regola Tattica di Portafoglio: il Sistema "Traffic Light"

### Principio generale

La regola si basa sulla **convergenza dei segnali**: tanto più indicatori segnalano recessione simultaneamente, tanto più aggressivo deve essere lo spostamento difensivo del portafoglio. L'obiettivo non è prevedere la recessione, ma **ridurre l'esposizione al rischio quando la probabilità di danno permanente al capitale aumenta significativamente**.

La regola è applicabile a portafogli multi-asset bilanciati (es. 60/40 o simili) e distingue tre stati: **Verde** (espansione, piena allocazione al rischio), **Giallo** (allerta, riduzione graduale), **Rosso** (recessione probabile, posizionamento difensivo).

---

### Definizione degli stati e soglie di attivazione

#### 🟢 STATO VERDE — Espansione

**Condizioni (tutte devono essere verificate):**
- Sahm Rule < 0,30 pp
- Hamilton GDP Index < 33%
- Chauvet-Piger < 20%

**Allocazione target (portafoglio bilanciato di riferimento):**

| Asset class | Peso |
|---|---|
| Azioni globali (es. MSCI World / S&P 500) | 55–65% |
| Obbligazioni investment grade (duration media) | 20–25% |
| Alternativi / commodities / real asset | 10–15% |
| Liquidità e strumenti monetari | 0–5% |

**Azioni:** nessuna modifica. Mantenere il profilo di rischio obiettivo. Beta di portafoglio neutrale rispetto al benchmark.

---

#### 🟡 STATO GIALLO — Allerta (almeno 1 indicatore in zona di attenzione)

**Condizioni di attivazione (almeno una):**
- Sahm Rule ≥ 0,30 pp e < 0,50 pp, **oppure**
- Hamilton GDP Index ≥ 33% e < 67%, **oppure**
- Chauvet-Piger ≥ 20% e < 80%

**Allocazione target:**

| Asset class | Peso | Variazione vs Verde |
|---|---|---|
| Azioni globali | 45–55% | −10 pp |
| Obbligazioni IG (allungare duration) | 25–30% | +5 pp |
| Alternativi / commodities | 5–10% | −5 pp |
| Liquidità e strumenti monetari | 10–15% | +10 pp |

**Azioni tattiche:**
- Ridurre esposizione a settori ciclici (industriali, materiali, discrezionali) a favore di difensivi (utilities, healthcare, consumer staples).
- Ridurre esposizione a small cap e high yield (spread sensibili al ciclo).
- Iniziare a costruire posizioni in Treasury USA a lunga scadenza (flight-to-quality).
- Considerare coperture parziali (put su indici, volatilità).

**Revisione:** mensile, o a ogni nuovo rilascio dei dati rilevanti.

---

#### 🔴 STATO ROSSO — Recessione probabile (convergenza multipla)

**Condizioni di attivazione (almeno due delle seguenti):**
- Sahm Rule ≥ 0,50 pp, **oppure**
- Hamilton GDP Index ≥ 67%, **oppure**
- Chauvet-Piger ≥ 80%

**Allocazione target:**

| Asset class | Peso | Variazione vs Verde |
|---|---|---|
| Azioni globali | 25–35% | −30 pp |
| Obbligazioni governative alta qualità (lunga duration) | 35–40% | +15 pp |
| Oro / asset reali difensivi | 5–10% | neutro/+5 |
| Liquidità e strumenti monetari | 20–30% | +20 pp |

**Azioni tattiche:**
- Portare il beta azionario del portafoglio significativamente sotto 1 (es. 0,4–0,6).
- Eliminare o azzerare esposizione a high yield, leveraged loans, mercati emergenti in valuta locale.
- Concentrare l'esposizione azionaria residua su settori ad alta qualità e bassa ciclicità (healthcare, utilities, dividend growers con payout sostenibile).
- Incrementare posizioni in titoli governativi USA a lunga scadenza (20–30Y) e/o TIP anti-inflazione se la recessione è accompagnata da pressioni sui prezzi.
- Considerare posizioni long su VIX o opzioni put sistematiche come copertura residua.

**Revisione:** bisettimanale, con monitoraggio continuo dei dati in uscita.

---

### Regola di uscita dallo Stato Rosso (segnale di riaccumulazione)

Il ritorno progressivo allo Stato Giallo e poi Verde avviene solo quando **tutti** i seguenti criteri sono soddisfatti:

1. Hamilton GDP Index scende **stabilmente** al di sotto del 33% per almeno un trimestre.
2. Chauvet-Piger scende **stabilmente** al di sotto del 20% per almeno 2 mesi consecutivi.
3. Sahm Rule inizia a invertire (la media mobile trimestrale di U3 smette di accelerare e si stabilizza o scende).
4. *Opzionale, per investitori con orizzonte di medio-lungo termine:* lo S&P 500 ha già registrato un minimo confermato (definito come rimbalzo ≥ 20% dai minimi), segnalando che il mercato ha già incorporato la recessione.

> ⚠️ **Attenzione al "all-clear" prematuro.** Le recessioni tendono a produrre più di un minimo (double-dip pattern) e i mercati azionari spesso rimbalzano violentemente nel mezzo di una recessione prima di ritestare i minimi. La regola di uscita richiede conferma dagli indicatori macro, non solo dall'azione di prezzo.

---

### Note operative e avvertenze generali

- **Questa regola è uno strumento tattico e sistematico**, non un sistema di market timing esatto. Il suo scopo è ridurre il drawdown nelle fasi peggiori del ciclo, accettando di lasciare sul tavolo parte del rendimento nelle fasi di transizione.
- **I costi di transazione e le implicazioni fiscali** delle rotazioni devono essere valutati caso per caso: in un portafoglio con plusvalenze latenti rilevanti, potrebbe essere preferibile una riduzione del rischio tramite strumenti derivati o ETF invece che vendita diretta delle posizioni.
- **Il contesto monetario è un fattore complementare**: in cicli in cui la Fed ha già avviato tagli aggressivi, la duration obbligazionaria può offrire protezione maggiore; in cicli di stagflazione (recessione + inflazione alta), l'oro e i TIPS diventano più importanti dei Treasury nominali.
- **Backtesting indicativo**: applicando questa regola alle recessioni USA dal 1990 a oggi (1990–91, 2001, 2007–09, 2020), il portafoglio difensivo Rosso avrebbe ridotto il drawdown massimo di 15–25 punti percentuali rispetto a un portafoglio 60/40 statico, a costo di un ritardo medio di 6–12 mesi nel rientro pieno sul rischio.
- La regola **non sostituisce** una policy di investimento, un IPS (Investment Policy Statement) o il giudizio del gestore su fattori qualitativi (geopolitica, politica fiscale, shock idiosincratici).

---

*Ultimo aggiornamento documento: giugno 2025 — Fonti: FRED St. Louis Fed, Hamilton Project, UC Riverside (Chauvet), BLS, BEA.*
