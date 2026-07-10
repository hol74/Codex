# Fase D - Slice 1: Adapter FRED isolato con stub - Piano implementativo

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:executing-plans per eseguire task-by-task. Steps usano sintassi checkbox `- [ ]`.

**Goal:** Introdurre l'architettura dell'adapter FRED/ALFRED isolato con stub deterministico, scrivendo `macro-data-{asOf}.json` leggibile dal runtime esistente, senza HTTP reale.

**Architecture:** Porta Application `IExternalMacroDataSource` + use case `DownloadMacroDataUseCase` + stub Infrastructure `FredStubMacroDataSource` + writer `JsonMacroDataFileWriter`. CLI `--download-fred` compone il tutto offline. Domain/Application/Web runtime restano senza rete.

**Tech Stack:** C# .NET 10, xUnit, System.Text.Json, file-based persistence.

**Spec di riferimento:** `docs/superpowers/specs/2026-07-10-fase-d-slice1-adapter-fred-design.md`

---

## File structure

### Application (nuovi)

- `src/MacroRegime.Application/External/FredObservation.cs` - record FRED-style
- `src/MacroRegime.Application/External/FredSeriesSet.cs` - record set di serie + `Baseline`
- `src/MacroRegime.Application/External/FredFetchCommand.cs` - command fetch
- `src/MacroRegime.Application/External/DownloadMacroData.cs` - command + result
- `src/MacroRegime.Application/External/DownloadMacroDataUseCase.cs` - orchestratore
- `src/MacroRegime.Application/Ports/IExternalMacroDataSource.cs` - porta
- `src/MacroRegime.Application/Ports/IMacroDataFileWriter.cs` - porta scrittura

### Infrastructure (nuovi)

- `src/MacroRegime.Infrastructure/External/FredSeriesCatalog.cs` - catalogo serie
- `src/MacroRegime.Infrastructure/External/FredStubMacroDataSource.cs` - stub
- `src/MacroRegime.Infrastructure/External/JsonMacroDataFileWriter.cs` - writer

### CLI (modifica)

- `src/MacroRegime.Cli/Program.cs` - nuove opzioni + modo `--download-fred`

### Test (nuovi)

- `tests/MacroRegime.Application.Tests/External/DownloadMacroDataUseCaseTests.cs`
- `tests/MacroRegime.Infrastructure.Tests/External/FredSeriesCatalogTests.cs`
- `tests/MacroRegime.Infrastructure.Tests/External/FredStubMacroDataSourceTests.cs`
- `tests/MacroRegime.Infrastructure.Tests/External/JsonMacroDataFileWriterTests.cs`

### Test (modifica)

- `tests/MacroRegime.Cli.Tests/MacroRegimeCliTests.cs` - 3 test nuovi `--download-fred`

### Docs (nuovi/finali)

- `docs/adr/0004-isolamento-rete-adapter-fred.md`
- `docs/checkpoints/0024-fase-d-slice1-adapter-fred-stub-done.md`
- aggiorna `docs/0001-piano-operativo.md`, `docs/0002-riepilogo-lavoro-svolto.md`

---

## Catalogo serie baseline (allineato ai sample esistenti)

| SeriesCode | FRED series id | Name | Dimension | Unit | Frequenza | Base | Ampiezza |
|---|---|---|---|---|---|---|---|
| `ISM_PMI` | `NAPM` | ISM manufacturing PMI | Growth | Index | monthly | 52.0 | 3.0 |
| `SAHM` | `SAHMREALTIME` | Sahm rule recession indicator | Growth | Index | monthly | 0.05 | 0.10 |
| `T10YIE` | `T10YIE` | 10-year breakeven inflation | Inflation | Percent | daily | 2.0 | 0.5 |
| `VIX` | `VIXCLS` | CBOE volatility index | Risk | Index | daily | 18.0 | 5.0 |
| `YC_10Y2Y` | `T10Y2Y` | 10-year minus 2-year Treasury slope | Monetary | Percentage points | daily | 0.0 | 0.5 |
| `HY_OAS` | `BAMLH0A0HYM2` | High-yield option-adjusted spread | Credit | Basis points | daily | 300.0 | 80.0 |

Motivo: queste 6 serie sono gia' usate dai sample e dalla feature engine; il file scaricato e' immediatamente consumabile dalla pipeline esistente.

Generazione deterministica: `value = base + ampiezza * DeterministicFactor(seriesCode, asOf)` dove `DeterministicFactor` restituisce un double in `[-1, 1]` derivato da hash stabile di `seriesCode + asOf`. `observationDate` = `asOf` per daily, ultimo giorno del mese precedente per monthly. `publicationDate = asOf`, `vintageDate = asOf` (flat).

---

## Task 1: DownloadMacroDataUseCase (Application) con fakes

