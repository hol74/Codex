using MacroRegime.Domain.Time;

namespace MacroRegime.Application.External;

public sealed record FredFetchCommand(AsOfDate AsOfDate, FredSeriesSet SeriesSet);
