using MacroRegime.Application.Regimes;
using MacroRegime.Domain.Allocations;
using MacroRegime.Domain.Regimes;

namespace MacroRegime.Application.Runs;

/// <summary>
/// Read model of a persisted regime run. It mirrors what is stored on disk so that
/// historical runs can be consulted without re-executing the pipeline and without
/// reconstructing domain aggregates from partial data.
/// </summary>
public sealed record RegimeRunDocument(
    DateOnly AsOfDate,
    string ModelName,
    string ModelVersion,
    string FeatureSetName,
    string FeatureSetVersion,
    string PrimaryRegime,
    string OperationalRegime,
    decimal Confidence,
    decimal CompositeScore,
    string Status,
    IReadOnlyList<RegimeRunProbability> Probabilities,
    IReadOnlyList<RegimeRunFeatureScore> FeatureScores,
    IReadOnlyList<RegimeRunExplanation> Explanations,
    IReadOnlyList<string> Warnings,
    RegimeRunDataSource? DataSource,
    RegimeRunAllocation? Allocation)
{
    public static RegimeRunDocument FromDomain(
        RegimeSnapshot snapshot,
        AllocationProposal? allocationProposal = null,
        DataSnapshotSourceInfo? dataSourceInfo = null)
    {
        ArgumentNullException.ThrowIfNull(snapshot);

        return new RegimeRunDocument(
            snapshot.AsOfDate.Value,
            snapshot.ModelVersion.Name,
            snapshot.ModelVersion.Version,
            snapshot.FeatureSetVersion.Name,
            snapshot.FeatureSetVersion.Version,
            snapshot.PrimaryRegime.ToString(),
            snapshot.OperationalRegime.ToString(),
            snapshot.Confidence.Value,
            snapshot.CompositeScore.Value,
            snapshot.Status,
            snapshot.Probabilities
                .Select(probability => new RegimeRunProbability(
                    probability.Regime.ToString(),
                    probability.Probability.Value,
                    probability.Rank))
                .ToArray(),
            snapshot.FeatureScores
                .Select(score => new RegimeRunFeatureScore(
                    score.FeatureCode,
                    score.Name,
                    score.Dimension.ToString(),
                    score.Weight.Value,
                    score.RawValue,
                    score.NormalizedScore.Value,
                    score.ZScore,
                    score.Momentum,
                    score.Interpretation))
                .ToArray(),
            snapshot.Explanations
                .Select(explanation => new RegimeRunExplanation(
                    explanation.Title,
                    explanation.Detail,
                    explanation.Impact,
                    explanation.FeatureCode,
                    explanation.Kind.ToString()))
                .ToArray(),
            snapshot.Warnings.ToArray(),
            dataSourceInfo is null
                ? null
                : new RegimeRunDataSource(
                    dataSourceInfo.Kind.ToString(),
                    dataSourceInfo.Description,
                    dataSourceInfo.Reference),
            allocationProposal is null
                ? null
                : new RegimeRunAllocation(
                    allocationProposal.Suggestion.ToString(),
                    allocationProposal.Turnover.Value,
                    allocationProposal.EstimatedCost,
                    allocationProposal.Lines
                        .Select(line => new RegimeRunAllocationLine(
                            line.AssetClass.ToString(),
                            line.CurrentWeight.Value,
                            line.StrategicWeight.Value,
                            line.TargetWeight.Value,
                            line.MinimumWeight.Value,
                            line.MaximumWeight.Value,
                            line.AppliedTilt,
                            line.Trade))
                        .ToArray(),
                    allocationProposal.Reasons.ToArray(),
                    allocationProposal.ConstraintMessages.ToArray()));
    }
}

public sealed record RegimeRunProbability(
    string Regime,
    decimal Probability,
    int Rank);

public sealed record RegimeRunFeatureScore(
    string FeatureCode,
    string Name,
    string Dimension,
    decimal Weight,
    decimal RawValue,
    decimal NormalizedScore,
    decimal? ZScore,
    decimal? Momentum,
    string Interpretation);

public sealed record RegimeRunExplanation(
    string Title,
    string Detail,
    decimal Impact,
    string? FeatureCode,
    string Kind);

public sealed record RegimeRunDataSource(
    string Kind,
    string Description,
    string? Reference);

public sealed record RegimeRunAllocation(
    string Suggestion,
    decimal Turnover,
    decimal EstimatedCost,
    IReadOnlyList<RegimeRunAllocationLine> Lines,
    IReadOnlyList<string> Reasons,
    IReadOnlyList<string> ConstraintMessages);

public sealed record RegimeRunAllocationLine(
    string AssetClass,
    decimal CurrentWeight,
    decimal StrategicWeight,
    decimal TargetWeight,
    decimal MinimumWeight,
    decimal MaximumWeight,
    decimal AppliedTilt,
    decimal Trade);
