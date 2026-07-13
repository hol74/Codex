using System.Text.Json;
using MacroRegime.Infrastructure.Demo;
using MacroRegime.Infrastructure.External;
using MacroRegime.Infrastructure.Import;
using MacroRegime.Domain.Regimes;

namespace MacroRegime.Infrastructure.Tests.External;

public sealed class HistoricalBaselineEvaluatorTests : IDisposable
{
    private static readonly JsonSerializerOptions SerializerOptions = new(JsonSerializerDefaults.Web) { WriteIndented = true };
    private readonly string directory = Path.Combine(Path.GetTempPath(), "HistoricalBaselineEvaluatorTests", Guid.NewGuid().ToString("N"));

    [Fact]
    public async Task EvaluateAsync_RunsAuthoritativeBaseline_AndLinksDatasetHash()
    {
        Directory.CreateDirectory(directory);
        var datasetPath = Path.Combine(directory, "historical-dataset.json");
        var asOf = new DateOnly(2025, 1, 31);
        var macro = new[]
        {
            Macro("INDPRO_YOY", "Growth", 4m, asOf),
            Macro("SAHM", "Growth", 0.05m, asOf),
            Macro("T10YIE", "Inflation", 2m, asOf),
            Macro("VIX", "Risk", 14m, asOf),
            Macro("YC_10Y2Y", "Monetary", 0.5m, asOf),
            Macro("HY_OAS", "Credit", 3m, asOf),
        };
        var dataset = new HistoricalDatasetRecord(
            1, asOf, asOf, new[] { 28 },
            new[] { new HistoricalDatasetRowRecord(asOf, macro, Array.Empty<JsonMarketObservationRecord>(), Array.Empty<HistoricalForwardReturnRecord>()) });
        await File.WriteAllTextAsync(datasetPath, JsonSerializer.Serialize(dataset, SerializerOptions));
        var evaluator = new HistoricalBaselineEvaluator(
            new BaselineRegimeDetector(),
            DemoMacroRegimeInputs.CreateFeatureSetVersion(),
            DemoMacroRegimeInputs.CreateModelVersion());

        var result = await evaluator.EvaluateAsync(new EvaluateHistoricalBaselineCommand(datasetPath, directory));

        Assert.Equal(1, result.RowCount);
        Assert.Equal(64, result.DatasetSha256.Length);
        var output = JsonDocument.Parse(await File.ReadAllTextAsync(result.OutputPath));
        Assert.Equal(result.DatasetSha256, output.RootElement.GetProperty("datasetSha256").GetString());
        Assert.Equal("CRS Rule-Based Engine", output.RootElement.GetProperty("modelName").GetString());
        Assert.Equal(5, output.RootElement.GetProperty("rows")[0].GetProperty("featureScores").GetArrayLength());
        Assert.Equal(6, output.RootElement.GetProperty("rows")[0].GetProperty("probabilities").GetArrayLength());
    }

    public void Dispose()
    {
        if (Directory.Exists(directory))
        {
            Directory.Delete(directory, recursive: true);
        }
    }

    private static JsonMacroObservationRecord Macro(string code, string dimension, decimal value, DateOnly asOf) =>
        new(code, code, dimension, asOf.AddDays(-1), asOf, asOf, value, "test", "Index");
}
