using Finance.Application.MacroRegime;
using Finance.Domain.Enums;
using Finance.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;

namespace Finance.Infrastructure.Services;

public sealed class MacroRegimeService(FinanceDbContext dbContext) : IMacroRegimeService
{
    public async Task<MacroRegimeDashboard?> GetDashboardAsync(CancellationToken cancellationToken = default)
    {
        var run = await dbContext.RegimeRuns
            .AsNoTracking()
            .Include(x => x.RegimeModelVersion)
            .ThenInclude(x => x!.RegimeModel)
            .Include(x => x.Probabilities)
            .Include(x => x.Explanations)
            .OrderByDescending(x => x.AsOfDate)
            .FirstOrDefaultAsync(cancellationToken);

        if (run is null)
        {
            return null;
        }

        var report = await dbContext.RegimeReports
            .AsNoTracking()
            .Where(x => x.RegimeRunId == run.Id)
            .OrderByDescending(x => x.ReportDate)
            .Select(x => new RegimeReportReadModel(
                x.Title,
                x.ReportDate,
                x.Narrative,
                x.RecommendedAction,
                x.ReviewRequired))
            .FirstOrDefaultAsync(cancellationToken);

        var features = await dbContext.MacroFeatureValues
            .AsNoTracking()
            .Include(x => x.MacroFeatureDefinition)
            .Where(x => x.AsOfDate == run.AsOfDate)
            .OrderBy(x => x.MacroFeatureDefinition!.Dimension)
            .ThenByDescending(x => x.MacroFeatureDefinition!.Weight)
            .Select(x => new MacroFeatureReadModel(
                x.MacroFeatureDefinition!.Code,
                x.MacroFeatureDefinition.Name,
                x.MacroFeatureDefinition.Dimension,
                x.MacroFeatureDefinition.Weight,
                x.RawValue,
                x.NormalizedValue,
                x.ZScore,
                x.Momentum4Weeks,
                x.Interpretation))
            .ToListAsync(cancellationToken);

        var observations = await dbContext.MacroObservations
            .AsNoTracking()
            .Include(x => x.MacroSeries)
            .ThenInclude(x => x!.MacroDataSource)
            .OrderByDescending(x => x.ObservationDate)
            .Take(40)
            .ToListAsync(cancellationToken);

        var latestSeries = observations
            .GroupBy(x => x.MacroSeriesId)
            .Select(x => x.OrderByDescending(y => y.ObservationDate).First())
            .OrderBy(x => x.MacroSeries!.Category)
            .ThenBy(x => x.MacroSeries!.Code)
            .Select(x => new MacroSeriesReadModel(
                x.MacroSeries!.Code,
                x.MacroSeries.Name,
                x.MacroSeries.Category,
                x.MacroSeries.MacroDataSource?.Name ?? "-",
                x.ObservationDate,
                x.PublishedDate,
                x.Value,
                x.MacroSeries.Unit,
                x.Vintage))
            .ToList();

        var marketObservations = await dbContext.MarketObservations
            .AsNoTracking()
            .Include(x => x.MarketSeries)
            .ThenInclude(x => x!.MacroDataSource)
            .OrderByDescending(x => x.Date)
            .Take(40)
            .ToListAsync(cancellationToken);

        var latestMarketSeries = marketObservations
            .GroupBy(x => x.MarketSeriesId)
            .Select(x => x.OrderByDescending(y => y.Date).First())
            .OrderBy(x => x.MarketSeries!.Category)
            .ThenBy(x => x.MarketSeries!.Symbol)
            .Select(x => new MarketSeriesReadModel(
                x.MarketSeries!.Symbol,
                x.MarketSeries.Name,
                x.MarketSeries.Category,
                x.MarketSeries.MacroDataSource?.Name ?? "-",
                x.Date,
                x.AvailableDate,
                x.Value,
                x.MarketSeries.Unit,
                x.MarketSeries.ProxyRole))
            .ToList();

        var releases = await dbContext.ReleaseCalendar
            .AsNoTracking()
            .Include(x => x.MacroDataSource)
            .OrderByDescending(x => x.ReleaseDate)
            .Take(12)
            .Select(x => new ReleaseCalendarReadModel(
                x.ReleaseCode,
                x.Name,
                x.MacroDataSource!.Name,
                x.ReleaseDate,
                x.ObservationPeriodStart,
                x.ObservationPeriodEnd,
                x.Frequency,
                x.Status))
            .ToListAsync(cancellationToken);

        return new MacroRegimeDashboard(
            run.AsOfDate,
            run.RegimeModelVersion?.RegimeModel?.Name ?? "-",
            run.RegimeModelVersion?.Version ?? "-",
            DisplayRegime(run.PrimaryRegime),
            run.Status,
            run.Confidence,
            run.CompositeScore,
            run.Summary,
            report,
            run.Probabilities.OrderBy(x => x.Rank).Select(x => new RegimeProbabilityReadModel(DisplayRegime(x.Regime), x.Probability, x.Rank)).ToList(),
            features,
            run.Explanations.OrderByDescending(x => x.Impact).Select(x => new RegimeExplanationReadModel(x.Title, x.Detail, x.Impact, x.FeatureCode)).ToList(),
            latestSeries,
            latestMarketSeries,
            releases);
    }

    private static string DisplayRegime(RegimeType regime)
    {
        return regime switch
        {
            RegimeType.ExpansionRiskOn => "Expansion / Risk-on",
            RegimeType.InflationaryExpansion => "Espansione inflazionistica",
            RegimeType.Slowdown => "Rallentamento",
            RegimeType.RecessionStress => "Recessione / Stress",
            RegimeType.Recovery => "Ripresa",
            RegimeType.UncertainTransition => "Incerto / Transizione",
            RegimeType.Goldilocks => "Goldilocks",
            RegimeType.Reflation => "Reflazione",
            RegimeType.LateCycleOverheating => "Late cycle / Surriscaldamento",
            RegimeType.Stagflation => "Stagflazione",
            RegimeType.DeflationBust => "Deflazione / Bust",
            RegimeType.ZirpQeFinancialRepression => "ZIRP/QE / Repressione finanziaria",
            _ => regime.ToString()
        };
    }
}
