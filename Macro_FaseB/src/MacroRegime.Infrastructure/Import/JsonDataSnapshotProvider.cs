using System.Text.Json;
using MacroRegime.Application.Ports;
using MacroRegime.Application.Regimes;
using MacroRegime.Domain.Data;
using MacroRegime.Domain.Time;

namespace MacroRegime.Infrastructure.Import;

public sealed class JsonDataSnapshotProvider : IDataSnapshotProvider, IDataSnapshotSourceInfoProvider
{
    private static readonly JsonSerializerOptions SerializerOptions = new(JsonSerializerDefaults.Web);

    private readonly string filePath;
    private readonly IDataSnapshotProvider? fallbackProvider;
    private readonly bool strict;

    public JsonDataSnapshotProvider(string filePath, IDataSnapshotProvider? fallbackProvider = null, bool strict = false)
    {
        if (string.IsNullOrWhiteSpace(filePath))
        {
            throw new ArgumentException("File path is required.", nameof(filePath));
        }

        this.filePath = filePath;
        this.fallbackProvider = fallbackProvider;
        this.strict = strict;
    }

    public DataSnapshotSourceInfo LastSourceInfo { get; private set; } = DataSnapshotSourceInfo.Unspecified();

    public async Task<DataSnapshot?> GetSnapshotAsync(AsOfDate asOfDate, CancellationToken cancellationToken = default)
    {
        if (!File.Exists(filePath))
        {
            if (strict)
            {
                throw new InvalidDataException($"Data snapshot import file '{filePath}' does not exist.");
            }

            return await GetFallbackAsync(
                asOfDate,
                $"Data snapshot import file '{filePath}' does not exist; demo fallback used.",
                cancellationToken).ConfigureAwait(false);
        }

        await using var stream = File.OpenRead(filePath);
        JsonDataSnapshotRecord? record;
        try
        {
            record = await JsonSerializer
                .DeserializeAsync<JsonDataSnapshotRecord>(stream, SerializerOptions, cancellationToken)
                .ConfigureAwait(false);
        }
        catch (JsonException exception)
        {
            throw new InvalidDataException($"Data snapshot import file '{filePath}' is not valid JSON.", exception);
        }

        if (record is null)
        {
            throw new InvalidDataException($"Data snapshot import file '{filePath}' is empty.");
        }

        var snapshot = JsonDataSnapshotRecordMapper.ToSnapshot(record);
        if (snapshot.AsOfDate.Value != asOfDate.Value)
        {
            if (strict)
            {
                throw new InvalidDataException($"Data snapshot import file '{filePath}' has as-of date {snapshot.AsOfDate.Value:yyyy-MM-dd}; expected {asOfDate.Value:yyyy-MM-dd}.");
            }

            return await GetFallbackAsync(
                asOfDate,
                $"Data snapshot import file '{filePath}' has as-of date {snapshot.AsOfDate.Value:yyyy-MM-dd}; expected {asOfDate.Value:yyyy-MM-dd}. Demo fallback used.",
                cancellationToken).ConfigureAwait(false);
        }

        LastSourceInfo = DataSnapshotSourceInfo.Imported(filePath);
        return snapshot;
    }

    private async Task<DataSnapshot?> GetFallbackAsync(
        AsOfDate asOfDate,
        string fallbackReason,
        CancellationToken cancellationToken)
    {
        if (fallbackProvider is null)
        {
            LastSourceInfo = DataSnapshotSourceInfo.EmptyFallback(fallbackReason, filePath);
            return null;
        }

        var snapshot = await fallbackProvider.GetSnapshotAsync(asOfDate, cancellationToken).ConfigureAwait(false);
        LastSourceInfo = snapshot is null
            ? DataSnapshotSourceInfo.EmptyFallback(fallbackReason, filePath)
            : DataSnapshotSourceInfo.DemoFallback(fallbackReason, filePath);

        return snapshot;
    }
}
