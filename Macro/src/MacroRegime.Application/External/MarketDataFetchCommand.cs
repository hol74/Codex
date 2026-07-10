using MacroRegime.Domain.Time;

namespace MacroRegime.Application.External;

public sealed record MarketDataFetchCommand(AsOfDate AsOfDate, MarketDataSeriesSet SeriesSet);
