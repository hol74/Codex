using MacroRegime.Application.Ports;
using MacroRegime.Domain.Allocations;
using MacroRegime.Domain.Time;

namespace MacroRegime.Infrastructure.Demo;

public sealed class DemoRegimeTiltRuleProvider : IRegimeTiltRuleProvider
{
    public Task<IReadOnlyList<RegimeTiltRule>> GetTiltRulesAsync(AsOfDate asOfDate, CancellationToken cancellationToken = default)
    {
        return Task.FromResult(DemoMacroRegimeInputs.CreateTiltRules());
    }
}
