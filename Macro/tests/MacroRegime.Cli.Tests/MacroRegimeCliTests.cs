using MacroRegime.Domain.Time;
using MacroRegime.Infrastructure.Import;

namespace MacroRegime.Cli.Tests;

public sealed class MacroRegimeCliTests : IDisposable
{
    private readonly string directoryPath = Path.Combine(Path.GetTempPath(), "MacroRegimeCliTests", Guid.NewGuid().ToString("N"));

    [Fact]
    public async Task RunAsync_WritesRunAndReport_WithDemoData()
    {
        var outputDirectory = Path.Combine(directoryPath, "output");

        var exitCode = await global::MacroRegimeCli.RunAsync(new[]
        {
            "--as-of",
            "2026-07-01",
            "--output-dir",
            outputDirectory
        });

        Assert.Equal(0, exitCode);
        Assert.True(File.Exists(Path.Combine(outputDirectory, "runs", "regime-run-2026-07-01.json")));
        Assert.True(File.Exists(Path.Combine(outputDirectory, "runs", "manifest.json")));
        Assert.True(File.Exists(Path.Combine(outputDirectory, "reports", "macro-regime-report-2026-07-01.md")));
    }

    [Fact]
    public async Task RunAsync_ReturnsUsageError_WhenStrictDataHasNoDataPath()
    {
        var exitCode = await global::MacroRegimeCli.RunAsync(new[]
        {
            "--as-of",
            "2026-07-01",
            "--strict-data"
        });

        Assert.Equal(1, exitCode);
    }

    [Fact]
    public async Task RunAsync_ReturnsFailure_WhenStrictDataFileIsMissing()
    {
        var outputDirectory = Path.Combine(directoryPath, "output");
        var missingPath = Path.Combine(directoryPath, "missing.json");

        var exitCode = await global::MacroRegimeCli.RunAsync(new[]
        {
            "--as-of",
            "2026-07-01",
            "--data",
            missingPath,
            "--strict-data",
            "--output-dir",
            outputDirectory
        });

        Assert.Equal(2, exitCode);
        Assert.False(Directory.Exists(outputDirectory));
    }

    [Fact]
    public async Task RunAsync_ReturnsFailure_WhenStrictConfigFileIsMissing()
    {
        var outputDirectory = Path.Combine(directoryPath, "output");
        var missingPath = Path.Combine(directoryPath, "missing-model.json");

        var exitCode = await global::MacroRegimeCli.RunAsync(new[]
        {
            "--as-of",
            "2026-07-01",
            "--model",
            missingPath,
            "--strict-config",
            "--output-dir",
            outputDirectory
        });

        Assert.Equal(2, exitCode);
        Assert.False(Directory.Exists(outputDirectory));
    }

    [Fact]
    public async Task RunAsync_ValidateOnly_WritesValidationReportWithoutRunArtifacts()
    {
        var outputDirectory = Path.Combine(directoryPath, "validation-output");
        var reportPath = Path.Combine(outputDirectory, "import-validation.md");

        var exitCode = await global::MacroRegimeCli.RunAsync(new[]
        {
            "--as-of",
            "2026-07-01",
            "--validate-only",
            "--validate-report",
            reportPath,
            "--output-dir",
            outputDirectory
        });

        Assert.Equal(0, exitCode);
        Assert.True(File.Exists(reportPath));
        var report = await File.ReadAllTextAsync(reportPath);
        Assert.Contains("# Import Validation Report", report);
        Assert.Contains("As-of date: 2026-07-01", report);
        Assert.False(File.Exists(Path.Combine(outputDirectory, "runs", "regime-run-2026-07-01.json")));
        Assert.False(File.Exists(Path.Combine(outputDirectory, "reports", "macro-regime-report-2026-07-01.md")));
    }

    [Fact]
    public async Task RunAsync_ValidateOnly_ReturnsFailureAndWritesReport_WhenStrictDataIsMissing()
    {
        var outputDirectory = Path.Combine(directoryPath, "validation-error-output");
        var reportPath = Path.Combine(outputDirectory, "import-validation.md");
        var missingPath = Path.Combine(directoryPath, "missing-data.json");

        var exitCode = await global::MacroRegimeCli.RunAsync(new[]
        {
            "--as-of",
            "2026-07-01",
            "--data",
            missingPath,
            "--strict-data",
            "--validate-only",
            "--validate-report",
            reportPath,
            "--output-dir",
            outputDirectory
        });

        Assert.Equal(2, exitCode);
        Assert.True(File.Exists(reportPath));
        var report = await File.ReadAllTextAsync(reportPath);
        Assert.Contains("Errors: 1", report);
        Assert.Contains("Macro data", report);
        Assert.Contains("does not exist", report);
        Assert.False(File.Exists(Path.Combine(outputDirectory, "runs", "regime-run-2026-07-01.json")));
    }

