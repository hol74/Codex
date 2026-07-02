using System.Globalization;
using System.Text;
using MacroRegime.Domain.Regimes;

namespace MacroRegime.Reporting.Markdown;

public sealed class MarkdownRegimeReportRenderer
{
    public string Render(RegimeSnapshot snapshot)
    {
        ArgumentNullException.ThrowIfNull(snapshot);

        var builder = new StringBuilder();
        builder.AppendLine("# Macro-Regime Report");
        builder.AppendLine();
        builder.AppendLine($"As-of date: {snapshot.AsOfDate.Value:yyyy-MM-dd}");
        builder.AppendLine($"Model: {snapshot.ModelVersion.Name} v{snapshot.ModelVersion.Version}");
        builder.AppendLine($"Feature set: {snapshot.FeatureSetVersion.Name} v{snapshot.FeatureSetVersion.Version}");
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

    private static string Format(decimal value)
    {
        return value.ToString("0.####", CultureInfo.InvariantCulture);
    }
}
