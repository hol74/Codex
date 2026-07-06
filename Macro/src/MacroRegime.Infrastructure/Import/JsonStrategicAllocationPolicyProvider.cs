using MacroRegime.Application.Ports;
using MacroRegime.Domain.Allocations;
using MacroRegime.Domain.Time;

namespace MacroRegime.Infrastructure.Import;

public sealed class JsonStrategicAllocationPolicyProvider : IStrategicAllocationPolicyProvider
{
    private readonly string filePath;
    private readonly IStrategicAllocationPolicyProvider? fallbackProvider;
    private readonly bool strict;

    public JsonStrategicAllocationPolicyProvider(string filePath, IStrategicAllocationPolicyProvider? fallbackProvider = null, bool strict = false)
    {
        if (string.IsNullOrWhiteSpace(filePath))
        {
            throw new ArgumentException("File path is required.", nameof(filePath));
        }

        this.filePath = filePath;
        this.fallbackProvider = fallbackProvider;
        this.strict = strict;
    }

    public async Task<StrategicAllocationPolicy?> GetPolicyAsync(AsOfDate asOfDate, CancellationToken cancellationToken = default)
    {
        if (!File.Exists(filePath))
        {
            return await GetFallbackAsync(asOfDate, $"Allocation policy file '{filePath}' does not exist.", cancellationToken).ConfigureAwait(false);
        }

        var record = await JsonConfigurationFileReader
            .ReadRequiredAsync<JsonStrategicAllocationPolicyRecord>(filePath, "Allocation policy", cancellationToken)
            .ConfigureAwait(false);
        return JsonConfigurationRecordMapper.ToStrategicAllocationPolicy(record);
    }

    private async Task<StrategicAllocationPolicy?> GetFallbackAsync(AsOfDate asOfDate, string message, CancellationToken cancellationToken)
    {
        if (strict || fallbackProvider is null)
        {
            throw new InvalidDataException(message);
        }

        return await fallbackProvider.GetPolicyAsync(asOfDate, cancellationToken).ConfigureAwait(false);
    }
}
