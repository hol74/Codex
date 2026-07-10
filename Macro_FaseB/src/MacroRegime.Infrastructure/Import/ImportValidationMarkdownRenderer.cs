using System.Globalization;
using System.Text;
using MacroRegime.Application.Import;

namespace MacroRegime.Infrastructure.Import;

public static class ImportValidationMarkdownRenderer
{
    public static string Render(ImportValidationReport report)
    {
        ArgumentNullException.ThrowIfNull(report);

        var builder = new StringBuilder();
        builder.AppendLine("# Import Validation Report");
        builder.AppendLine();
        builder.AppendLine(CultureInfo.InvariantCulture, $"As-of date: {report.AsOfDate:yyyy-MM-dd}");
        builder.AppendLine(CultureInfo.InvariantCulture, $"OK: {report.OkCount}");
        builder.AppendLine(CultureInfo.InvariantCulture, $"Warnings: {report.WarningCount}");
        builder.AppendLine(CultureInfo.InvariantCulture, $"Errors: {report.ErrorCount}");
        builder.AppendLine();
        builder.AppendLine("| Input | Severity | Message | Path |");
        builder.AppendLine("|---|---|---|---|");

        foreach (var item in report.Items)
        {
            builder.AppendLine(CultureInfo.InvariantCulture, $"| {Escape(item.InputKind)} | {item.Severity} | {Escape(item.Message)} | {Escape(item.Path ?? "-")} |");
        }

        return builder.ToString();
    }

    private static string Escape(string value)
    {
        return value.Replace("|", "\\|", StringComparison.Ordinal);
    }
}