**Files:**
- Create: `src/MacroRegime.Application/External/FredObservation.cs`
- Create: `src/MacroRegime.Application/External/FredSeriesSet.cs`
- Create: `src/MacroRegime.Application/External/FredFetchCommand.cs`
- Create: `src/MacroRegime.Application/External/DownloadMacroData.cs`
- Create: `src/MacroRegime.Application/Ports/IExternalMacroDataSource.cs`
- Create: `src/MacroRegime.Application/Ports/IMacroDataFileWriter.cs`
- Create: `src/MacroRegime.Application/External/DownloadMacroDataUseCase.cs`
- Test: `tests/MacroRegime.Application.Tests/External/DownloadMacroDataUseCaseTests.cs`

- [ ] Step 1: Scrivere test fallente

Test (xUnit) con `FakeExternalMacroDataSource` e `FakeMacroDataFileWriter` in-memory:

```csharp
namespace MacroRegime.Application.Tests.External;

public sealed class DownloadMacroDataUseCaseTests
{
    [Fact]
    public async Task ExecuteAsync_WritesFile_WithCorrectNameAndSeriesCount()
    {
        var asOf = new AsOfDate(new DateOnly(2026, 7, 1));
        var observations = new[]
        {
            new FredObservation("NAPM", "ISM_PMI", asOf.Value, asOf.Value, asOf.Value, 52.0m, "Index"),
            new FredObservation("VIXCLS", "VIX", asOf.Value, asOf.Value, asOf.Value, 18.0m, "Index"),
        };
        var source = new FakeExternalMacroDataSource(observations);
        var writer = new FakeMacroDataFileWriter();
        var useCase = new DownloadMacroDataUseCase(source, writer);

        var result = await useCase.ExecuteAsync(
            new DownloadMacroDataCommand(asOf, FredSeriesSet.Baseline, "/tmp/out"));

        Assert.Equal(2, result.SeriesCount);
        Assert.Equal(2, result.ObservationCount);
        Assert.Equal("/tmp/out/macro-data-2026-07-01.json", result.OutputPath);
        Assert.Equal(asOf, writer.LastAsOf);
        Assert.Equal(2, writer.LastObservations!.Count);
    }

    [Fact]
    public async Task ExecuteAsync_RequestsOnlyBaselineSeries_FromSource()
    {
        var asOf = new AsOfDate(new DateOnly(2026, 7, 1));
        var source = new FakeExternalMacroDataSource(Array.Empty<FredObservation>());
        var writer = new FakeMacroDataFileWriter();
        var useCase = new DownloadMacroDataUseCase(source, writer);

        await useCase.ExecuteAsync(new DownloadMacroDataCommand(asOf, FredSeriesSet.Baseline, "/tmp/out"));

        Assert.Equal(FredSeriesSet.Baseline, source.LastCommand?.SeriesSet);
        Assert.Equal(asOf, source.LastCommand?.AsOfDate);
    }

    [Fact]
    public async Task ExecuteAsync_Throws_WhenSeriesSetIsEmpty()
    {
        var asOf = new AsOfDate(new DateOnly(2026, 7, 1));
        var useCase = new DownloadMacroDataUseCase(new FakeExternalMacroDataSource(Array.Empty<FredObservation>()), new FakeMacroDataFileWriter());

        await Assert.ThrowsAsync<ArgumentException>(() =>
            useCase.ExecuteAsync(new DownloadMacroDataCommand(asOf, new FredSeriesSet(Array.Empty<string>()), "/tmp/out")));
    }

    private sealed class FakeExternalMacroDataSource : IExternalMacroDataSource
    {
        private readonly IReadOnlyList<FredObservation> observations;
        public FredFetchCommand? LastCommand { get; private set; }
        public FakeExternalMacroDataSource(IReadOnlyList<FredObservation> observations) => this.observations = observations;
        public Task<IReadOnlyList<FredObservation>> FetchAsync(FredFetchCommand command, CancellationToken ct = default)
        {
            LastCommand = command;
            return Task.FromResult(observations);
        }
    }

    private sealed class FakeMacroDataFileWriter : IMacroDataFileWriter
    {
        public IReadOnlyList<FredObservation>? LastObservations { get; private set; }
        public AsOfDate? LastAsOf { get; private set; }
        public Task<string> WriteAsync(IReadOnlyList<FredObservation> observations, AsOfDate asOfDate, string outputDirectory, CancellationToken ct = default)
        {
            LastObservations = observations;
            LastAsOf = asOfDate;
            return Task.FromResult(Path.Combine(outputDirectory, $"macro-data-{asOfDate.Value:yyyy-MM-dd}.json"));
        }
    }
}
```

- [ ] Step 2: Eseguire test e verificare fail (compilation error: tipi mancanti)

Run: `dotnet test tests/MacroRegime.Application.Tests --no-restore -filter DownloadMacroData`
Expected: FAIL compilation (namespace/types not found)

- [ ] Step 3: Implementare tipi Application

`src/MacroRegime.Application/External/FredObservation.cs`:
```csharp
using MacroRegime.Domain.Time;

namespace MacroRegime.Application.External;

public sealed record FredObservation(
    string SeriesId,
    string SeriesCode,
    DateOnly ObservationDate,
    DateOnly PublicationDate,
    DateOnly VintageDate,
    decimal Value,
    string Unit);
```

