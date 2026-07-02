using Finance.Domain.Common;
using Finance.Domain.Enums;

namespace Finance.Domain.Entities;

public sealed class DataSource : Entity
{
    public required string Name { get; set; }
    public required string Kind { get; set; }
    public string? Url { get; set; }
    public string? Notes { get; set; }
}

public sealed class ImportBatch : Entity
{
    public required string SourceName { get; set; }
    public DateTimeOffset ImportedAt { get; set; } = DateTimeOffset.UtcNow;
    public int RecordsRead { get; set; }
    public int RecordsAccepted { get; set; }
    public int RecordsRejected { get; set; }
    public string? FileName { get; set; }
}

public sealed class MacroDataSource : Entity
{
    public required string Name { get; set; }
    public required string Kind { get; set; }
    public string? Url { get; set; }
    public string? ApiBaseUrl { get; set; }
    public bool SupportsVintageData { get; set; }
    public string? Notes { get; set; }
    public ICollection<MacroSeries> Series { get; set; } = [];
    public ICollection<MarketSeries> MarketSeries { get; set; } = [];
    public ICollection<ReleaseCalendar> ReleaseCalendar { get; set; } = [];
}

public sealed class MacroSeries : Entity
{
    public Guid MacroDataSourceId { get; set; }
    public MacroDataSource? MacroDataSource { get; set; }
    public required string Code { get; set; }
    public required string Name { get; set; }
    public required string Category { get; set; }
    public required string Frequency { get; set; }
    public string? Unit { get; set; }
    public bool IsHigherRiskOn { get; set; } = true;
    public int PublicationLagDays { get; set; }
    public string? FredSeriesId { get; set; }
    public string? FredMdColumn { get; set; }
    public bool RequiresVintageTracking { get; set; } = true;
    public ICollection<MacroObservation> Observations { get; set; } = [];
    public ICollection<DataVintage> Vintages { get; set; } = [];
}

public sealed class DataVintage : Entity
{
    public Guid MacroSeriesId { get; set; }
    public MacroSeries? MacroSeries { get; set; }
    public Guid? ImportBatchId { get; set; }
    public ImportBatch? ImportBatch { get; set; }
    public DateOnly VintageDate { get; set; }
    public DateOnly RealtimeStart { get; set; }
    public DateOnly RealtimeEnd { get; set; }
    public DateTimeOffset RetrievedAt { get; set; } = DateTimeOffset.UtcNow;
    public required string SourceSystem { get; set; }
    public string? SourceUrl { get; set; }
    public string? SourceHash { get; set; }
    public bool IsOfficialVintage { get; set; }
    public ICollection<MacroObservation> Observations { get; set; } = [];
}

public sealed class MacroObservation : Entity
{
    public Guid MacroSeriesId { get; set; }
    public MacroSeries? MacroSeries { get; set; }
    public Guid? DataVintageId { get; set; }
    public DataVintage? DataVintage { get; set; }
    public DateOnly ObservationDate { get; set; }
    public DateOnly PublishedDate { get; set; }
    public decimal Value { get; set; }
    public string? Vintage { get; set; }
    public bool IsRevised { get; set; }
}

public sealed class ReleaseCalendar : Entity
{
    public Guid MacroDataSourceId { get; set; }
    public MacroDataSource? MacroDataSource { get; set; }
    public required string ReleaseCode { get; set; }
    public required string Name { get; set; }
    public DateOnly ReleaseDate { get; set; }
    public DateOnly? ObservationPeriodStart { get; set; }
    public DateOnly? ObservationPeriodEnd { get; set; }
    public required string Frequency { get; set; }
    public string? SourceUrl { get; set; }
    public string Status { get; set; } = "Scheduled";
}

public sealed class MarketSeries : Entity
{
    public Guid MacroDataSourceId { get; set; }
    public MacroDataSource? MacroDataSource { get; set; }
    public required string Symbol { get; set; }
    public required string Name { get; set; }
    public required string Category { get; set; }
    public required string Frequency { get; set; }
    public string? Unit { get; set; }
    public string? CurrencyCode { get; set; }
    public string? AssetClassCode { get; set; }
    public string? ProxyRole { get; set; }
    public bool IsProxy { get; set; } = true;
    public bool IsHigherRiskOn { get; set; } = true;
    public Guid? InstrumentId { get; set; }
    public Instrument? Instrument { get; set; }
    public ICollection<MarketObservation> Observations { get; set; } = [];
}

public sealed class MarketObservation : Entity
{
    public Guid MarketSeriesId { get; set; }
    public MarketSeries? MarketSeries { get; set; }
    public DateOnly Date { get; set; }
    public decimal Value { get; set; }
    public DateOnly AvailableDate { get; set; }
    public string? SourceHash { get; set; }
    public string? Notes { get; set; }
}

public sealed class MacroFeatureSetVersion : Entity
{
    public required string Name { get; set; }
    public required string Version { get; set; }
    public string? Description { get; set; }
    public bool IsActive { get; set; } = true;
    public ICollection<MacroFeatureDefinition> FeatureDefinitions { get; set; } = [];
}

public sealed class MacroFeatureDefinition : Entity
{
    public Guid MacroFeatureSetVersionId { get; set; }
    public MacroFeatureSetVersion? MacroFeatureSetVersion { get; set; }
    public required string Code { get; set; }
    public required string Name { get; set; }
    public required string Dimension { get; set; }
    public required string Formula { get; set; }
    public decimal Weight { get; set; }
    public int LookbackMonths { get; set; }
    public bool IsHigherRiskOn { get; set; } = true;
    public bool IsActive { get; set; } = true;
    public ICollection<MacroFeatureValue> Values { get; set; } = [];
}

