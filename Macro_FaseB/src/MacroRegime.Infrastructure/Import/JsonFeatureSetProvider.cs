using MacroRegime.Application.Ports;
using MacroRegime.Domain.Features;
using MacroRegime.Domain.Time;

namespace MacroRegime.Infrastructure.Import;

public sealed class JsonFeatureSetProvider : IFeatureSetProvider
{
    private readonly string filePath;
    private readonly IFeatureSetProvider? fallbackProvider;
    private readonly bool strict;

    public JsonFeatureSetProvider(string filePath, IFeatureSetProvider? fallbackProvider = null, bool strict = false)
    {
        if (string.IsNullOrWhiteSpace(filePath))
        {
            throw new ArgumentException("File path is required.", nameof(filePath));
        }

        this.filePath = filePath;
        this.fallbackProvider = fallbackProvider;
        this.strict = strict;
    }

    public async Task<FeatureSetVersion?> GetActiveFeatureSetAsync(AsOfDate asOfDate, CancellationToken cancellationToken = default)
    {
        if (!File.Exists(filePath))
        {
            return await GetFallbackAsync(asOfDate, $"Feature set file '{filePath}' does not exist.", cancellationToken).ConfigureAwait(false);
        }

        var record = await JsonConfigurationFileReader
            .ReadRequiredAsync<JsonFeatureSetVersionRecord>(filePath, "Feature set", cancellationToken)
            .ConfigureAwait(false);
        return JsonConfigurationRecordMapper.ToFeatureSetVersion(record);
    }

    private async Task<FeatureSetVersion?> GetFallbackAsync(AsOfDate asOfDate, string message, CancellationToken cancellationToken)
    {
        if (strict || fallbackProvider is null)
        {
            throw new InvalidDataException(message);
        }

        return await fallbackProvider.GetActiveFeatureSetAsync(asOfDate, cancellationToken).ConfigureAwait(false);
    }
}
