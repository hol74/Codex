using MacroRegime.Domain.Time;

namespace MacroRegime.Application.External;

public sealed record DownloadMacroDataCommand(AsOfDate AsOfDate, FredSeriesSet SeriesSet, string OutputDirectory);

public sealed record DownloadMacroDataResult(string OutputPath, int SeriesCount, int ObservationCount);
