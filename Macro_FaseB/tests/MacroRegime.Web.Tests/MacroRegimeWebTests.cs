using Microsoft.AspNetCore.Hosting;
using Microsoft.AspNetCore.Mvc.Testing;

namespace MacroRegime.Web.Tests;

public sealed class MacroRegimeWebTests : IClassFixture<MacroRegimeWebFactory>
{
    private readonly MacroRegimeWebFactory factory;

    public MacroRegimeWebTests(MacroRegimeWebFactory factory)
    {
        this.factory = factory;
    }

    [Fact]
    public async Task Dashboard_RunsPipelineAndRendersRegimeSummary()
    {
        using var client = factory.CreateClient();

        var response = await client.GetAsync("/");
        var content = await response.Content.ReadAsStringAsync();

        Assert.Equal(System.Net.HttpStatusCode.OK, response.StatusCode);
        Assert.Contains("Macro Regime", content);
        Assert.Contains("Run History", content);
        Assert.Contains("Goldilocks", content);
        Assert.Contains("Active configuration", content);
    }

    [Fact]
    public async Task RunDetail_LoadsStoredRunFromJson_WithoutRerunningPipeline()
    {
        using var client = factory.CreateClient();

        // Produce and index the run first.
        var runResponse = await client.GetAsync("/?asOfDate=2026-07-01");
        Assert.Equal(System.Net.HttpStatusCode.OK, runResponse.StatusCode);

        var response = await client.GetAsync("/RunDetail?asOfDate=2026-07-01");
        var content = await response.Content.ReadAsStringAsync();

        Assert.Equal(System.Net.HttpStatusCode.OK, response.StatusCode);
        Assert.Contains("Stored Run Detail", content);
        Assert.Contains("Loaded from saved run JSON", content);
        Assert.Contains("Goldilocks", content);
        Assert.Contains("Allocation Proposal", content);
        Assert.Contains("regime-run-2026-07-01.json", content);
    }

    [Fact]
    public async Task RunDetail_ReportsMissingRun_WhenNoStoredRunExists()
    {
        using var client = factory.CreateClient();

        var response = await client.GetAsync("/RunDetail?asOfDate=1999-01-01");
        var content = await response.Content.ReadAsStringAsync();

        Assert.Equal(System.Net.HttpStatusCode.OK, response.StatusCode);
        Assert.Contains("Stored run unavailable", content);
        Assert.Contains("No stored run found", content);
    }

    [Fact]
    public async Task CompareRuns_ComparesTwoStoredRuns()
    {
        using var client = factory.CreateClient();

        // Produce two runs: the imported sample date and a later demo-fallback date.
        Assert.Equal(System.Net.HttpStatusCode.OK, (await client.GetAsync("/?asOfDate=2026-07-01")).StatusCode);
        Assert.Equal(System.Net.HttpStatusCode.OK, (await client.GetAsync("/?asOfDate=2026-08-03")).StatusCode);

        var response = await client.GetAsync("/CompareRuns?baseline=2026-07-01&comparison=2026-08-03");
        var content = await response.Content.ReadAsStringAsync();

        Assert.Equal(System.Net.HttpStatusCode.OK, response.StatusCode);
        Assert.Contains("Compare Runs", content);
        Assert.Contains("Probability Deltas", content);
        Assert.Contains("Feature Deltas", content);
        Assert.Contains("Allocation Comparison", content);
    }

    [Fact]
    public async Task CompareRuns_ReportsMissingBaselineRun()
    {
        using var client = factory.CreateClient();

        Assert.Equal(System.Net.HttpStatusCode.OK, (await client.GetAsync("/?asOfDate=2026-07-01")).StatusCode);

        var response = await client.GetAsync("/CompareRuns?baseline=1999-01-01&comparison=2026-07-01");
        var content = await response.Content.ReadAsStringAsync();

        Assert.Equal(System.Net.HttpStatusCode.OK, response.StatusCode);
        Assert.Contains("Comparison unavailable", content);
        Assert.Contains("No stored run found", content);
    }

    [Fact]
    public async Task ImportDiagnostics_RendersValidationReport()
    {
        using var client = factory.CreateClient();

        var response = await client.GetAsync("/ImportDiagnostics?asOfDate=2026-07-01");
        var content = await response.Content.ReadAsStringAsync();

        Assert.Equal(System.Net.HttpStatusCode.OK, response.StatusCode);
        Assert.Contains("Import Diagnostics", content);
        Assert.Contains("Import Validation Report", content);
        Assert.Contains("Macro data", content);
        Assert.Contains("Current portfolio", content);
        Assert.Contains("OK:", content);
    }
}

public sealed class MacroRegimeWebFactory : WebApplicationFactory<Program>, IDisposable
{
    private readonly string outputDirectory =
        Path.Combine(Path.GetTempPath(), "MacroRegimeWebTests", Guid.NewGuid().ToString("N"));

    protected override void ConfigureWebHost(IWebHostBuilder builder)
    {
        builder.UseEnvironment("Development");
        builder.UseSetting("MacroRegime:OutputDirectory", outputDirectory);
        // Dates other than the sample as-of date must fall back to deterministic demo data/config.
        builder.UseSetting("MacroRegime:StrictData", "false");
        builder.UseSetting("MacroRegime:StrictConfig", "false");
    }

    public new void Dispose()
    {
        base.Dispose();
        if (Directory.Exists(outputDirectory))
        {
            Directory.Delete(outputDirectory, recursive: true);
        }
    }
}
