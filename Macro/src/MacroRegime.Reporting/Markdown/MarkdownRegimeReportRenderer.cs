using System.Globalization;
using System.Text;
using MacroRegime.Application.Ports;
using MacroRegime.Application.Reports;
using MacroRegime.Domain.Allocations;
using MacroRegime.Domain.Regimes;

namespace MacroRegime.Reporting.Markdown;

public sealed class MarkdownRegimeReportRenderer : IRegimeReportRenderer
{
    public string Render(RegimeReportContent content)
    {
        ArgumentNullException.ThrowIfNull(content);

        var snapshot = content.Snapshot;

        var builder = new StringBuilder();
        builder.AppendLine("# Macro-Regime Report");
        builder.AppendLine();
        builder.AppendLine($"As-of date: {snapshot.AsOfDate.Value:yyyy-MM-dd}");
        builder.AppendLine($"Model: {snapshot.ModelVersion.Name} v{snapshot.ModelVersion.Version}");
        builder.AppendLine($"Feature set: {snapshot.FeatureSetVersion.Name} v{snapshot.FeatureSetVersion.Version}");
        AppendInputSummary(builder, content);
        builder.AppendLine();
        builder.AppendLine("## Regime");
        builder.AppendLine();
        builder.AppendLine($"Primary regime: {snapshot.PrimaryRegime}");
        builder.AppendLine($"Operational regime: {snapshot.OperationalRegime}");
        builder.AppendLine($"Confidence: {Format(snapshot.Confidence.Value)}");
        builder.AppendLine($"Composite score: {Format(snapshot.CompositeScore.Value)}");
        builder.AppendLine($"Status: {snapshot.Status}");
        builder.AppendLine();
        builder.AppendLine("## Probabilities");
        builder.AppendLine();
        builder.AppendLine("| Rank | Regime | Probability |");
        builder.AppendLine("|---:|---|---:|");

        foreach (var probability in snapshot.Probabilities.OrderBy(probability => probability.Rank))
        {
            builder.AppendLine($"| {probability.Rank} | {probability.Regime} | {Format(probability.Probability.Value)} |");
        }

        builder.AppendLine();
        builder.AppendLine("## Feature Scores");
        builder.AppendLine();
        builder.AppendLine("| Feature | Dimension | Score | Weight |");
        builder.AppendLine("|---|---|---:|---:|");

        foreach (var score in snapshot.FeatureScores)
        {
            builder.AppendLine($"| {score.FeatureCode} | {score.Dimension} | {Format(score.NormalizedScore.Value)} | {Format(score.Weight.Value)} |");
        }

        builder.AppendLine();
        builder.AppendLine("## Explanations");
        builder.AppendLine();

        if (snapshot.Explanations.Count == 0)
        {
            builder.AppendLine("No explanations available.");
        }
        else
        {
            foreach (var explanation in snapshot.Explanations)
            {
                builder.AppendLine($"- {explanation.Kind}: {explanation.Title} ({Format(explanation.Impact)})");
            }
        }

        AppendAllocationProposal(builder, content.AllocationProposal);

        builder.AppendLine();
        builder.AppendLine("## Warnings");
        builder.AppendLine();

        if (snapshot.Warnings.Count == 0)
        {
            builder.AppendLine("No warnings.");
        }
        else
        {
            foreach (var warning in snapshot.Warnings)
            {
                builder.AppendLine($"- {warning}");
            }
        }

        return builder.ToString();
    }

    private static void AppendInputSummary(StringBuilder builder, RegimeReportContent content)
    {
        var snapshot = content.Snapshot;
        var activeFeatureCount = snapshot.FeatureSetVersion.FeatureDefinitions.Count(definition => definition.IsActive);

        builder.AppendLine();
        builder.AppendLine("## Input Summary");
        builder.AppendLine();
        builder.AppendLine($"Data source: {content.DataSourceInfo.Kind}");
        builder.AppendLine($"Data source detail: {content.DataSourceInfo.Description}");
        if (content.DataSourceInfo.Reference is not null)
        {
            builder.AppendLine($"Data source reference: {content.DataSourceInfo.Reference}");
        }

        builder.AppendLine($"Active feature definitions: {activeFeatureCount}");
        builder.AppendLine($"Feature scores produced: {snapshot.FeatureScores.Count}");
        builder.AppendLine($"Warnings: {snapshot.Warnings.Count}");
    }

    private static void AppendAllocationProposal(StringBuilder builder, AllocationProposal? proposal)
    {
        builder.AppendLine();
        builder.AppendLine("## Allocation Proposal");
        builder.AppendLine();

        if (proposal is null)
        {
            builder.AppendLine("No allocation proposal available.");
            return;
        }

        builder.AppendLine($"Decision suggestion: {proposal.Suggestion}");
        builder.AppendLine($"Turnover: {Format(proposal.Turnover.Value)}");
        builder.AppendLine($"Estimated cost: {Format(proposal.EstimatedCost)}");
        builder.AppendLine();
        builder.AppendLine("| Asset class | Current | Strategic | Target | Trade | Band | Tilt |");
        builder.AppendLine("|---|---:|---:|---:|---:|---:|---:|");

        foreach (var line in proposal.Lines)
        {
            builder.AppendLine(
                $"| {line.AssetClass} | {Format(line.CurrentWeight.Value)} | {Format(line.StrategicWeight.Value)} | {Format(line.TargetWeight.Value)} | {Format(line.Trade)} | {Format(line.MinimumWeight.Value)}-{Format(line.MaximumWeight.Value)} | {Format(line.AppliedTilt)} |");
        }

        builder.AppendLine();
        builder.AppendLine("### Allocation Rationale");
        builder.AppendLine();

        if (proposal.Reasons.Count == 0)
        {
            builder.AppendLine("No allocation rationale available.");
        }
        else
        {
            foreach (var reason in proposal.Reasons)
            {
                builder.AppendLine($"- {reason}");
            }
        }

        builder.AppendLine();
        builder.AppendLine("### Allocation Constraints");
        builder.AppendLine();

        if (proposal.ConstraintMessages.Count == 0)
        {
            builder.AppendLine("No allocation constraints triggered.");
        }
        else
        {
            foreach (var message in proposal.ConstraintMessages)
            {
                builder.AppendLine($"- {message}");
            }
        }
    }

    private static string Format(decimal value)
    {
        return value.ToString("0.####", CultureInfo.InvariantCulture);
    }
}