`src/MacroRegime.Application/External/FredSeriesSet.cs`:
```csharp
namespace MacroRegime.Application.External;

public sealed record FredSeriesSet(IReadOnlyList<string> SeriesCodes)
{
    public static FredSeriesSet Baseline { get; } = new(new[]
    {
        "ISM_PMI", "SAHM", "T10YIE", "VIX", "YC_10Y2Y", "HY_OAS"
    });
}
```

`src/MacroRegime.Application/External/FredFetchCommand.cs`:
```csharp
using MacroRegime.Domain.Time;

namespace MacroRegime.Application.External;

public sealed record FredFetchCommand(AsOfDate AsOfDate, FredSeriesSet SeriesSet);
```

`src/MacroRegime.Application/External/DownloadMacroData.cs`:
```csharp
using MacroRegime.Domain.Time;

namespace MacroRegime.Application.External;

public sealed record DownloadMacroDataCommand(AsOfDate AsOfDate, FredSeriesSet SeriesSet, string OutputDirectory);

public sealed record DownloadMacroDataResult(string OutputPath, int SeriesCount, int ObservationCount);
```

`src/MacroRegime.Application/Ports/IExternalMacroDataSource.cs`:
```csharp
using MacroRegime.Application.External;

namespace MacroRegime.Application.Ports;

public interface IExternalMacroDataSource
{
    Task<IReadOnlyList<FredObservation>> FetchAsync(FredFetchCommand command, CancellationToken cancellationToken = default);
}
```

`src/MacroRegime.Application/Ports/IMacroDataFileWriter.cs`:
```csharp
using MacroRegime.Application.External;
using MacroRegime.Domain.Time;

namespace MacroRegime.Application.Ports;

public interface IMacroDataFileWriter
{
    Task<string> WriteAsync(IReadOnlyList<FredObservation> observations, AsOfDate asOfDate, string outputDirectory, CancellationToken cancellationToken = default);
}
```

`src/MacroRegime.Application/External/DownloadMacroDataUseCase.cs`:
```csharp
using MacroRegime.Application.Ports;
using MacroRegime.Domain.Time;

namespace MacroRegime.Application.External;

public sealed class DownloadMacroDataUseCase
{
    private readonly IExternalMacroDataSource source;
    private readonly IMacroDataFileWriter writer;

    public DownloadMacroDataUseCase(IExternalMacroDataSource source, IMacroDataFileWriter writer)
    {
        this.source = source;
        this.writer = writer;
    }

    public async Task<DownloadMacroDataResult> ExecuteAsync(DownloadMacroDataCommand command, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(command);
        if (command.SeriesSet.SeriesCodes.Count == 0)
        {
            throw new ArgumentException("Series set must contain at least one series.", nameof(command));
        }

        var observations = await source.FetchAsync(new FredFetchCommand(command.AsOfDate, command.SeriesSet), cancellationToken).ConfigureAwait(false);
        var outputPath = await writer.WriteAsync(observations, command.AsOfDate, command.OutputDirectory, cancellationToken).ConfigureAwait(false);
        var seriesCount = observations.Select(o => o.SeriesCode).Distinct().Count();
        return new DownloadMacroDataResult(outputPath, seriesCount, observations.Count);
    }
}
```

- [ ] Step 4: Eseguire test e verificare pass

Run: `dotnet test tests/MacroRegime.Application.Tests --no-restore -filter DownloadMacroData`
Expected: PASS (3 test)

- [ ] Step 5: Commit

```bash
git add src/MacroRegime.Application/External src/MacroRegime.Application/Ports/IExternalMacroDataSource.cs src/MacroRegime.Application/Ports/IMacroDataFileWriter.cs tests/MacroRegime.Application.Tests/External
git commit -m "feat(fase-d): add DownloadMacroDataUseCase with IExternalMacroDataSource port"
```

---

## Task 2: FredSeriesCatalog (Infrastructure)

**Files:**
- Create: `src/MacroRegime.Infrastructure/External/FredSeriesCatalog.cs`
- Test: `tests/MacroRegime.Infrastructure.Tests/External/FredSeriesCatalogTests.cs`

- [ ] Step 1: Scrivere test fallente

```csharp
namespace MacroRegime.Infrastructure.Tests.External;

public sealed class FredSeriesCatalogTests
{
    [Fact]
    public void Baseline_ContainsSixSeries()
    {
        var codes = FredSeriesCatalog.BaselineSeriesCodes;
        Assert.Equal(new[] { "ISM_PMI", "SAHM", "T10YIE", "VIX", "YC_10Y2Y", "HY_OAS" }, codes);
    }

    [Fact]
    public void Resolve_ReturnsMetadata_ForKnownCode()
    {
        var meta = FredSeriesCatalog.Resolve("ISM_PMI");
        Assert.Equal("NAPM", meta.FredSeriesId);
        Assert.Equal("ISM manufacturing PMI", meta.Name);
        Assert.Equal("Growth", meta.Dimension);
        Assert.Equal("Index", meta.Unit);
        Assert.Equal("monthly", meta.Frequency);
        Assert.Equal(52.0m, meta.BaseValue);
        Assert.Equal(3.0m, meta.Amplitude);
    }

    [Fact]
    public void Resolve_Throws_ForUnknownCode()
    {
        Assert.Throws<KeyNotFoundException>(() => FredSeriesCatalog.Resolve("UNKNOWN"));
    }

    [Fact]
    public void Resolve_ReturnsAllSix_ForBaselineCodes()
    {
        foreach (var code in FredSeriesCatalog.BaselineSeriesCodes)
        {
            var meta = FredSeriesCatalog.Resolve(code);
            Assert.Equal(code, meta.SeriesCode);
        }
    }
}
```