public sealed class MacroFeatureValue : Entity
{
    public Guid MacroFeatureDefinitionId { get; set; }
    public MacroFeatureDefinition? MacroFeatureDefinition { get; set; }
    public Guid? MacroObservationId { get; set; }
    public MacroObservation? MacroObservation { get; set; }
    public Guid? MarketObservationId { get; set; }
    public MarketObservation? MarketObservation { get; set; }
    public DateOnly DataAsOfDate { get; set; }
    public DateOnly AsOfDate { get; set; }
    public decimal RawValue { get; set; }
    public decimal NormalizedValue { get; set; }
    public decimal ZScore { get; set; }
    public decimal Momentum4Weeks { get; set; }
    public required string Interpretation { get; set; }
}

public sealed class RegimeModel : Entity
{
    public required string Name { get; set; }
    public required string Kind { get; set; }
    public bool IsProduction { get; set; }
    public string? Notes { get; set; }
    public ICollection<RegimeModelVersion> Versions { get; set; } = [];
}

public sealed class RegimeModelVersion : Entity
{
    public Guid RegimeModelId { get; set; }
    public RegimeModel? RegimeModel { get; set; }
    public required string Version { get; set; }
    public string? Description { get; set; }
    public string? ParametersJson { get; set; }
    public DateOnly EffectiveFrom { get; set; }
    public ICollection<RegimeRun> Runs { get; set; } = [];
}

public sealed class RegimeRun : Entity
{
    public Guid RegimeModelVersionId { get; set; }
    public RegimeModelVersion? RegimeModelVersion { get; set; }
    public DateOnly RunDate { get; set; }
    public DateOnly AsOfDate { get; set; }
    public RegimeType PrimaryRegime { get; set; }
    public decimal Confidence { get; set; }
    public decimal CompositeScore { get; set; }
    public required string Status { get; set; }
    public required string Summary { get; set; }
    public ICollection<RegimeProbability> Probabilities { get; set; } = [];
    public ICollection<RegimeExplanation> Explanations { get; set; } = [];
}

public sealed class RegimeProbability : Entity
{
    public Guid RegimeRunId { get; set; }
    public RegimeRun? RegimeRun { get; set; }
    public RegimeType Regime { get; set; }
    public decimal Probability { get; set; }
    public int Rank { get; set; }
}

public sealed class RegimeExplanation : Entity
{
    public Guid RegimeRunId { get; set; }
    public RegimeRun? RegimeRun { get; set; }
    public required string Title { get; set; }
    public required string Detail { get; set; }
    public decimal Impact { get; set; }
    public string? FeatureCode { get; set; }
}

public sealed class RegimeReport : Entity
{
    public Guid RegimeRunId { get; set; }
    public RegimeRun? RegimeRun { get; set; }
    public DateOnly ReportDate { get; set; }
    public required string Title { get; set; }
    public required string Narrative { get; set; }
    public required string RecommendedAction { get; set; }
    public bool ReviewRequired { get; set; }
}

public sealed class AuditEvent : Entity
{
    public required string Area { get; set; }
    public required string EventType { get; set; }
    public required string Message { get; set; }
    public string? Actor { get; set; }
}

public sealed class PortfolioPolicy : Entity
{
    public Guid PortfolioId { get; set; }
    public Portfolio? Portfolio { get; set; }
    public required string Name { get; set; }
    public decimal MaxTurnoverPerRebalance { get; set; }
    public decimal CashBufferWeight { get; set; }
    public decimal MinimumTradeAmountBase { get; set; }
    public bool TaxAwareRebalancing { get; set; }
    public bool IsActive { get; set; } = true;
}

public sealed class RegimeObservation : Entity
{
    public DateOnly ObservationDate { get; set; }
    public RegimeType Regime { get; set; }
    public decimal Probability { get; set; }
    public required string Summary { get; set; }
    public string? Explanation { get; set; }
    public ICollection<RegimeSignal> Signals { get; set; } = [];
}

public sealed class RegimeSignal : Entity
{
    public Guid RegimeObservationId { get; set; }
    public RegimeObservation? RegimeObservation { get; set; }
    public required string Name { get; set; }
    public required string Dimension { get; set; }
    public decimal Value { get; set; }
    public decimal ZScore { get; set; }
    public required string Interpretation { get; set; }
}

public sealed class AllocationProposal : Entity
{
    public Guid PortfolioId { get; set; }
    public Portfolio? Portfolio { get; set; }
    public Guid? RegimeObservationId { get; set; }
    public RegimeObservation? RegimeObservation { get; set; }
    public DateOnly ProposalDate { get; set; }
    public required string Decision { get; set; }
    public string? Rationale { get; set; }
    public decimal EstimatedCostBase { get; set; }
    public decimal EstimatedTaxImpactBase { get; set; }
    public ICollection<RebalanceRecommendation> Recommendations { get; set; } = [];
}

public sealed class RebalanceRecommendation : Entity
{
    public Guid AllocationProposalId { get; set; }
    public AllocationProposal? AllocationProposal { get; set; }
    public Guid AssetClassId { get; set; }
    public AssetClass? AssetClass { get; set; }
    public RebalanceAction Action { get; set; }
    public decimal CurrentWeight { get; set; }
    public decimal TargetWeight { get; set; }
    public decimal TradeAmountBase { get; set; }
    public string? Notes { get; set; }
}
