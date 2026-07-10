using MacroRegime.Application.Runs;

namespace MacroRegime.Infrastructure.Persistence;

public static class RegimeRunRecordMapper
{
    public const int CurrentSchemaVersion = 2;
    public const int MinimumSupportedSchemaVersion = 1;

    public static RegimeRunRecord FromDocument(RegimeRunDocument document)
    {
        ArgumentNullException.ThrowIfNull(document);

        return new RegimeRunRecord(
            CurrentSchemaVersion,
            document.AsOfDate,
            document.ModelName,
            document.ModelVersion,
            document.FeatureSetName,
            document.FeatureSetVersion,
            document.PrimaryRegime,
            document.OperationalRegime,
            document.Confidence,
            document.CompositeScore,
            document.Status,
            document.Probabilities
                .Select(probability => new RegimeProbabilityRecord(
                    probability.Regime,
                    probability.Probability,
                    probability.Rank))
                .ToArray(),
            document.FeatureScores
                .Select(score => new FeatureScoreRecord(
                    score.FeatureCode,
                    score.Name,
                    score.Dimension,
                    score.Weight,
                    score.RawValue,
                    score.NormalizedScore,
                    score.ZScore,
                    score.Momentum,
                    score.Interpretation))
                .ToArray(),
            document.Explanations
                .Select(explanation => new RegimeExplanationRecord(
                    explanation.Title,
                    explanation.Detail,
                    explanation.Impact,
                    explanation.FeatureCode,
                    explanation.Kind))
                .ToArray(),
            document.Warnings.ToArray(),
            document.DataSource is null
                ? null
                : new RegimeRunDataSourceRecord(
                    document.DataSource.Kind,
                    document.DataSource.Description,
                    document.DataSource.Reference),
            document.Allocation is null
                ? null
                : new RegimeRunAllocationRecord(
                    document.Allocation.Suggestion,
                    document.Allocation.Turnover,
                    document.Allocation.EstimatedCost,
                    document.Allocation.Lines
                        .Select(line => new RegimeRunAllocationLineRecord(
                            line.AssetClass,
                            line.CurrentWeight,
                            line.StrategicWeight,
                            line.TargetWeight,
                            line.MinimumWeight,
                            line.MaximumWeight,
                            line.AppliedTilt,
                            line.Trade))
                        .ToArray(),
                    document.Allocation.Reasons.ToArray(),
                    document.Allocation.ConstraintMessages.ToArray()));
    }

    public static RegimeRunDocument ToDocument(RegimeRunRecord record)
    {
        ArgumentNullException.ThrowIfNull(record);

        if (record.SchemaVersion < MinimumSupportedSchemaVersion || record.SchemaVersion > CurrentSchemaVersion)
        {
            throw new InvalidDataException(
                $"Regime run record has unsupported schema version {record.SchemaVersion}; supported versions are {MinimumSupportedSchemaVersion} to {CurrentSchemaVersion}.");
        }

        return new RegimeRunDocument(
            record.AsOfDate,
            record.ModelName,
            record.ModelVersion,
            record.FeatureSetName,
            record.FeatureSetVersion,
            record.PrimaryRegime,
            record.OperationalRegime,
            record.Confidence,
            record.CompositeScore,
            record.Status,
            record.Probabilities
                .Select(probability => new RegimeRunProbability(
                    probability.Regime,
                    probability.Probability,
                    probability.Rank))
                .ToArray(),
            record.FeatureScores
                .Select(score => new RegimeRunFeatureScore(
                    score.FeatureCode,
                    score.Name,
                    score.Dimension,
                    score.Weight,
                    score.RawValue,
                    score.NormalizedScore,
                    score.ZScore,
                    score.Momentum,
                    score.Interpretation))
                .ToArray(),
            record.Explanations
                .Select(explanation => new RegimeRunExplanation(
                    explanation.Title,
                    explanation.Detail,
                    explanation.Impact,
                    explanation.FeatureCode,
                    explanation.Kind))
                .ToArray(),
            record.Warnings.ToArray(),
            record.DataSource is null
                ? null
                : new RegimeRunDataSource(
                    record.DataSource.Kind,
                    record.DataSource.Description,
                    record.DataSource.Reference),
            record.Allocation is null
                ? null
                : new RegimeRunAllocation(
                    record.Allocation.Suggestion,
                    record.Allocation.Turnover,
                    record.Allocation.EstimatedCost,
                    record.Allocation.Lines
                        .Select(line => new RegimeRunAllocationLine(
                            line.AssetClass,
                            line.CurrentWeight,
                            line.StrategicWeight,
                            line.TargetWeight,
                            line.MinimumWeight,
                            line.MaximumWeight,
                            line.AppliedTilt,
                            line.Trade))
                        .ToArray(),
                    record.Allocation.Reasons.ToArray(),
                    record.Allocation.ConstraintMessages.ToArray()));
    }
}
