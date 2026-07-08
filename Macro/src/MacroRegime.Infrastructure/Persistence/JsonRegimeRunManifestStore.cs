using System.Text.Json;
using MacroRegime.Application.Ports;

namespace MacroRegime.Infrastructure.Persistence;

public sealed class JsonRegimeRunManifestStore : IRegimeRunManifestStore
{
    public const int CurrentSchemaVersion = 1;

    private static readonly JsonSerializerOptions SerializerOptions = new(JsonSerializerDefaults.Web)
    {
        WriteIndented = true
    };

    private readonly string filePath;

    public JsonRegimeRunManifestStore(string filePath)
    {
        if (string.IsNullOrWhiteSpace(filePath))
        {
            throw new ArgumentException("Manifest file path is required.", nameof(filePath));
        }

        this.filePath = filePath;
    }

    public string FilePath => filePath;

    public async Task UpsertAsync(RegimeRunManifestEntry entry, CancellationToken cancellationToken = default)
    {
        Validate(entry);

        var record = await ReadRecordAsync(cancellationToken).ConfigureAwait(false);
        var entries = record.Entries
            .Where(existing => existing.AsOfDate != entry.AsOfDate)
            .Append(ToRecord(entry))
            .OrderByDescending(existing => existing.AsOfDate)
            .ToArray();

        var updated = new RegimeRunManifestRecord(CurrentSchemaVersion, entries);
        var directory = Path.GetDirectoryName(filePath);
        if (!string.IsNullOrWhiteSpace(directory))
        {
            Directory.CreateDirectory(directory);
        }

        await using var stream = File.Create(filePath);
        await JsonSerializer.SerializeAsync(stream, updated, SerializerOptions, cancellationToken).ConfigureAwait(false);
    }

    public async Task<IReadOnlyList<RegimeRunManifestEntry>> ListAsync(CancellationToken cancellationToken = default)
    {
        var record = await ReadRecordAsync(cancellationToken).ConfigureAwait(false);
        return record.Entries
            .OrderByDescending(entry => entry.AsOfDate)
            .Select(ToEntry)
            .ToArray();
    }

    private async Task<RegimeRunManifestRecord> ReadRecordAsync(CancellationToken cancellationToken)
    {
        if (!File.Exists(filePath))
        {
            return new RegimeRunManifestRecord(CurrentSchemaVersion, Array.Empty<RegimeRunManifestEntryRecord>());
        }

        await using var stream = File.OpenRead(filePath);
        var record = await JsonSerializer
            .DeserializeAsync<RegimeRunManifestRecord>(stream, SerializerOptions, cancellationToken)
            .ConfigureAwait(false);

        if (record is null)
        {
            throw new InvalidDataException($"Manifest file '{filePath}' is empty.");
        }

        if (record.SchemaVersion != CurrentSchemaVersion)
        {
            throw new InvalidDataException(
                $"Manifest file '{filePath}' has unsupported schema version {record.SchemaVersion}; expected {CurrentSchemaVersion}.");
        }

        return record;
    }

    private static RegimeRunManifestEntryRecord ToRecord(RegimeRunManifestEntry entry)
    {
        return new RegimeRunManifestEntryRecord(
            entry.AsOfDate,
            entry.RunLocation.Trim(),
            entry.ReportLocation.Trim(),
            entry.DataSourceKind.Trim(),
            entry.DataSourceDescription.Trim(),
            string.IsNullOrWhiteSpace(entry.DataSourceReference) ? null : entry.DataSourceReference.Trim(),
            entry.ModelName.Trim(),
            entry.ModelVersion.Trim(),
            entry.FeatureSetName.Trim(),
            entry.FeatureSetVersion.Trim(),
            entry.PrimaryRegime.Trim(),
            entry.OperationalRegime.Trim(),
            entry.Confidence,
            entry.CompositeScore,
            entry.Status.Trim(),
            entry.AllocationSuggestion.Trim(),
            entry.Turnover,
            entry.EstimatedCost,
            entry.WarningCount);
    }

    private static RegimeRunManifestEntry ToEntry(RegimeRunManifestEntryRecord record)
    {
        return new RegimeRunManifestEntry(
            record.AsOfDate,
            record.RunLocation,
            record.ReportLocation,
            record.DataSourceKind,
            record.DataSourceDescription,
            record.DataSourceReference,
            record.ModelName,
            record.ModelVersion,
            record.FeatureSetName,
            record.FeatureSetVersion,
            record.PrimaryRegime,
            record.OperationalRegime,
            record.Confidence,
            record.CompositeScore,
            record.Status,
            record.AllocationSuggestion,
            record.Turnover,
            record.EstimatedCost,
            record.WarningCount);
    }

    private static void Validate(RegimeRunManifestEntry entry)
    {
        if (entry.AsOfDate == DateOnly.MinValue)
        {
            throw new ArgumentOutOfRangeException(nameof(entry), "As-of date is required.");
        }

        Require(entry.RunLocation, nameof(entry.RunLocation));
        Require(entry.ReportLocation, nameof(entry.ReportLocation));
        Require(entry.DataSourceKind, nameof(entry.DataSourceKind));
        Require(entry.ModelName, nameof(entry.ModelName));
        Require(entry.ModelVersion, nameof(entry.ModelVersion));
        Require(entry.FeatureSetName, nameof(entry.FeatureSetName));
        Require(entry.FeatureSetVersion, nameof(entry.FeatureSetVersion));
        Require(entry.PrimaryRegime, nameof(entry.PrimaryRegime));
        Require(entry.OperationalRegime, nameof(entry.OperationalRegime));
        Require(entry.Status, nameof(entry.Status));
        Require(entry.AllocationSuggestion, nameof(entry.AllocationSuggestion));

        if (entry.WarningCount < 0)
        {
            throw new ArgumentOutOfRangeException(nameof(entry), "Warning count cannot be negative.");
        }
    }

    private static void Require(string value, string name)
    {
        if (string.IsNullOrWhiteSpace(value))
        {
            throw new ArgumentException($"{name} is required.", name);
        }
    }
}