    [Fact]
    public async Task RunAsync_BatchRange_UsesDatedDataAndPortfolioDirectories()
    {
        var outputDirectory = Path.Combine(directoryPath, "batch-output");
        var dataDirectory = Path.Combine(directoryPath, "batch-data");
        var portfolioDirectory = Path.Combine(directoryPath, "batch-portfolio");
        await WriteBatchInputsAsync(dataDirectory, portfolioDirectory, new DateOnly(2026, 7, 1));
        await WriteBatchInputsAsync(dataDirectory, portfolioDirectory, new DateOnly(2026, 7, 2));

        var exitCode = await global::MacroRegimeCli.RunAsync(new[]
        {
            "--batch-from",
            "2026-07-01",
            "--batch-to",
            "2026-07-02",
            "--data-dir",
            dataDirectory,
            "--portfolio-dir",
            portfolioDirectory,
            "--strict-data",
            "--output-dir",
            outputDirectory
        });

        Assert.Equal(0, exitCode);
        Assert.True(File.Exists(Path.Combine(outputDirectory, "runs", "regime-run-2026-07-01.json")));
        Assert.True(File.Exists(Path.Combine(outputDirectory, "runs", "regime-run-2026-07-02.json")));
        Assert.True(File.Exists(Path.Combine(outputDirectory, "runs", "manifest.json")));
        var manifest = await File.ReadAllTextAsync(Path.Combine(outputDirectory, "runs", "manifest.json"));
        Assert.Contains("2026-07-01", manifest);
        Assert.Contains("2026-07-02", manifest);
    }

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

    [Fact]
    public async Task RunAsync_DownloadFredHttp_ReturnsUsageError_WhenApiKeyMissing()
    {
        var previousApiKey = Environment.GetEnvironmentVariable("FRED_API_KEY");
        var previousCurrentDirectory = Directory.GetCurrentDirectory();
        Environment.SetEnvironmentVariable("FRED_API_KEY", null);
        try
        {
            var isolatedDirectory = Path.Combine(directoryPath, "no-dotenv");
            Directory.CreateDirectory(isolatedDirectory);
            Directory.SetCurrentDirectory(isolatedDirectory);
            var outputDirectory = Path.Combine(directoryPath, "fred-http-no-key");

            var exitCode = await global::MacroRegimeCli.RunAsync(new[]
            {
                "--download-fred",
                "--fred-source",
                "http",
                "--as-of",
                "2026-07-01",
                "--output-dir",
                outputDirectory
            });

            Assert.Equal(1, exitCode);
            Assert.False(Directory.Exists(outputDirectory));
        }
        finally
        {
            Directory.SetCurrentDirectory(previousCurrentDirectory);
            Environment.SetEnvironmentVariable("FRED_API_KEY", previousApiKey);
        }
    }

    [Fact]
    public async Task RunAsync_DownloadFred_ReturnsUsageError_WhenSourceIsUnknown()
    {
        var exitCode = await global::MacroRegimeCli.RunAsync(new[]
        {
            "--download-fred",
            "--fred-source",
            "unknown",
            "--as-of",
            "2026-07-01"
        });

        Assert.Equal(1, exitCode);
    }

    [Fact]
    public async Task RunAsync_DownloadMarketData_WritesMarketDataFileReadableByJsonDataSnapshotProvider()
    {
        var outputDirectory = Path.Combine(directoryPath, "market-out");

        var exitCode = await global::MacroRegimeCli.RunAsync(new[]
        {
            "--download-market-data",
            "--as-of",
            "2026-07-01",
            "--output-dir",
            outputDirectory
        });

        Assert.Equal(0, exitCode);
        var dataPath = Path.Combine(outputDirectory, "market-data-2026-07-01.json");
        Assert.True(File.Exists(dataPath));

        var provider = new JsonDataSnapshotProvider(dataPath, strict: true);
        var snapshot = await provider.GetSnapshotAsync(new AsOfDate(new DateOnly(2026, 7, 1)));
        Assert.NotNull(snapshot);
        Assert.Equal(6, snapshot!.MarketObservations.Count);
        Assert.Empty(snapshot.MacroObservations);
    }