- [ ] Step 2: Eseguire e verificare fail (compilation)

Run: `dotnet test tests/MacroRegime.Infrastructure.Tests --no-restore -filter FredSeriesCatalog`
Expected: FAIL compilation

- [ ] Step 3: Implementare catalogo

```csharp
namespace MacroRegime.Infrastructure.External;

public sealed record FredSeriesMetadata(
    string SeriesCode,
    string FredSeriesId,
    string Name,
    string Dimension,
    string Unit,
    string Frequency,
    decimal BaseValue,
    decimal Amplitude);

public static class FredSeriesCatalog
{
    public static IReadOnlyList<string> BaselineSeriesCodes { get; } = new[]
    {
        "ISM_PMI", "SAHM", "T10YIE", "VIX", "YC_10Y2Y", "HY_OAS"
    };

    private static readonly IReadOnlyDictionary<string, FredSeriesMetadata> Entries = new Dictionary<string, FredSeriesMetadata>(StringComparer.OrdinalIgnoreCase)
    {
        ["ISM_PMI"] = new("ISM_PMI", "NAPM", "ISM manufacturing PMI", "Growth", "Index", "monthly", 52.0m, 3.0m),
        ["SAHM"] = new("SAHM", "SAHMREALTIME", "Sahm rule recession indicator", "Growth", "Index", "monthly", 0.05m, 0.10m),
        ["T10YIE"] = new("T10YIE", "T10YIE", "10-year breakeven inflation", "Inflation", "Percent", "daily", 2.0m, 0.5m),
        ["VIX"] = new("VIX", "VIXCLS", "CBOE volatility index", "Risk", "Index", "daily", 18.0m, 5.0m),
        ["YC_10Y2Y"] = new("YC_10Y2Y", "T10Y2Y", "10-year minus 2-year Treasury slope", "Monetary", "Percentage points", "daily", 0.0m, 0.5m),
        ["HY_OAS"] = new("HY_OAS", "BAMLH0A0HYM2", "High-yield option-adjusted spread", "Credit", "Basis points", "daily", 300.0m, 80.0m),
    };

    public static FredSeriesMetadata Resolve(string seriesCode)
    {
        return Entries.TryGetValue(seriesCode, out var meta)
            ? meta
            : throw new KeyNotFoundException($"Unknown FRED series code '{seriesCode}'.");
    }
}
```

- [ ] Step 4: Verificare pass

Run: `dotnet test tests/MacroRegime.Infrastructure.Tests --no-restore -filter FredSeriesCatalog`
Expected: PASS (4 test)

- [ ] Step 5: Commit

```bash
git add src/MacroRegime.Infrastructure/External/FredSeriesCatalog.cs tests/MacroRegime.Infrastructure.Tests/External/FredSeriesCatalogTests.cs
git commit -m "feat(fase-d): add FredSeriesCatalog baseline metadata"
```

---

## Task 3: FredStubMacroDataSource (Infrastructure)

**Files:**
- Create: `src/MacroRegime.Infrastructure/External/FredStubMacroDataSource.cs`
- Test: `tests/MacroRegime.Infrastructure.Tests/External/FredStubMacroDataSourceTests.cs`

- [ ] Step 1: Scrivere test fallente

