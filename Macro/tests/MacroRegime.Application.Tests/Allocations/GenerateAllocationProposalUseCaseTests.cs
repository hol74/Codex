using MacroRegime.Application.Allocations;
using MacroRegime.Application.Ports;
using MacroRegime.Domain.Allocations;
using MacroRegime.Domain.Time;

namespace MacroRegime.Application.Tests.Allocations;

public sealed class GenerateAllocationProposalUseCaseTests
{
    [Fact]
    public async Task ExecuteAsync_GeneratesProposalFromApplicationProviders()
    {
        var snapshot = AllocationProposalTestFixtures.CreateSnapshot();
        var policyProvider = new FakePolicyProvider(AllocationProposalTestFixtures.CreatePolicy());
        var portfolioProvider = new FakePortfolioProvider(AllocationProposalTestFixtures.CreatePortfolio());
        var tiltProvider = new FakeTiltRuleProvider(AllocationProposalTestFixtures.CreateTiltRules());
        var useCase = new GenerateAllocationProposalUseCase(
            policyProvider,
            portfolioProvider,
            tiltProvider,
            new AllocationProposalService());

        var result = await useCase.ExecuteAsync(new GenerateAllocationProposalCommand(snapshot));

        Assert.True(result.IsSuccess);
        Assert.NotNull(result.Proposal);
        Assert.Equal(snapshot.AsOfDate.Value, policyProvider.RequestedAsOfDate?.Value);
        Assert.Equal(snapshot.AsOfDate.Value, portfolioProvider.RequestedAsOfDate?.Value);
        Assert.Equal(snapshot.AsOfDate.Value, tiltProvider.RequestedAsOfDate?.Value);
        Assert.Equal(DecisionSuggestion.PartialRebalance, result.Proposal.Suggestion);
        Assert.True(result.Proposal.LineFor(AssetClass.GlobalEquity).TargetWeight.Value > 0.60m);
    }

    [Fact]
    public async Task ExecuteAsync_ReturnsFailure_WhenPolicyIsMissing()
    {
        var useCase = new GenerateAllocationProposalUseCase(
            new FakePolicyProvider(null),
            new FakePortfolioProvider(AllocationProposalTestFixtures.CreatePortfolio()),
            new FakeTiltRuleProvider(AllocationProposalTestFixtures.CreateTiltRules()),
            new AllocationProposalService());

        var result = await useCase.ExecuteAsync(new GenerateAllocationProposalCommand(AllocationProposalTestFixtures.CreateSnapshot()));

        Assert.False(result.IsSuccess);
        Assert.Null(result.Proposal);
        Assert.Equal("Strategic allocation policy is missing.", result.Error);
    }

    [Fact]
    public async Task ExecuteAsync_ReturnsFailure_WhenCurrentPortfolioIsMissing()
    {
        var useCase = new GenerateAllocationProposalUseCase(
            new FakePolicyProvider(AllocationProposalTestFixtures.CreatePolicy()),
            new FakePortfolioProvider(null),
            new FakeTiltRuleProvider(AllocationProposalTestFixtures.CreateTiltRules()),
            new AllocationProposalService());

        var result = await useCase.ExecuteAsync(new GenerateAllocationProposalCommand(AllocationProposalTestFixtures.CreateSnapshot()));

        Assert.False(result.IsSuccess);
        Assert.Null(result.Proposal);
        Assert.Equal("Current portfolio is missing.", result.Error);
    }

    [Fact]
    public async Task ExecuteAsync_UsesEmptyTiltRules_WhenProviderReturnsNone()
    {
        var useCase = new GenerateAllocationProposalUseCase(
            new FakePolicyProvider(AllocationProposalTestFixtures.CreatePolicy()),
            new FakePortfolioProvider(AllocationProposalTestFixtures.CreatePortfolio()),
            new FakeTiltRuleProvider(Array.Empty<RegimeTiltRule>()),
            new AllocationProposalService());

        var result = await useCase.ExecuteAsync(new GenerateAllocationProposalCommand(AllocationProposalTestFixtures.CreateSnapshot()));

        Assert.True(result.IsSuccess);
        Assert.NotNull(result.Proposal);
        Assert.Equal(DecisionSuggestion.Hold, result.Proposal.Suggestion);
        Assert.Equal(0m, result.Proposal.Turnover.Value);
    }

    private sealed class FakePolicyProvider(StrategicAllocationPolicy? policy) : IStrategicAllocationPolicyProvider
    {
        public AsOfDate? RequestedAsOfDate { get; private set; }

        public Task<StrategicAllocationPolicy?> GetPolicyAsync(AsOfDate asOfDate, CancellationToken cancellationToken = default)
        {
            RequestedAsOfDate = asOfDate;
            return Task.FromResult(policy);
        }
    }

    private sealed class FakePortfolioProvider(CurrentPortfolio? portfolio) : ICurrentPortfolioProvider
    {
        public AsOfDate? RequestedAsOfDate { get; private set; }

        public Task<CurrentPortfolio?> GetCurrentPortfolioAsync(AsOfDate asOfDate, CancellationToken cancellationToken = default)
        {
            RequestedAsOfDate = asOfDate;
            return Task.FromResult(portfolio);
        }
    }

    private sealed class FakeTiltRuleProvider(IReadOnlyList<RegimeTiltRule> tiltRules) : IRegimeTiltRuleProvider
    {
        public AsOfDate? RequestedAsOfDate { get; private set; }

        public Task<IReadOnlyList<RegimeTiltRule>> GetTiltRulesAsync(AsOfDate asOfDate, CancellationToken cancellationToken = default)
        {
            RequestedAsOfDate = asOfDate;
            return Task.FromResult(tiltRules);
        }
    }
}