    [Fact]
    public async Task RunAsync_DownloadMarketData_ReturnsUsageError_WhenAsOfMissing()
    {
        var outputDirectory = Path.Combine(directoryPath, "market-noasof");

        var exitCode = await global::MacroRegimeCli.RunAsync(new[]
        {
            "--download-market-data",
            "--output-dir",
            outputDirectory
        });

        Assert.Equal(1, exitCode);
    }

    [Fact]
    public async Task RunAsync_DownloadMarketData_ReturnsUsageError_WhenSourceIsUnknown()
    {
        var exitCode = await global::MacroRegimeCli.RunAsync(new[]
        {
            "--download-market-data",
            "--market-source",
            "unknown",
            "--as-of",
            "2026-07-01"
        });

        Assert.Equal(1, exitCode);
    }

    [Fact]
    public async Task RunAsync_BuildHistoricalDataset_WritesDatasetWithForwardReturns()
    {
        var macroDirectory = Path.Combine(directoryPath, "historical-macro");
        var marketDirectory = Path.Combine(directoryPath, "historical-market");
        var outputDirectory = Path.Combine(directoryPath, "historical-out");
        Directory.CreateDirectory(macroDirectory);
        Directory.CreateDirectory(marketDirectory);
        await File.WriteAllTextAsync(Path.Combine(macroDirectory, "macro-data-2026-07-01.json"), SampleMacroDataJson("2026-07-01"));
        await File.WriteAllTextAsync(Path.Combine(marketDirectory, "market-data-2026-07-01.json"), SampleMarketDataJson("2026-07-01", 100m));
        await File.WriteAllTextAsync(Path.Combine(marketDirectory, "market-data-2026-07-29.json"), SampleMarketDataJson("2026-07-29", 110m));

        var exitCode = await global::MacroRegimeCli.RunAsync(new[]
        {
            "--build-historical-dataset",
            "--dataset-from",
            "2026-07-01",
            "--dataset-to",
            "2026-07-02",
            "--macro-data-dir",
            macroDirectory,
            "--market-data-dir",
            marketDirectory,
            "--forward-return-days",
            "28",
            "--output-dir",
            outputDirectory
        });

        Assert.Equal(0, exitCode);
        var datasetPath = Path.Combine(outputDirectory, "historical-dataset-2026-07-01-2026-07-02.json");
        Assert.True(File.Exists(datasetPath));
        var dataset = await File.ReadAllTextAsync(datasetPath);
        Assert.Contains("\"rows\": [", dataset);
        Assert.Contains("\"asOfDate\": \"2026-07-01\"", dataset);
        Assert.Contains("\"symbol\": \"SPY\"", dataset);
        Assert.Contains("\"returnValue\": 0.1", dataset);
    }

    [Fact]
    public async Task RunAsync_BuildHistoricalDataset_ReturnsUsageError_WhenDirectoriesAreMissing()
    {
        var exitCode = await global::MacroRegimeCli.RunAsync(new[]
        {
            "--build-historical-dataset",
            "--dataset-from",
            "2026-07-01",
            "--dataset-to",
            "2026-07-01"
        });

        Assert.Equal(1, exitCode);
    }

    [Fact]
    public async Task RunAsync_EvaluateHistoricalBaseline_WritesEvaluation()
    {
        var macroDirectory = Path.Combine(directoryPath, "baseline-macro");
        var marketDirectory = Path.Combine(directoryPath, "baseline-market");
        var datasetDirectory = Path.Combine(directoryPath, "baseline-dataset");
        var outputDirectory = Path.Combine(directoryPath, "baseline-output");
        Directory.CreateDirectory(macroDirectory);
        Directory.CreateDirectory(marketDirectory);
        await File.WriteAllTextAsync(Path.Combine(macroDirectory, "macro-data-2026-07-01.json"), SampleMacroDataJson("2026-07-01"));
        await File.WriteAllTextAsync(Path.Combine(marketDirectory, "market-data-2026-07-01.json"), SampleMarketDataJson("2026-07-01", 100m));
        var buildExitCode = await global::MacroRegimeCli.RunAsync(new[]
        {
            "--build-historical-dataset", "--dataset-from", "2026-07-01", "--dataset-to", "2026-07-01",
            "--macro-data-dir", macroDirectory, "--market-data-dir", marketDirectory, "--output-dir", datasetDirectory,
        });

        var exitCode = await global::MacroRegimeCli.RunAsync(new[]
        {
            "--evaluate-historical-baseline",
            "--dataset-file", Path.Combine(datasetDirectory, "historical-dataset-2026-07-01-2026-07-01.json"),
            "--output-dir", outputDirectory,
        });

        Assert.Equal(0, buildExitCode);
        Assert.Equal(0, exitCode);
        var evaluationPath = Path.Combine(outputDirectory, "baseline-evaluation-2026-07-01-2026-07-01.json");
        Assert.True(File.Exists(evaluationPath));
        var evaluation = await File.ReadAllTextAsync(evaluationPath);
        Assert.Contains("\"modelName\": \"CRS Rule-Based Engine\"", evaluation);
        Assert.Contains("\"asOfDate\": \"2026-07-01\"", evaluation);
    }

