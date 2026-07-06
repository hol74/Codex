using MacroRegime.Application.Ports;
using MacroRegime.Domain.Allocations;
using MacroRegime.Domain.Time;

namespace MacroRegime.Infrastructure.Import;

public sealed class JsonCurrentPortfolioProvider : ICurrentPortfolioProvider
{
    private readonly string filePath;
    private readonly ICurrentPortfolioProvider? fallbackProvider;
    private readonly bool strict;

    public JsonCurrentPortfolioProvider(string filePath, ICurrentPortfolioProvider? fallbackProvider = null, bool strict = false)
    {
        if (string.IsNullOrWhiteSpace(filePath))
        {
            throw new ArgumentException("File path is required.", nameof(filePath));
        }

        this.filePath = filePath;
        this.fallbackProvider = fallbackProvider;
        this.strict = strict;
    }

    public async Task<CurrentPortfolio?> GetCurrentPortfolioAsync(AsOfDate asOfDate, CancellationToken cancellationToken = default)
    {
        if (!File.Exists(filePath))
        {
            return await GetFallbackAsync(asOfDate, $"Current portfolio file '{filePath}' does not exist.", cancellationToken).ConfigureAwait(false);
        }

        var record = await JsonConfigurationFileReader
            .ReadRequiredAsync<JsonCurrentPortfolioRecord>(filePath, "Current portfolio", cancellationToken)
            .ConfigureAwait(false);

        if (record.AsOfDate != asOfDate.Value)
        {
            var message = $"Current portfolio file '{filePath}' has as-of date {record.AsOfDate:yyyy-MM-dd}; expected {asOfDate.Value:yyyy-MM-dd}.";
            return await GetFallbackAsync(asOfDate, message, cancellationToken).ConfigureAwait(false);
        }

        return JsonConfigurationRecordMapper.ToCurrentPortfolio(record);
    }

    private async Task<CurrentPortfolio?> GetFallbackAsync(AsOfDate asOfDate, string message, CancellationToken cancellationToken)
    {
        if (strict || fallbackProvider is null)
        {
            throw new InvalidDataException(message);
        }

        return await fallbackProvider.GetCurrentPortfolioAsync(asOfDate, cancellationToken).ConfigureAwait(false);
    }
}
