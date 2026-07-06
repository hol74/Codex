using MacroRegime.Application.Ports;
using MacroRegime.Domain.Allocations;
using MacroRegime.Domain.Time;

namespace MacroRegime.Infrastructure.Import;

public sealed class JsonRegimeTiltRuleProvider : IRegimeTiltRuleProvider
{
    private readonly string filePath;
    private readonly IRegimeTiltRuleProvider? fallbackProvider;
    private readonly bool strict;

    public JsonRegimeTiltRuleProvider(string filePath, IRegimeTiltRuleProvider? fallbackProvider = null, bool strict = false)
    {
        if (string.IsNullOrWhiteSpace(filePath))
        {
            throw new ArgumentException("File path is required.", nameof(filePath));
        }

        this.filePath = filePath;
        this.fallbackProvider = fallbackProvider;
        this.strict = strict;
    }

    public async Task<IReadOnlyList<RegimeTiltRule>> GetTiltRulesAsync(AsOfDate asOfDate, CancellationToken cancellationToken = default)
    {
        if (!File.Exists(filePath))
        {
            return await GetFallbackAsync(asOfDate, $"Regime tilt rules file '{filePath}' does not exist.", cancellationToken).ConfigureAwait(false);
        }

        var record = await JsonConfigurationFileReader
            .ReadRequiredAsync<JsonRegimeTiltRulesRecord>(filePath, "Regime tilt rules", cancellationToken)
            .ConfigureAwait(false);
        return JsonConfigurationRecordMapper.ToTiltRules(record);
    }

    private async Task<IReadOnlyList<RegimeTiltRule>> GetFallbackAsync(AsOfDate asOfDate, string message, CancellationToken cancellationToken)
    {
        if (strict || fallbackProvider is null)
        {
            throw new InvalidDataException(message);
        }

        return await fallbackProvider.GetTiltRulesAsync(asOfDate, cancellationToken).ConfigureAwait(false);
    }
}
