using System.Globalization;
using MacroRegime.Web.Services;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using Microsoft.Extensions.Options;

namespace MacroRegime.Web.Pages;

public class IndexModel : PageModel
{
    private readonly MacroRegimeWebAnalysisService analysisService;
    private readonly MacroRegimeWebOptions options;

    public IndexModel(MacroRegimeWebAnalysisService analysisService, IOptions<MacroRegimeWebOptions> options)
    {
        this.analysisService = analysisService ?? throw new ArgumentNullException(nameof(analysisService));
        this.options = options?.Value ?? throw new ArgumentNullException(nameof(options));
        AsOfDateInput = this.options.DefaultAsOfDate.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);
    }

    [BindProperty(SupportsGet = true, Name = "asOfDate")]
    public string AsOfDateInput { get; set; }

    public WebAnalysisResult? WebResult { get; private set; }

    public string? ErrorMessage { get; private set; }

    public async Task OnGetAsync(CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(AsOfDateInput))
        {
            AsOfDateInput = options.DefaultAsOfDate.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);
        }

        await RunAsync(cancellationToken).ConfigureAwait(false);
    }

    public async Task OnPostAsync(CancellationToken cancellationToken)
    {
        await RunAsync(cancellationToken).ConfigureAwait(false);
    }

    public static string FormatRatio(decimal value)
    {
        return value.ToString("0.####", CultureInfo.InvariantCulture);
    }

    public static string FormatPercent(decimal value)
    {
        return value.ToString("0.##%", CultureInfo.InvariantCulture);
    }

    public static string FormatSignedPercent(decimal value)
    {
        return value.ToString("+0.##%;-0.##%;0%", CultureInfo.InvariantCulture);
    }

    public static string ProbabilityWidth(decimal probability)
    {
        return Math.Clamp(probability * 100m, 0m, 100m).ToString("0.##", CultureInfo.InvariantCulture);
    }

    private async Task RunAsync(CancellationToken cancellationToken)
    {
        if (!DateOnly.TryParseExact(AsOfDateInput, "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out var asOfDate))
        {
            ErrorMessage = "As-of date must use yyyy-MM-dd format.";
            return;
        }

        try
        {
            WebResult = await analysisService.RunAsync(asOfDate, cancellationToken).ConfigureAwait(false);
            if (!WebResult.Analysis.IsSuccess)
            {
                ErrorMessage = WebResult.Analysis.Error ?? "Macro-regime analysis failed.";
            }
        }
        catch (Exception exception) when (exception is IOException or InvalidDataException or UnauthorizedAccessException or ArgumentException)
        {
            ErrorMessage = exception.Message;
        }
    }
}