```csharp
namespace MacroRegime.Infrastructure.Tests.External;

public sealed class FredStubMacroDataSourceTests
{
    private static readonly AsOfDate AsOf = new(new DateOnly(2026, 7, 1));

    [Fact]
    public async Task FetchAsync_ReturnsOneObservationPerSeries_ForBaselineSet()
    {
        var source = new FredStubMacroDataSource();
        var result = await source.FetchAsync(new FredFetchCommand(AsOf, FredSeriesSet.Baseline));
        Assert.Equal(6, result.Count);
        Assert.Equal(FredSeriesCatalog.BaselineSeriesCodes, result.Select(o => o.SeriesCode).ToArray());
    }

    [Fact]
    public async Task FetchAsync_IsDeterministic_SameAsOfSameValues()
    {
        var source = new FredStubMacroDataSource();
        var first = await source.FetchAsync(new FredFetchCommand(AsOf, FredSeriesSet.Baseline));
        var second = await source.FetchAsync(new FredFetchCommand(AsOf, FredSeriesSet.Baseline));
        Assert.Equal(first, second);
    }

    [Fact]
    public async Task FetchAsync_PublicationDate_EqualsAsOf()
    {
        var source = new FredStubMacroDataSource();
        var result = await source.FetchAsync(new FredFetchCommand(AsOf, FredSeriesSet.Baseline));
        Assert.All(result, o => Assert.Equal(AsOf.Value, o.PublicationDate));
    }

    [Fact]
    public async Task FetchAsync_VintageDate_EqualsAsOf_Flat()
    {
        var source = new FredStubMacroDataSource();
        var result = await source.FetchAsync(new FredFetchCommand(AsOf, FredSeriesSet.Baseline));
        Assert.All(result, o => Assert.Equal(AsOf.Value, o.VintageDate));
    }

    [Fact]
    public async Task FetchAsync_MonthlySeries_ObservationDate_IsLastDayOfPreviousMonth()
    {
        var source = new FredStubMacroDataSource();
        var result = await source.FetchAsync(new FredFetchCommand(AsOf, new FredSeriesSet(new[] { "ISM_PMI" })));
        var ism = Assert.Single(result);
        Assert.Equal(new DateOnly(2026, 6, 30), ism.ObservationDate);
    }

    [Fact]
    public async Task FetchAsync_DailySeries_ObservationDate_EqualsAsOf()
    {
        var source = new FredStubMacroDataSource();
        var result = await source.FetchAsync(new FredFetchCommand(AsOf, new FredSeriesSet(new[] { "VIX" })));
        var vix = Assert.Single(result);
        Assert.Equal(AsOf.Value, vix.ObservationDate);
    }

    [Fact]
    public async Task FetchAsync_ReturnsOnlyRequestedSeries_WhenSubsetRequested()
    {
        var source = new FredStubMacroDataSource();
        var result = await source.FetchAsync(new FredFetchCommand(AsOf, new FredSeriesSet(new[] { "VIX", "SAHM" })));
        Assert.Equal(2, result.Count);
        Assert.Contains(result, o => o.SeriesCode == "VIX");
        Assert.Contains(result, o => o.SeriesCode == "SAHM");
    }

    [Fact]
    public async Task FetchAsync_Throws_OnUnknownSeriesCode()
    {
        var source = new FredStubMacroDataSource();
        await Assert.ThrowsAsync<KeyNotFoundException>(() =>
            source.FetchAsync(new FredFetchCommand(AsOf, new FredSeriesSet(new[] { "UNKNOWN" }))));
    }
}
```

- [ ] Step 2: Eseguire e verificare fail

Run: `dotnet test tests/MacroRegime.Infrastructure.Tests --no-restore -filter FredStubMacroDataSource`
Expected: FAIL compilation

- [ ] Step 3: Implementare stub

```csharp
using System.Security.Cryptography;
using MacroRegime.Application.External;
using MacroRegime.Application.Ports;

namespace MacroRegime.Infrastructure.External;

public sealed class FredStubMacroDataSource : IExternalMacroDataSource
{
    public Task<IReadOnlyList<FredObservation>> FetchAsync(FredFetchCommand command, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(command);
        var asOf = command.AsOfDate.Value;
        var observations = command.SeriesSet.SeriesCodes
            .Select(code => BuildObservation(code, asOf))
            .ToArray();
        return Task.FromResult<IReadOnlyList<FredObservation>>(observations);
    }

    private static FredObservation BuildObservation(string seriesCode, DateOnly asOf)
    {
        var meta = FredSeriesCatalog.Resolve(seriesCode);
        var factor = DeterministicFactor(seriesCode, asOf);
        var value = meta.BaseValue + meta.Amplitude * factor;
        var observationDate = meta.Frequency == "daily"
            ? asOf
            : LastDayOfPreviousMonth(asOf);
        return new FredObservation(
            meta.FredSeriesId,
            meta.SeriesCode,
            observationDate,
            asOf,
            asOf,
            decimal.Round((decimal)(value), 4, MidpointRounding.ToEven),
            meta.Unit);
    }

    private static double DeterministicFactor(string seriesCode, DateOnly asOf)
    {
        var seed = $"{seriesCode}|{asOf:yyyy-MM-dd}";
        var bytes = System.Text.Encoding.UTF8.GetBytes(seed);
        var hash = SHA256.HashData(bytes);
        var shortHash = BitConverter.ToInt32(hash, 0);
        var normalized = (shortHash & 0x7FFFFFFF) / (double)0x7FFFFFFF; // [0,1]
        return (normalized * 2.0) - 1.0; // [-1,1]
    }

    private static DateOnly LastDayOfPreviousMonth(DateOnly asOf)
    {
        var firstOfThisMonth = new DateOnly(asOf.Year, asOf.Month, 1);
        return firstOfThisMonth.AddDays(-1);
    }
}
```

- [ ] Step 4: Verificare pass

Run: `dotnet test tests/MacroRegime.Infrastructure.Tests --no-restore -filter FredStubMacroDataSource`
Expected: PASS (8 test)

- [ ] Step 5: Commit

```bash
git add src/MacroRegime.Infrastructure/External/FredStubMacroDataSource.cs tests/MacroRegime.Infrastructure.Tests/External/FredStubMacroDataSourceTests.cs
git commit -m "feat(fase-d): add FredStubMacroDataSource deterministic stub"
```

---

## Task 4: JsonMacroDataFileWriter (Infrastructure)

