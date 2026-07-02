using MacroRegime.Domain.Allocations;
using MacroRegime.Domain.Time;

namespace MacroRegime.Application.Ports;

public interface ICurrentPortfolioProvider
{
    Task<CurrentPortfolio?> GetCurrentPortfolioAsync(AsOfDate asOfDate, CancellationToken cancellationToken = default);
}
