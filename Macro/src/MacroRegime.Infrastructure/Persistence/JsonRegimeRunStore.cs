using System.Text.Json;
using MacroRegime.Application.Ports;
using MacroRegime.Domain.Regimes;

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

    public async Task SaveAsync(RegimeSnapshot snapshot, CancellationToken cancellationToken = default)
    {
        ArgumentNullException.ThrowIfNull(snapshot);

        Directory.CreateDirectory(directoryPath);

        var record = RegimeRunRecordMapper.FromSnapshot(snapshot);
        var path = GetPath(snapshot.AsOfDate.Value);
        await using var stream = File.Create(path);
        await JsonSerializer.SerializeAsync(stream, record, SerializerOptions, cancellationToken).ConfigureAwait(false);
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