**Files:**
- Create: `src/MacroRegime.Infrastructure/External/JsonMacroDataFileWriter.cs`
- Test: `tests/MacroRegime.Infrastructure.Tests/External/JsonMacroDataFileWriterTests.cs`

- [ ] Step 1: Scrivere test fallente

```csharp
namespace MacroRegime.Infrastructure.Tests.External;

public sealed class JsonMacroDataFileWriterTests : IDisposable
{
    private readonly string directoryPath = Path.Combine(Path.GetTempPath(), "JsonMacroDataFileWriterTests", Guid.NewGuid().ToString("N"));

    [Fact]
    public async Task WriteAsync_CreatesDirectory_IfMissing()
    {
        var writer = new JsonMacroDataFileWriter();
        var outDir = Path.Combine(directoryPath, "nested", "out");
        var observations = new[]
        {
            new FredObservation("NAPM", "ISM_PMI", new DateOnly(2026,6,30), new DateOnly(2026,7,1), new DateOnly(2026,7,1), 52.0m, "Index"),
        };

        var path = await writer.WriteAsync(observations, new AsOfDate(new DateOnly(2026,7,1)), outDir);

        Assert.True(Directory.Exists(outDir));
        Assert.True(File.Exists(path));
    }

    [Fact]
    public async Task WriteAsync_WritesFile_NamedMacroDataDateJson()
    {
        var writer = new JsonMacroDataFileWriter();
        var outDir = Path.Combine(directoryPath, "out");
        Directory.CreateDirectory(outDir);
        var observations = new[]
        {
            new FredObservation("NAPM", "ISM_PMI", new DateOnly(2026,6,30), new DateOnly(2026,7,1), new DateOnly(2026,7,1), 52.0m, "Index"),
        };

        var path = await writer.WriteAsync(observations, new AsOfDate(new DateOnly(2026,7,1)), outDir);

        Assert.Equal(Path.Combine(outDir, "macro-data-2026-07-01.json"), path);
    }

    [Fact]
    public async Task WriteAsync_SerializesSchemaVersion1_AndCamelCase()
    {
        var writer = new JsonMacroDataFileWriter();
        var outDir = Path.Combine(directoryPath, "out");
        Directory.CreateDirectory(outDir);
        var observations = new[]
        {
            new FredObservation("NAPM", "ISM_PMI", new DateOnly(2026,6,30), new DateOnly(2026,7,1), new DateOnly(2026,7,1), 52.0m, "Index"),
        };

        var path = await writer.WriteAsync(observations, new AsOfDate(new DateOnly(2026,7,1)), outDir);
        var json = await File.ReadAllTextAsync(path);

        Assert.Contains("\"schemaVersion\": 1", json);
        Assert.Contains("\"asOfDate\": \"2026-07-01\"", json);
        Assert.Contains("\"seriesCode\": \"ISM_PMI\"", json);
        Assert.Contains("\"macroObservations\": [", json);
        Assert.Contains("\"marketObservations\": []", json);
    }

    [Fact]
    public async Task WriteAsync_RoundTrips_ThroughJsonDataSnapshotProvider()
    {
        var writer = new JsonMacroDataFileWriter();
        var outDir = Path.Combine(directoryPath, "out");
        Directory.CreateDirectory(outDir);
        var asOf = new AsOfDate(new DateOnly(2026, 7, 1));
        var observations = new[]
        {
            new FredObservation("NAPM", "ISM_PMI", new DateOnly(2026,6,30), new DateOnly(2026,7,1), new DateOnly(2026,7,1), 52.0m, "Index"),
            new FredObservation("VIXCLS", "VIX", new DateOnly(2026,7,1), new DateOnly(2026,7,1), new DateOnly(2026,7,1), 18.0m, "Index"),
        };

        var path = await writer.WriteAsync(observations, asOf, outDir);
        var provider = new JsonDataSnapshotProvider(path, strict: true);
        var snapshot = await provider.GetSnapshotAsync(asOf);

        Assert.NotNull(snapshot);
        Assert.Equal(asOf.Value, snapshot!.AsOfDate.Value);
        Assert.Equal(2, snapshot.MacroObservations.Count);
        Assert.Empty(snapshot.MarketObservations);
    }

    public void Dispose()
    {
        if (Directory.Exists(directoryPath))
        {
            Directory.Delete(directoryPath, recursive: true);
        }
    }
}
```

- [ ] Step 2: Eseguire e verificare fail

Run: `dotnet test tests/MacroRegime.Infrastructure.Tests --no-restore -filter JsonMacroDataFileWriter`
Expected: FAIL compilation

- [ ] Step 3: Implementare writer

