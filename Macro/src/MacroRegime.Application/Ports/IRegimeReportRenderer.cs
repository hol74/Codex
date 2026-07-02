using MacroRegime.Application.Reports;

namespace MacroRegime.Application.Ports;

public interface IRegimeReportRenderer
{
    string Render(RegimeReportContent content);
}
