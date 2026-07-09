using System.Globalization;
using MacroRegime.Web.Services;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;
using Microsoft.Extensions.Options;

namespace MacroRegime.Web.Pages;

public class ImportDiagnosticsModel : PageModel
{
    private readonly MacroRegimeWebAnalysisService analysisService;
    private readonly MacroRegimeWebOptions options;

    public ImportDiagnosticsModel(MacroRegimeWebAnalysisService analysisService, IOptions<MacroRegimeWebOptions> options)
    {
        this.analysisService = analysisService ?? throw new ArgumentNullException(nameof(analysisService));
        this.options = options?.Value ?? throw new ArgumentNullException(nameof(options));
        AsOfDateInput = this.options.DefaultAsOfDate.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);
    }

    [BindProperty(SupportsGet = true, Name = "asOfDate")]
    public string AsOfDateInput { get; set; }

    public WebImportDiagnosticsResult? Diagnostics { get; private set; }

    public string? ErrorMessage { get; private set; }

    public async Task OnGetAsync(CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(AsOfDateInput))
        {
            AsOfDateInput = options.DefaultAsOfDate.ToString("yyyy-MM-dd", CultureInfo.InvariantCulture);
        }

        if (!DateOnly.TryParseExact(AsOfDateInput, "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out var asOfDate))
        {
            ErrorMessage = "As-of date must use yyyy-MM-dd format.";
            return;
        }

        Diagnostics = await analysisService.ValidateImportsAsync(asOfDate, cancellationToken).ConfigureAwait(false);
    }
}