```csharp
using System.Text.Json;
using MacroRegime.Application.External;
using MacroRegime.Application.Ports;
using MacroRegime.Domain.Time;
using MacroRegime.Infrastructure.Import;

namespace MacroRegime.Infrastructure.External;

public sealed class JsonMacroDataFileWriter : IMacroDataFileWriter
{
    private static readonly JsonSerializerOptions SerializerOptions = new(JsonSerializerDefaults.Web) { WriteIndented = true };

    public async Task<string> WriteAsync(IReadOnlyList<FredObservation> observations, AsOfDate asOfDate, string outputDirectory, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(observations);
        ArgumentNullException.ThrowIfNull(asOfDate);
        if (string.IsNullOrWhiteSpace(outputDirectory))
        {
            throw new ArgumentException("Output directory is required.", nameof(outputDirectory));
        }

        Directory.CreateDirectory(outputDirectory);
        var macroRecords = observations.Select(MapMacro).ToArray();
        var record = new JsonDataSnapshotRecord(
            JsonDataSnapshotRecordMapper.CurrentSchemaVersion,
            asOfDate.Value,
            macroRecords,
            Array.Empty<JsonMarketObservationRecord>());
        var path = Path.Combine(outputDirectory, $"macro-data-{asOfDate.Value:yyyy-MM-dd}.json");
        await using var stream = File.Create(path);
        await JsonSerializer.SerializeAsync(stream, record, SerializerOptions, cancellationToken).ConfigureAwait(false);
        return path;
    }

    private static JsonMacroObservationRecord MapMacro(FredObservation observation)
    {
        var meta = FredSeriesCatalog.Resolve(observation.SeriesCode);
        return new JsonMacroObservationRecord(
            observation.SeriesCode,
            meta.Name,
            meta.Dimension,
            observation.ObservationDate,
            observation.PublicationDate,
            observation.VintageDate,
            observation.Value,
            "FRED-Stub",
            observation.Unit);
    }
}
```

- [ ] Step 4: Verificare pass

Run: `dotnet test tests/MacroRegime.Infrastructure.Tests --no-restore -filter JsonMacroDataFileWriter`
Expected: PASS (4 test)

- [ ] Step 5: Commit

```bash
git add src/MacroRegime.Infrastructure/External/JsonMacroDataFileWriter.cs tests/MacroRegime.Infrastructure.Tests/External/JsonMacroDataFileWriterTests.cs
git commit -m "feat(fase-d): add JsonMacroDataFileWriter producing schema v1 macro-data files"
```

---

## Task 5: CLI --download-fred

**Files:**
- Modify: `src/MacroRegime.Cli/Program.cs`
- Test: `tests/MacroRegime.Cli.Tests/MacroRegimeCliTests.cs`

- [ ] Step 1: Scrivere test fallenti (aggiungere alla classe esistente)

```csharp
[Fact]
public async Task RunAsync_DownloadFred_WritesMacroDataFileReadableByJsonDataSnapshotProvider()
{
    var outputDirectory = Path.Combine(directoryPath, "fred-out");

    var exitCode = await global::MacroRegimeCli.RunAsync(new[]
    {
        "--download-fred",
        "--as-of",
        "2026-07-01",
        "--output-dir",
        outputDirectory
    });

    Assert.Equal(0, exitCode);
    var dataPath = Path.Combine(outputDirectory, "macro-data-2026-07-01.json");
    Assert.True(File.Exists(dataPath));

    var provider = new JsonDataSnapshotProvider(dataPath, strict: true);
    var snapshot = await provider.GetSnapshotAsync(new AsOfDate(new DateOnly(2026, 7, 1)));
    Assert.NotNull(snapshot);
    Assert.Equal(6, snapshot!.MacroObservations.Count);
}

[Fact]
public async Task RunAsync_DownloadFred_ReturnsUsageError_WhenAsOfMissing()
{
    var outputDirectory = Path.Combine(directoryPath, "fred-noasof");

    var exitCode = await global::MacroRegimeCli.RunAsync(new[]
    {
        "--download-fred",
        "--output-dir",
        outputDirectory
    });

    Assert.Equal(1, exitCode);
}

[Fact]
public async Task RunAsync_DownloadFred_DoesNotWriteRunArtifacts()
{
    var outputDirectory = Path.Combine(directoryPath, "fred-only");

    var exitCode = await global::MacroRegimeCli.RunAsync(new[]
    {
        "--download-fred",
        "--as-of",
        "2026-07-01",
        "--output-dir",
        outputDirectory
    });

    Assert.Equal(0, exitCode);
    Assert.False(File.Exists(Path.Combine(outputDirectory, "runs", "regime-run-2026-07-01.json")));
    Assert.False(File.Exists(Path.Combine(outputDirectory, "reports", "macro-regime-report-2026-07-01.md")));
}
```

Aggiungere `using MacroRegime.Domain.Time;` e `using MacroRegime.Infrastructure.Import;` in cima al file di test se non presenti.

- [ ] Step 2: Eseguire e verificare fail

Run: `dotnet test tests/MacroRegime.Cli.Tests --no-restore -filter DownloadFred`
Expected: FAIL (unknown arg / option non gestita)

- [ ] Step 3: Implementare opzioni CLI e modo

Modifiche a `src/MacroRegime.Cli/Program.cs`:

1. Aggiungere `bool DownloadFred` e `string? DownloadOutputDir` al record `CliOptions`.
2. Aggiungere case `--download-fred` (flag) e `--download-output-dir` (opzionale; default = `--output-dir`) nel parser.
3. Aggiungere validazione: `--download-fred` richiede `--as-of`.
4. Aggiungere branca `if (options.DownloadFred)` prima di `RunSingleAsync` che compone `FredStubMacroDataSource` + `JsonMacroDataFileWriter` + `DownloadMacroDataUseCase`, esegue, stampa riepilogo, return 0 o 2.
5. Aggiungere `using MacroRegime.Application.External;` e `using MacroRegime.Infrastructure.External;`.
6. Aggiornare `HelpText` con le nuove opzioni.

