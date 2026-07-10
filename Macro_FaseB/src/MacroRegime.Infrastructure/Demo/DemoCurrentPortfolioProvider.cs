using MacroRegime.Application.Ports;
using MacroRegime.Domain.Allocations;
using MacroRegime.Domain.Time;

namespace MacroRegime.Infrastructure.Demo;

public sealed class DemoCurrentPortfolioProvider : ICurrentPortfolioProvider
{
    public Task<CurrentPortfolio?> GetCurrentPortfolioAsync(AsOfDate asOfDate, CancellationToken cancellationToken = default)
    {
        return Task.FromResult<CurrentPortfolio?>(DemoMacroRegimeInputs.CreateCurrentPortfolio());
    }
}
