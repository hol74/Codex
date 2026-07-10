using MacroRegime.Domain.Time;

namespace MacroRegime.Application.External;

public sealed record DownloadMarketDataCommand(AsOfDate AsOfDate, MarketDataSeriesSet SeriesSet, string OutputDirectory);

public sealed record DownloadMarketDataResult(string OutputPath, int SeriesCount, int ObservationCount);
