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

    public void Dispose()
    {
        if (Directory.Exists(directoryPath))
        {
            Directory.Delete(directoryPath, recursive: true);
        }
    }
}
