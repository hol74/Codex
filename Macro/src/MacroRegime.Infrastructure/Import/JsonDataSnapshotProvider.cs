using System.Text.Json;
using MacroRegime.Application.Ports;
using MacroRegime.Domain.Data;
using MacroRegime.Domain.Time;

namespace MacroRegime.Infrastructure.Import;

public sealed class JsonDataSnapshotProvider : IDataSnapshotProvider
{
    private static readonly JsonSerializerOptions SerializerOptions = new(JsonSerializerDefaults.Web);

    private readonly string filePath;
    private readonly IDataSnapshotProvider? fallbackProvider;

    public JsonDataSnapshotProvider(string filePath, IDataSnapshotProvider? fallbackProvider = null)
    {
        if (string.IsNullOrWhiteSpace(filePath))
        {
            throw new ArgumentException("File path is required.", nameof(filePath));
        }

        this.filePath = filePath;
        this.fallbackProvider = fallbackProvider;
    }

    public async Task<DataSnapshot?> GetSnapshotAsync(AsOfDate asOfDate, CancellationToken cancellationToken = default)
    {
        if (!File.Exists(filePath))
        {
            return await GetFallbackAsync(asOfDate, cancellationToken).ConfigureAwait(false);
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
            return await GetFallbackAsync(asOfDate, cancellationToken).ConfigureAwait(false);
        }

        return snapshot;
    }

    private Task<DataSnapshot?> GetFallbackAsync(AsOfDate asOfDate, CancellationToken cancellationToken)
    {
        return fallbackProvider is null
            ? Task.FromResult<DataSnapshot?>(null)
            : fallbackProvider.GetSnapshotAsync(asOfDate, cancellationToken);
    }
}
