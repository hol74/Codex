using System.Security.Cryptography;
using System.Text.Json;
using MacroRegime.Domain.Features;
using MacroRegime.Domain.Models;
using MacroRegime.Domain.Regimes;
using MacroRegime.Infrastructure.Import;

namespace MacroRegime.Infrastructure.External;

public sealed record EvaluateHistoricalBaselineCommand(string DatasetPath, string OutputDirectory);

public sealed record EvaluateHistoricalBaselineResult(string OutputPath, int RowCount, string DatasetSha256);

public sealed record HistoricalBaselineEvaluationRecord(
    int SchemaVersion,
    string DatasetFileName,
    string DatasetSha256,
    string ModelName,
    string ModelVersion,
    DateOnly ModelEffectiveFrom,
    string FeatureSetName,
    string FeatureSetVersion,
    decimal ConfirmationThreshold,
    IReadOnlyList<HistoricalBaselineEvaluationRowRecord> Rows);

public sealed record HistoricalBaselineEvaluationRowRecord(
    DateOnly AsOfDate,
    string PrimaryRegime,
    string OperationalRegime,
    decimal Confidence,
    decimal CompositeScore,
    string Status,
    IReadOnlyList<HistoricalBaselineProbabilityRecord> Probabilities,
    IReadOnlyList<HistoricalBaselineFeatureRecord> FeatureScores,
    IReadOnlyList<string> Warnings);

public sealed record HistoricalBaselineProbabilityRecord(string Regime, decimal Probability, int Rank);

public sealed record HistoricalBaselineFeatureRecord(string FeatureCode, decimal RawValue, decimal NormalizedScore);

public sealed class HistoricalBaselineEvaluator
{
    private const int CurrentSchemaVersion = 1;
    private static readonly JsonSerializerOptions SerializerOptions = new(JsonSerializerDefaults.Web) { WriteIndented = true };
    private readonly BaselineRegimeDetector detector;
    private readonly FeatureSetVersion featureSetVersion;
    private readonly ModelVersion modelVersion;

    public HistoricalBaselineEvaluator(
        BaselineRegimeDetector detector,
        FeatureSetVersion featureSetVersion,
        ModelVersion modelVersion)
    {
        this.detector = detector ?? throw new ArgumentNullException(nameof(detector));
        this.featureSetVersion = featureSetVersion ?? throw new ArgumentNullException(nameof(featureSetVersion));
        this.modelVersion = modelVersion ?? throw new ArgumentNullException(nameof(modelVersion));
    }

    public async Task<EvaluateHistoricalBaselineResult> EvaluateAsync(
        EvaluateHistoricalBaselineCommand command,
        CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(command);
        if (string.IsNullOrWhiteSpace(command.DatasetPath) || string.IsNullOrWhiteSpace(command.OutputDirectory))
        {
            throw new ArgumentException("Historical baseline dataset and output paths are required.", nameof(command));
        }

        var datasetPath = Path.GetFullPath(command.DatasetPath);
        var datasetBytes = await File.ReadAllBytesAsync(datasetPath, cancellationToken).ConfigureAwait(false);
        HistoricalDatasetRecord dataset;
        try
        {
            dataset = JsonSerializer.Deserialize<HistoricalDatasetRecord>(datasetBytes, SerializerOptions)
                ?? throw new InvalidDataException($"Historical dataset '{datasetPath}' is empty.");
        }
        catch (JsonException exception)
        {
            throw new InvalidDataException($"Historical dataset '{datasetPath}' is not valid JSON.", exception);
        }

        if (dataset.SchemaVersion != CurrentSchemaVersion)
        {
            throw new InvalidDataException($"Unsupported historical dataset schema version {dataset.SchemaVersion}.");
        }

        var rows = dataset.Rows.Select(row =>
        {
            var snapshot = JsonDataSnapshotRecordMapper.ToSnapshot(new JsonDataSnapshotRecord(
                JsonDataSnapshotRecordMapper.CurrentSchemaVersion,
                row.AsOfDate,
                row.MacroObservations,
                row.MarketObservations));
            var result = detector.Detect(snapshot, featureSetVersion, modelVersion);
            return new HistoricalBaselineEvaluationRowRecord(
                row.AsOfDate,
                result.PrimaryRegime.ToString(),
                result.OperationalRegime.ToString(),
                result.Confidence.Value,
                result.CompositeScore.Value,
                result.Status,
                result.Probabilities.Select(item => new HistoricalBaselineProbabilityRecord(
                    item.Regime.ToString(), item.Probability.Value, item.Rank)).ToArray(),
                result.FeatureScores.Select(item => new HistoricalBaselineFeatureRecord(
                    item.FeatureCode, item.RawValue, item.NormalizedScore.Value)).ToArray(),
                result.Warnings);
        }).ToArray();

        var datasetSha256 = Convert.ToHexString(SHA256.HashData(datasetBytes)).ToLowerInvariant();
        var confirmationThreshold = BaselineRegimeParameters.From(modelVersion).ConfirmationThreshold;
        var evaluation = new HistoricalBaselineEvaluationRecord(
            CurrentSchemaVersion,
            Path.GetFileName(datasetPath),
            datasetSha256,
            modelVersion.Name,
            modelVersion.Version,
            modelVersion.EffectiveFrom,
            featureSetVersion.Name,
            featureSetVersion.Version,
            confirmationThreshold,
            rows);

        var outputDirectory = Path.GetFullPath(command.OutputDirectory);
        Directory.CreateDirectory(outputDirectory);
        var outputPath = Path.Combine(outputDirectory, $"baseline-evaluation-{dataset.From:yyyy-MM-dd}-{dataset.To:yyyy-MM-dd}.json");
        await using var output = File.Create(outputPath);
        await JsonSerializer.SerializeAsync(output, evaluation, SerializerOptions, cancellationToken).ConfigureAwait(false);
        return new EvaluateHistoricalBaselineResult(outputPath, rows.Length, datasetSha256);
    }
}
