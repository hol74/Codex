using System.Globalization;
using MacroRegime.Web.Services;
using Microsoft.AspNetCore.Mvc;
using Microsoft.AspNetCore.Mvc.RazorPages;

namespace MacroRegime.Web.Pages;

public class RunDetailModel : PageModel
{
    private readonly MacroRegimeWebAnalysisService analysisService;

    public RunDetailModel(MacroRegimeWebAnalysisService analysisService)
    {
        this.analysisService = analysisService ?? throw new ArgumentNullException(nameof(analysisService));
    }

    [BindProperty(SupportsGet = true, Name = "asOfDate")]
    public string? AsOfDateInput { get; set; }

    public WebRunDetailResult? Detail { get; private set; }

    public string? ErrorMessage { get; private set; }

    public async Task OnGetAsync(CancellationToken cancellationToken)
    {
        if (string.IsNullOrWhiteSpace(AsOfDateInput))
        {
            ErrorMessage = "As-of date is required to open a stored run.";
            return;
        }

        if (!DateOnly.TryParseExact(AsOfDateInput, "yyyy-MM-dd", CultureInfo.InvariantCulture, DateTimeStyles.None, out var asOfDate))
        {
            ErrorMessage = "As-of date must use yyyy-MM-dd format.";
            return;
        }

        try
        {
            Detail = await analysisService.LoadRunAsync(asOfDate, cancellationToken).ConfigureAwait(false);
            if (!Detail.IsSuccess)
            {
                ErrorMessage = Detail.Error ?? "Stored run could not be loaded.";
            }
        }
        catch (Exception exception) when (exception is IOException or InvalidDataException or UnauthorizedAccessException)
        {
            ErrorMessage = $"Stored run could not be read: {exception.Message}";
        }
    }
}
