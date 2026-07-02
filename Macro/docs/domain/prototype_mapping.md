# Mapping dal prototipo Finance al nuovo Macro-Regime Engine

Data: 2026-07-02

## Scopo

Questo documento mappa gli elementi utili del prototipo Finance verso il nuovo sistema Macro-Regime. Serve a recuperare lavoro valido senza importare gli accoppiamenti architetturali sbagliati.

Azioni possibili:

- recuperare: usare concetto/nome quasi direttamente;
- rivedere: mantenere idea ma ridisegnare tipo o responsabilita';
- spezzare: dividere un componente in piu' parti;
- rimandare: usare dopo il core;
- scartare: non portare nel nuovo sistema.

## Regola generale

Il prototipo Finance e' una reference implementation. Non e' la base diretta da estendere.

## Mapping principale

| Prototipo Finance | Nuovo sistema | Azione | Note |
|---|---|---|---|
| `Finance.Domain.Entities.MacroDataSource` | `MacroDataSource` / source metadata | rivedere | Separare fonte logica da entita' EF persistente. |
| `MacroSeries` | `MacroSeriesDefinition` | rivedere | Deve descrivere serie, frequenza, unita', polarita', lag e fonte. |
| `MacroObservation` | `MacroObservation` | recuperare | Nel core deve essere record/value data senza navigation properties. |
| `DataVintage` | `DataVintage` / `DataSnapshot` | recuperare | Concetto fondamentale per evitare look-ahead bias. |
| `MarketSeries` | `MarketSeriesDefinition` | rivedere | Mantenere proxy role, asset class code e categoria. |
| `MarketObservation` | `MarketObservation` | recuperare | Deve includere `AvailabilityDate`. |
| `MacroFeatureSetVersion` | `FeatureSetVersion` | recuperare | Da rendere parte esplicita del run. |
| `MacroFeatureDefinition` | `FeatureDefinition` | recuperare | Deve diventare input del normalizer/detector. |
| `MacroFeatureValue` | `FeatureScore` / persisted feature value | spezzare | Separare score di dominio da valore persistito. |
| `RegimeModel` | `RegimeModelDescriptor` | rivedere | Distinguere baseline/challenger/retired. |
| `RegimeModelVersion` | `BaselineModelVersion` / `ModelVersion` | recuperare | Parametri e soglie devono essere espliciti. |
| `RegimeRun` | `RegimeSnapshot` + persisted `RegimeRunRecord` | spezzare | Il core produce snapshot; Infrastructure salva record. |
| `RegimeProbability` | `RegimeProbability` | recuperare | Deve validare range e ordine. |
| `RegimeExplanation` | `RegimeExplanation` | recuperare | Deve distinguere driver e segnali contrari. |
| `RegimeReport` | `RegimeReport` in Reporting | rimandare | La reportistica viene dopo il core. |
| `RegimeObservation` | Da valutare | rivedere | Sembra sovrapporsi a `RegimeRun`. Evitare doppio concetto. |
| `RegimeSignal` | `FeatureScore` o explanation detail | rivedere | Utile, ma da consolidare. |
| `AllocationProposal` | `AllocationProposal` | rivedere | Da reintrodurre dopo detector e policy. |
| `RebalanceRecommendation` | `AllocationRecommendation` | rimandare | Serve nella fase allocation, non nel domain core iniziale. |
| `PortfolioPolicy` | `StrategicAllocationPolicy` | rivedere | Nome piu' esplicito per il contesto Macro-Regime. |

## Mapping servizi

| Prototipo Finance | Nuovo sistema | Azione | Note |
|---|---|---|---|
| `RegimeCalculationService` | `BaselineRegimeDetector` + `CalculateRegimeUseCase` + repository | spezzare | Non deve restare monolitico. |
| `MacroDataFoundationService` | `IDataSnapshotProvider` + import adapters | spezzare | As-of snapshot utile, import reali rimandati. |
| `MacroRegimeService` | dashboard query use case | rimandare | Utile per UI, dopo core e application. |
| `FinanceDbSeeder` | fixtures e sample scenarios | spezzare | Recuperare dati, non logica. |
| `DependencyInjection` | composition root | rimandare | Solo quando esiste Infrastructure. |

## Mapping UI

| Prototipo Finance | Nuovo sistema | Azione | Note |
|---|---|---|---|
| `MacroRegimeController` | futuro controller Web | rimandare | Recuperare flusso manuale `Calculate`. |
| `Views/MacroRegime/Index.cshtml` | futura dashboard | rimandare | Buone sezioni informative, ma non ora. |
| `Views/MacroRegime/Empty.cshtml` | futura empty state | rimandare | Utile quando non esistono run. |

## Mapping test

| Test Finance | Nuovo test | Azione | Note |
|---|---|---|---|
| `AsOfSnapshot_UsesOnlyVintageAvailableAtRequestedDate` | Application/Infrastructure as-of test | recuperare | Test fondamentale. |
| `CalculateAsync_UpsertsRegimeRunForSameAsOfDate` | Application persistence adapter test | rivedere | Nel core non deve esserci upsert. |
| `TargetAllocation_CanRepresentPolicyBand` | Allocation policy domain test | rimandare | Utile nella fase allocation. |
| `PortfolioMath.Weight_ReturnsComponentShare` | portfolio math test | rimandare | Troppo piccolo per ora. |

## Fixture da recuperare

### Macro series

- `ISM_PMI`: Growth.
- `SAHM`: Growth con polarita' difensiva.
- `T10YIE`: Inflation.
- `HY_OAS`: Credit.
- `YC_10Y2Y`: Monetary.
- `VIX`: Risk.
- `FREDMD_INDPRO`: Growth.

### Market proxy

- `EURUSD`: FX.
- `GLD`: Commodity.
- `VWCE_PROXY`: ETF/equity.
- `IEF_PROXY`: rates/bonds.
- `JNK_LQD`: credit proxy.

### Feature baseline

- `GROWTH_MOM`;
- `INFL_PRESS`;
- `RISK_APPETITE`;
- `MONETARY_COND`;
- `CREDIT_STRESS`.

## Elementi da non importare

- `FinanceDbContext` nel domain core.
- Navigation properties EF.
- `SaveChangesAsync` nel detector.
- `EnsureModelVersionAsync` dentro il calcolo.
- `EnsureFeatureDefinitionsAsync` dentro il calcolo.
- Report creation dentro il detector.
- Formula hardcoded in Infrastructure.

## Nuovo flusso desiderato

```text
DataSnapshot as-of
  -> FeatureDefinition + FeatureObservation
  -> FeatureNormalizer
  -> FeatureScore[]
  -> BaselineRegimeDetector
  -> RegimeSnapshot
  -> Application use case
  -> optional persistence adapter
  -> optional report/UI
```

## Decisione

Il nuovo core deve nascere dal mapping, non da copia del codice Finance. Ogni elemento recuperato deve essere tradotto in un tipo o servizio coerente con le regole di dipendenza.
