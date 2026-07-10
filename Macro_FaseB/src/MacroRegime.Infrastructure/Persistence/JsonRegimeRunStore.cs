using System.Text.Json;
using MacroRegime.Application.Ports;
using MacroRegime.Application.Runs;

namespace MacroRegime.Infrastructure.Persistence;

public sealed class JsonRegimeRunStore : IRegimeRunStore
{
    private static readonly JsonSerializerOptions SerializerOptions = new(JsonSerializerDefaults.Web)
    {
        WriteIndented = true
    };

    private readonly string directoryPath;

    public JsonRegimeRunStore(string directoryPath)
    {
        if (string.IsNullOrWhiteSpace(directoryPath))
        {
            throw new ArgumentException("Directory path is required.", nameof(directoryPath));
        }

        this.directoryPath = directoryPath;
    }

    public async Task<string> SaveAsync(RegimeRunDocument document, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(document);

        Directory.CreateDirectory(directoryPath);

        var record = RegimeRunRecordMapper.FromDocument(document);
        var path = GetPath(document.AsOfDate);
        await using var stream = File.Create(path);
        await JsonSerializer.SerializeAsync(stream, record, SerializerOptions, cancellationToken).ConfigureAwait(false);

        return path;
    }

    public async Task<RegimeRunDocument?> LoadAsync(DateOnly asOfDate, CancellationToken cancellationToken = default)
    {
        var path = GetPath(asOfDate);
        if (!File.Exists(path))
        {
            return null;
        }

        await using var stream = File.OpenRead(path);
        RegimeRunRecord? record;
        try
        {
            record = await JsonSerializer
                .DeserializeAsync<RegimeRunRecord>(stream, SerializerOptions, cancellationToken)
                .ConfigureAwait(false);
        }
        catch (JsonException exception)
        {
            throw new InvalidDataException($"Regime run file '{path}' is not valid JSON.", exception);
        }

        if (record is null)
        {
            throw new InvalidDataException($"Regime run file '{path}' is empty.");
        }

        return RegimeRunRecordMapper.ToDocument(record);
    }

    public string GetPath(DateOnly asOfDate)
    {
        if (asOfDate == DateOnly.MinValue)
        {
            throw new ArgumentOutOfRangeException(nameof(asOfDate), "As-of date is required.");
        }

        return Path.Combine(directoryPath, $"regime-run-{asOfDate:yyyy-MM-dd}.json");
    }
}