Branca download (in `RunAsync`, dopo `ValidateOnly` e prima di `BatchFrom`):

```csharp
if (options.DownloadFred)
{
    var downloadOutputDir = Path.GetFullPath(
        string.IsNullOrWhiteSpace(options.DownloadOutputDir) ? options.OutputDirectory : options.DownloadOutputDir);
    var source = new FredStubMacroDataSource();
    var writer = new JsonMacroDataFileWriter();
    var useCase = new DownloadMacroDataUseCase(source, writer);
    try
    {
        var result = await useCase.ExecuteAsync(
            new DownloadMacroDataCommand(new AsOfDate(options.AsOfDate), FredSeriesSet.Baseline, downloadOutputDir)).ConfigureAwait(false);
        Console.WriteLine("Macro-Regime FRED download completed (stub).");
        Console.WriteLine($"As-of date: {options.AsOfDate:yyyy-MM-dd}");
        Console.WriteLine($"Series: {result.SeriesCount}");
        Console.WriteLine($"Observations: {result.ObservationCount}");
        Console.WriteLine($"Macro data file: {result.OutputPath}");
        return 0;
    }
    catch (Exception exception) when (exception is IOException or InvalidDataException or UnauthorizedAccessException or KeyNotFoundException)
    {
        Console.Error.WriteLine($"Macro-Regime FRED download failed: {exception.Message}");
        return 2;
    }
}
```

- [ ] Step 4: Verificare pass

Run: `dotnet test tests/MacroRegime.Cli.Tests --no-restore -filter DownloadFred`
Expected: PASS (3 test)

- [ ] Step 5: Commit

```bash
git add src/MacroRegime.Cli/Program.cs tests/MacroRegime.Cli.Tests/MacroRegimeCliTests.cs
git commit -m "feat(fase-d): add CLI --download-fred offline stub mode"
```

---

## Task 6: Build completo,全套 test, ADR 0004, checkpoint 0024, aggiornamento docs

- [ ] Step 1: Build soluzione

Run: `dotnet build MacroRegime.slnx --no-restore`
Expected: 0 errori, 0 warning

- [ ] Step 2: Test soluzione completa

Run: `dotnet test MacroRegime.slnx --no-restore`
Expected: tutti pass (150 + 19 nuovi = 169 approx)

- [ ] Step 3: Smoke CLI

```bash
dotnet run --project src/MacroRegime.Cli -- --download-fred --as-of 2026-07-01 --output-dir ./smoke-fred
```
Verificare file `./smoke-fred/macro-data-2026-07-01.json` presente e leggibile.

- [ ] Step 4: Gate architetturali

Verificare assenza `HttpClient` in Domain/Application/Web:
```bash
rg HttpClient src/MacroRegime.Domain src/MacroRegime.Application src/MacroRegime.Web
```
Expected: nessun match.

- [ ] Step 5: Scrivere ADR 0004

`docs/adr/0004-isolamento-rete-adapter-fred.md`: formalizza isolamento rete, downloader offline come adapter Infrastructure, porta Application, runtime file-based, test accettazione.

- [ ] Step 6: Scrivere checkpoint 0024

`docs/checkpoints/0024-fase-d-slice1-adapter-fred-stub-done.md`: scopo, cosa realizzato, verifiche (build/test counts), gate, cosa resta fuori (Slice 2/3).

- [ ] Step 7: Aggiornare `docs/0001-piano-operativo.md`

Fase D - Slice 1 completata; Slice 2 (HTTP reale) e Slice 3 (vintage/calendar) rimangono.

- [ ] Step 8: Aggiornare `docs/0002-riepilogo-lavoro-svolto.md`

Sezione 10. Fase D - Slice 1.

- [ ] Step 9: Commit finale docs

```bash
git add docs/adr/0004-isolamento-rete-adapter-fred.md docs/checkpoints/0024-fase-d-slice1-adapter-fred-stub-done.md docs/0001-piano-operativo.md docs/0002-riepilogo-lavoro-svolto.md
git commit -m "docs(fase-d): ADR 0004 network isolation, checkpoint 0024, update plan and summary"
```

---

## Self-review check

- **Spec coverage**: ogni componente della spec ha un task. ✓
- **Placeholder**: nessun TBD/TODO. ✓
- **Type consistency**: `FredObservation`, `FredSeriesSet`, `FredFetchCommand`, `DownloadMacroDataCommand/Result`, `IExternalMacroDataSource`, `IMacroDataFileWriter` usati coerentemente tra task. ✓
- `AsOfDate` usato ovunque (Domain value object esistente). ✓
- `JsonDataSnapshotRecordMapper.CurrentSchemaVersion` riusato per schema version. ✓
- Catalogo allineato ai 6 sample series per integrazione immediata. ✓
