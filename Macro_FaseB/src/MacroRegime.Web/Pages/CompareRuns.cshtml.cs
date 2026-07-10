using System.Globalization;
using MacroRegime.Application.Ports;
using MacroRegime.Web.Services;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;

namespace MacroRegime.Web.Pages;

public class CompareRunsModel : PageModel
{
    private readonly MacroRegimeWebAnalysisService analysisService;

    public CompareRunsModel(MacroRegimeWebAnalysisService analysisService)
    {
        this.analysisService = analysisService ?? throw new ArgumentNullException(nameof(analysisService));
    }

    [BindProperty(SupportsGet = true, Name = "baseline")]
    public string? BaselineInput { get; set; }

    [BindProperty(SupportsGet = true, Name = "comparison")]
    public string? ComparisonInput { get; set; }

    public WebRunComparisonResult? Result { get; private set; }

    public IReadOnlyList<RegimeRunManifestEntry> RunHistory { get; private set; } = Array.Empty<RegimeRunManifestEntry>();

    public string? ErrorMessage { get; private set; }

    public async Task OnGetAsync(CancellationToken cancellationToken)
    {
        try
        {
            RunHistory = await analysisService.ListRunsAsync(cancellationToken).ConfigureAwait(false);
        }
        catch (Exception exception) when (exception is IOException or InvalidDataException or UnauthorizedAccessException)
        {
            ErrorMessage = $"Run manifest could not be read: {exception.Message}";
            return;
        }

        if (string.IsNullOrWhiteSpace(BaselineInput) && string.IsNullOrWhiteSpace(ComparisonInput))
        {
            return;
        }

        if (!TryParseDate(BaselineInput, out var baseline))
        {
            ErrorMessage = "Baseline as-of date must use yyyy-MM-dd format.";
            return;
        }

        if (!TryParseDate(ComparisonInput, out var comparison))
        {
            ErrorMessage = "Comparison as-of date must use yyyy-MM-dd format.";
            return;
        }

        if (baseline == comparison)
        {
            ErrorMessage = "Baseline and comparison as-of dates must differ.";
            return;
        }

        try
        {
            Result = await analysisService.CompareRunsAsync(baseline, comparison, cancellationToken).ConfigureAwait(false);
            RunHistory = Result.RunHistory;
            if (!Result.IsSuccess)
            {
                ErrorMessage = Result.Error ?? "Stored runs could not be compared.";
            }
        }
        catch (Exception exception) when (exception is IOException or InvalidDataException or UnauthorizedAccessException)
        {
            ErrorMessage = $"Stored runs could not be read: {exception.Message}";
        }
    }

    public static string FormatOptionalPercent(decimal? value)
    {
        return value is null ? "-" : IndexModel.FormatPercent(value.Value);
    }

    public static string FormatOptionalRatio(decimal? value)
    {
        return value is null ? "-" : IndexModel.FormatRatio(value.Value);
    }

    public static string FormatSignedRatio(decimal value)
    {
        return value.ToString("+0.####;-0.####;0", CultureInfo.InvariantCulture);
    }

    private static bool TryParseDate(string? input, out DateOnly date)
    {
        return DateOnly.TryParseExact(input ?? string.Empty, "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out date);
    }
}
