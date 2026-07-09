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
            { "seriesCode": "ISM_PMI", "name": "ISM manufacturing PMI", "dimension": "Growth", "observationDate": "{{asOfDate}}", "publicationDate": "{{asOfDate}}", "vintageDate": "{{asOfDate}}", "value": 55.0, "source": "Test", "unit": "Index" },
            { "seriesCode": "SAHM", "name": "Sahm rule recession indicator", "dimension": "Growth", "observationDate": "{{asOfDate}}", "publicationDate": "{{asOfDate}}", "vintageDate": "{{asOfDate}}", "value": 0.05, "source": "Test", "unit": "Index" },
            { "seriesCode": "T10YIE", "name": "10-year breakeven inflation", "dimension": "Inflation", "observationDate": "{{asOfDate}}", "publicationDate": "{{asOfDate}}", "vintageDate": "{{asOfDate}}", "value": 2.0, "source": "Test", "unit": "Percent" },
            { "seriesCode": "VIX", "name": "CBOE volatility index", "dimension": "Risk", "observationDate": "{{asOfDate}}", "publicationDate": "{{asOfDate}}", "vintageDate": "{{asOfDate}}", "value": 14.0, "source": "Test", "unit": "Index" },
            { "seriesCode": "YC_10Y2Y", "name": "10-year minus 2-year Treasury slope", "dimension": "Monetary", "observationDate": "{{asOfDate}}", "publicationDate": "{{asOfDate}}", "vintageDate": "{{asOfDate}}", "value": 0.5, "source": "Test", "unit": "Percentage points" },
            { "seriesCode": "HY_OAS", "name": "High-yield option-adjusted spread", "dimension": "Credit", "observationDate": "{{asOfDate}}", "publicationDate": "{{asOfDate}}", "vintageDate": "{{asOfDate}}", "value": 300.0, "source": "Test", "unit": "Basis points" }
          ],
          "marketObservations": []
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
