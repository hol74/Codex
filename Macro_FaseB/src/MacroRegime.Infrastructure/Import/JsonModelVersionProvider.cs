using MacroRegime.Application.Ports;
using MacroRegime.Domain.Models;
using MacroRegime.Domain.Time;

namespace MacroRegime.Infrastructure.Import;

public sealed class JsonModelVersionProvider : IModelVersionProvider
{
    private readonly string filePath;
    private readonly IModelVersionProvider? fallbackProvider;
    private readonly bool strict;

    public JsonModelVersionProvider(string filePath, IModelVersionProvider? fallbackProvider = null, bool strict = false)
    {
        if (string.IsNullOrWhiteSpace(filePath))
        {
            throw new ArgumentException("File path is required.", nameof(filePath));
        }

        this.filePath = filePath;
        this.fallbackProvider = fallbackProvider;
        this.strict = strict;
    }

    public async Task<ModelVersion?> GetActiveModelVersionAsync(AsOfDate asOfDate, CancellationToken cancellationToken = default)
    {
        if (!File.Exists(filePath))
        {
            return await GetFallbackAsync(asOfDate, $"Model version file '{filePath}' does not exist.", cancellationToken).ConfigureAwait(false);
        }

        var record = await JsonConfigurationFileReader
            .ReadRequiredAsync<JsonModelVersionRecord>(filePath, "Model version", cancellationToken)
            .ConfigureAwait(false);
        var modelVersion = JsonConfigurationRecordMapper.ToModelVersion(record);

        if (modelVersion.EffectiveFrom > asOfDate.Value)
        {
            var message = $"Model version file '{filePath}' is effective from {modelVersion.EffectiveFrom:yyyy-MM-dd}; expected a version effective on or before {asOfDate.Value:yyyy-MM-dd}.";
            return await GetFallbackAsync(asOfDate, message, cancellationToken).ConfigureAwait(false);
        }

        return modelVersion;
    }

    private async Task<ModelVersion?> GetFallbackAsync(AsOfDate asOfDate, string message, CancellationToken cancellationToken)
    {
        if (strict || fallbackProvider is null)
        {
            throw new InvalidDataException(message);
        }

        return await fallbackProvider.GetActiveModelVersionAsync(asOfDate, cancellationToken).ConfigureAwait(false);
    }
}
