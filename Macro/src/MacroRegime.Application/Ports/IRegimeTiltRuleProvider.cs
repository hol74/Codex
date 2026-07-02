using MacroRegime.Domain.Allocations;
using MacroRegime.Domain.Time;

namespace MacroRegime.Application.Ports;

public interface IRegimeTiltRuleProvider
{
    Task<IReadOnlyList<RegimeTiltRule>> GetTiltRulesAsync(AsOfDate asOfDate, CancellationToken cancellationToken = default);
}