    public void Dispose()
    {
        if (Directory.Exists(directoryPath))
        {
            Directory.Delete(directoryPath, recursive: true);
        }
    }

    private static async Task WriteBatchInputsAsync(string dataDirectory, string portfolioDirectory, DateOnly asOfDate)
    {
        Directory.CreateDirectory(dataDirectory);
        Directory.CreateDirectory(portfolioDirectory);

        var date = asOfDate.ToString("yyyy-MM-dd");
        await File.WriteAllTextAsync(
            Path.Combine(dataDirectory, $"macro-data-{date}.json"),
            SampleMacroDataJson(date));
        await File.WriteAllTextAsync(
            Path.Combine(portfolioDirectory, $"current-portfolio-{date}.json"),
            SamplePortfolioJson(date));
    }

    private static string SampleMacroDataJson(string asOfDate)
    {
        return $$"""
        {
          "schemaVersion": 1,
          "asOfDate": "{{asOfDate}}",
          "macroObservations": [
            { "seriesCode": "INDPRO_YOY", "name": "Industrial production YoY", "dimension": "Growth", "observationDate": "{{asOfDate}}", "publicationDate": "{{asOfDate}}", "vintageDate": "{{asOfDate}}", "value": 5.0, "source": "Test", "unit": "Percent change" },
            { "seriesCode": "SAHM", "name": "Sahm rule recession indicator", "dimension": "Growth", "observationDate": "{{asOfDate}}", "publicationDate": "{{asOfDate}}", "vintageDate": "{{asOfDate}}", "value": 0.05, "source": "Test", "unit": "Index" },
            { "seriesCode": "T10YIE", "name": "10-year breakeven inflation", "dimension": "Inflation", "observationDate": "{{asOfDate}}", "publicationDate": "{{asOfDate}}", "vintageDate": "{{asOfDate}}", "value": 2.0, "source": "Test", "unit": "Percent" },
            { "seriesCode": "VIX", "name": "CBOE volatility index", "dimension": "Risk", "observationDate": "{{asOfDate}}", "publicationDate": "{{asOfDate}}", "vintageDate": "{{asOfDate}}", "value": 14.0, "source": "Test", "unit": "Index" },
            { "seriesCode": "YC_10Y2Y", "name": "10-year minus 2-year Treasury slope", "dimension": "Monetary", "observationDate": "{{asOfDate}}", "publicationDate": "{{asOfDate}}", "vintageDate": "{{asOfDate}}", "value": 0.5, "source": "Test", "unit": "Percentage points" },
            { "seriesCode": "HY_OAS", "name": "High-yield option-adjusted spread", "dimension": "Credit", "observationDate": "{{asOfDate}}", "publicationDate": "{{asOfDate}}", "vintageDate": "{{asOfDate}}", "value": 3.0, "source": "Test", "unit": "Percent" }
          ],
          "marketObservations": []
        }
        """;
    }

    private static string SampleMarketDataJson(string asOfDate, decimal spyValue)
    {
        return $$"""
        {
          "schemaVersion": 1,
          "asOfDate": "{{asOfDate}}",
          "macroObservations": [],
          "marketObservations": [
            { "symbol": "SPY", "name": "SPDR S&P 500 ETF Trust", "dimension": "Risk", "observationDate": "{{asOfDate}}", "availabilityDate": "{{asOfDate}}", "value": {{spyValue}}, "source": "Test", "unit": "Adjusted close", "proxyRole": "US equity proxy" }
          ]
        }
        """;
    }

    private static string SamplePortfolioJson(string asOfDate)
    {
        return $$"""
        {
          "schemaVersion": 1,
          "asOfDate": "{{asOfDate}}",
          "weights": [
            { "assetClass": "Cash", "weight": 0.05 },
            { "assetClass": "GlobalEquity", "weight": 0.60 },
            { "assetClass": "GovernmentBonds", "weight": 0.25 },
            { "assetClass": "Gold", "weight": 0.10 }
          ]
        }
        """;
    }
}
