using Finance.Application.MacroRegime;
using Finance.Domain.Entities;
using Finance.Domain.Enums;
using Finance.Infrastructure.Data;
using Microsoft.EntityFrameworkCore;

namespace Finance.Infrastructure.Services;

public sealed class RegimeCalculationService(FinanceDbContext dbContext, IMacroDataFoundationService macroDataFoundationService) : IRegimeCalculationService
{
    private static readonly string[] RequiredDimensions = ["Growth", "Inflation", "Risk", "Monetary", "Credit"];

    public async Task<RegimeCalculationPreview> PreviewAsync(DateOnly asOfDate, Guid? modelVersionId = null, CancellationToken cancellationToken = default)
    {
        var version = await EnsureModelVersionAsync(modelVersionId, cancellationToken);
        var snapshot = await macroDataFoundationService.GetAsOfSnapshotAsync(asOfDate, cancellationToken);
        var dimensions = snapshot.MacroObservations.Select(x => x.Category)
            .Concat(snapshot.MarketObservations.Select(x => x.Category))
            .Where(x => !string.IsNullOrWhiteSpace(x))
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .OrderBy(x => x)
            .ToList();
        var missing = RequiredDimensions
            .Where(x => !dimensions.Contains(x, StringComparer.OrdinalIgnoreCase))
            .ToList();
        var warnings = BuildWarnings(snapshot.MacroObservations.Count, snapshot.MarketObservations.Count, missing);

        return new RegimeCalculationPreview(
            asOfDate,
            version.RegimeModel?.Name ?? "CRS Rule-Based Engine",
            version.Version,
            snapshot.MacroObservations.Count,
            snapshot.MarketObservations.Count,
            dimensions,
            missing,
            warnings);
    }

    public async Task<RegimeCalculationResult> CalculateAsync(DateOnly asOfDate, Guid? modelVersionId = null, CancellationToken cancellationToken = default)
    {
        var version = await EnsureModelVersionAsync(modelVersionId, cancellationToken);
        var featureDefinitions = await EnsureFeatureDefinitionsAsync(cancellationToken);
        var snapshot = await macroDataFoundationService.GetAsOfSnapshotAsync(asOfDate, cancellationToken);

        var dimensions = snapshot.MacroObservations.Select(x => x.Category)
            .Concat(snapshot.MarketObservations.Select(x => x.Category))
            .Distinct(StringComparer.OrdinalIgnoreCase)
            .ToList();
        var missing = RequiredDimensions.Where(x => !dimensions.Contains(x, StringComparer.OrdinalIgnoreCase)).ToList();
        var warnings = BuildWarnings(snapshot.MacroObservations.Count, snapshot.MarketObservations.Count, missing);
        var features = featureDefinitions
            .Select(x => CalculateFeature(x, snapshot))
            .OrderByDescending(x => x.Weight)
            .ToList();

        var totalWeight = features.Sum(x => x.Weight);
        var compositeScore = totalWeight == 0 ? 0.5m : Clamp(features.Sum(x => x.NormalizedValue * x.Weight) / totalWeight);
        var probabilities = CalculateProbabilities(features, compositeScore);
        var topProbability = probabilities.OrderByDescending(x => x.Probability).First();
        var primaryRegime = topProbability.Probability < 0.60m ? RegimeType.UncertainTransition : Enum.Parse<RegimeType>(topProbability.Regime);
        var confidence = topProbability.Probability;
        var status = primaryRegime == RegimeType.UncertainTransition || warnings.Count > 0 ? "Transition" : "Confirmed";
        var summary = BuildSummary(primaryRegime, compositeScore, confidence, warnings.Count);

        await UpsertFeatureValuesAsync(featureDefinitions, features, asOfDate, cancellationToken);
        var run = await UpsertRunAsync(version, asOfDate, primaryRegime, confidence, compositeScore, status, summary, features, probabilities, cancellationToken);

        dbContext.AuditEvents.Add(new AuditEvent
        {
            Area = "MacroRegime",
            EventType = "RegimeCalculated",
            Message = $"Calcolo regime {version.RegimeModel?.Name} {version.Version} eseguito as-of {asOfDate:yyyy-MM-dd}: {primaryRegime} ({confidence:P0}).",
            Actor = "manual"
        });

        await dbContext.SaveChangesAsync(cancellationToken);

        return new RegimeCalculationResult(
            run.AsOfDate,
            version.RegimeModel?.Name ?? "CRS Rule-Based Engine",
            version.Version,
            run.PrimaryRegime.ToString(),
            run.Confidence,
            run.CompositeScore,
            run.Status,
            features,
            probabilities,
            warnings);
    }

    private async Task<RegimeModelVersion> EnsureModelVersionAsync(Guid? modelVersionId, CancellationToken cancellationToken)
    {
        if (modelVersionId is not null)
        {
            var requested = await dbContext.RegimeModelVersions
                .Include(x => x.RegimeModel)
                .FirstOrDefaultAsync(x => x.Id == modelVersionId, cancellationToken);

            if (requested is not null)
            {
                return requested;
            }
        }

        var existing = await dbContext.RegimeModelVersions
            .Include(x => x.RegimeModel)
            .Where(x => x.RegimeModel != null && x.RegimeModel.Name == "CRS Rule-Based Engine")
            .OrderByDescending(x => x.EffectiveFrom)
            .FirstOrDefaultAsync(cancellationToken);

        if (existing is not null)
        {
            return existing;
        }

        var model = await dbContext.RegimeModels.FirstOrDefaultAsync(x => x.Name == "CRS Rule-Based Engine", cancellationToken)
            ?? dbContext.RegimeModels.Add(new RegimeModel
            {
                Name = "CRS Rule-Based Engine",
                Kind = "RuleBased",
                IsProduction = true,
                Notes = "Baseline interpretabile per il Macro-Regime Engine."
            }).Entity;

        return dbContext.RegimeModelVersions.Add(new RegimeModelVersion
        {
            RegimeModel = model,
            Version = "v0.1",
            Description = "Calcolo rule-based manuale su snapshot as-of.",
            EffectiveFrom = DateOnly.FromDateTime(DateTime.Today),
            ParametersJson = """{"uncertainBelowConfidence":0.60,"manualExecution":true}"""
        }).Entity;
    }

    private async Task<IReadOnlyCollection<MacroFeatureDefinition>> EnsureFeatureDefinitionsAsync(CancellationToken cancellationToken)
    {
        var featureSet = await dbContext.MacroFeatureSetVersions
            .Include(x => x.FeatureDefinitions)
            .FirstOrDefaultAsync(x => x.Name == "CRS Baseline" && x.Version == "v0.1", cancellationToken)
            ?? dbContext.MacroFeatureSetVersions.Add(new MacroFeatureSetVersion
            {
                Name = "CRS Baseline",
                Version = "v0.1",
                Description = "Feature set baseline per Growth, Inflation, Risk, Monetary e Credit.",
                IsActive = true
            }).Entity;

        var definitions = new[]
        {
            new FeatureDefinitionSeed("GROWTH_MOM", "Growth momentum", "Growth", "PMI, Sahm e indicatori growth vintage-aware", 0.30m, true),
            new FeatureDefinitionSeed("INFL_PRESS", "Inflation pressure", "Inflation", "Breakeven e proxy commodity", 0.25m, false),
            new FeatureDefinitionSeed("RISK_APPETITE", "Risk appetite", "Risk", "Volatilita' e proxy risk-on/risk-off", 0.25m, true),
            new FeatureDefinitionSeed("MONETARY_COND", "Monetary conditions", "Monetary", "Yield curve e stance monetaria", 0.15m, true),
            new FeatureDefinitionSeed("CREDIT_STRESS", "Credit stress", "Credit", "Spread credito e proxy HY/IG", 0.05m, false)
        };

        foreach (var seed in definitions)
        {
            if (featureSet.FeatureDefinitions.Any(x => x.Code == seed.Code))
            {
                continue;
            }

            featureSet.FeatureDefinitions.Add(new MacroFeatureDefinition
            {
                Code = seed.Code,
                Name = seed.Name,
                Dimension = seed.Dimension,
                Formula = seed.Formula,
                Weight = seed.Weight,
                LookbackMonths = 60,
                IsHigherRiskOn = seed.IsHigherRiskOn,
                IsActive = true
            });
        }

        await dbContext.SaveChangesAsync(cancellationToken);

        return await dbContext.MacroFeatureDefinitions
            .AsNoTracking()
            .Where(x => x.MacroFeatureSetVersionId == featureSet.Id && x.IsActive)
            .OrderBy(x => x.Code)
            .ToListAsync(cancellationToken);
    }

    private static CalculatedFeatureResult CalculateFeature(MacroFeatureDefinition definition, AsOfDataSnapshot snapshot)
    {
        var values = definition.Code switch
        {
            "GROWTH_MOM" => GrowthScores(snapshot),
            "INFL_PRESS" => InflationScores(snapshot),
            "RISK_APPETITE" => RiskScores(snapshot),
            "MONETARY_COND" => MonetaryScores(snapshot),
            "CREDIT_STRESS" => CreditScores(snapshot),
            _ => DimensionScores(snapshot, definition.Dimension)
        };

        var normalized = values.Count == 0 ? 0.5m : Clamp(values.Average());
        var raw = normalized;
        var zScore = (normalized - 0.5m) * 2m;
        var interpretation = Interpret(definition.Dimension, normalized, definition.IsHigherRiskOn);

        return new CalculatedFeatureResult(
            definition.Code,
            definition.Name,
            definition.Dimension,
            definition.Weight,
            raw,
            normalized,
            zScore / 10m,
            interpretation);
    }

    private static List<decimal> GrowthScores(AsOfDataSnapshot snapshot)
    {
        var scores = new List<decimal>();
        foreach (var item in snapshot.MacroObservations.Where(x => x.Category.Equals("Growth", StringComparison.OrdinalIgnoreCase)))
        {
            scores.Add(item.SeriesCode.Contains("SAHM", StringComparison.OrdinalIgnoreCase)
                ? 1m - Clamp(item.Value / 0.7m)
                : Clamp((item.Value - 45m) / 15m));
        }

        return scores;
    }

    private static List<decimal> InflationScores(AsOfDataSnapshot snapshot)
    {
        var scores = snapshot.MacroObservations
            .Where(x => x.Category.Equals("Inflation", StringComparison.OrdinalIgnoreCase))
            .Select(x => Clamp(x.Value / 4m))
            .ToList();

        scores.AddRange(snapshot.MarketObservations
            .Where(x => x.Category.Equals("Commodity", StringComparison.OrdinalIgnoreCase))
            .Select(x => Clamp((x.Value - 150m) / 120m)));

        return scores;
    }

    private static List<decimal> RiskScores(AsOfDataSnapshot snapshot)
    {
        var scores = snapshot.MacroObservations
            .Where(x => x.Category.Equals("Risk", StringComparison.OrdinalIgnoreCase))
            .Select(x => 1m - Clamp((x.Value - 10m) / 30m))
            .ToList();

        scores.AddRange(snapshot.MarketObservations
            .Where(x => x.Category.Equals("ETF", StringComparison.OrdinalIgnoreCase))
            .Select(_ => 0.6m));

        return scores;
    }

    private static List<decimal> MonetaryScores(AsOfDataSnapshot snapshot)
    {
        return snapshot.MacroObservations
            .Where(x => x.Category.Equals("Monetary", StringComparison.OrdinalIgnoreCase))
            .Select(x => Clamp((x.Value + 1m) / 3m))
            .ToList();
    }

    private static List<decimal> CreditScores(AsOfDataSnapshot snapshot)
    {
        var scores = snapshot.MacroObservations
            .Where(x => x.Category.Equals("Credit", StringComparison.OrdinalIgnoreCase))
            .Select(x => 1m - Clamp((x.Value - 250m) / 600m))
            .ToList();

        scores.AddRange(snapshot.MarketObservations
            .Where(x => x.Category.Equals("Credit", StringComparison.OrdinalIgnoreCase))
            .Select(x => Clamp(x.Value)));

        return scores;
    }

    private static List<decimal> DimensionScores(AsOfDataSnapshot snapshot, string dimension)
    {
        return snapshot.MacroObservations
            .Where(x => x.Category.Equals(dimension, StringComparison.OrdinalIgnoreCase))
            .Select(_ => 0.5m)
            .ToList();
    }

    private static List<CalculatedRegimeProbability> CalculateProbabilities(IReadOnlyCollection<CalculatedFeatureResult> features, decimal compositeScore)
    {
        var growth = FeatureValue(features, "GROWTH_MOM");
        var inflation = FeatureValue(features, "INFL_PRESS");
        var risk = FeatureValue(features, "RISK_APPETITE");
        var monetary = FeatureValue(features, "MONETARY_COND");
        var credit = FeatureValue(features, "CREDIT_STRESS");

        var raw = new Dictionary<RegimeType, decimal>
        {
            [RegimeType.Goldilocks] = Clamp(growth * risk * (1m - Abs(inflation - 0.45m))),
            [RegimeType.Reflation] = Clamp(compositeScore * inflation * risk),
            [RegimeType.LateCycleOverheating] = Clamp(growth * inflation * (1m - monetary)),
            [RegimeType.Stagflation] = Clamp((1m - growth) * inflation * (1m - credit)),
            [RegimeType.DeflationBust] = Clamp((1m - growth) * (1m - inflation) * (1m - risk)),
            [RegimeType.UncertainTransition] = 0.30m + Clamp(Abs(compositeScore - 0.5m)) * 0.20m
        };

        var total = raw.Values.Sum();
        var probabilities = raw
            .Select(x => new { Regime = x.Key, Probability = total == 0 ? 0m : x.Value / total })
            .OrderByDescending(x => x.Probability)
            .ThenBy(x => x.Regime.ToString())
            .Select((x, index) => new CalculatedRegimeProbability(x.Regime.ToString(), decimal.Round(x.Probability, 4), index + 1))
            .ToList();

        return probabilities;
    }

    private async Task UpsertFeatureValuesAsync(
        IReadOnlyCollection<MacroFeatureDefinition> definitions,
        IReadOnlyCollection<CalculatedFeatureResult> features,
        DateOnly asOfDate,
        CancellationToken cancellationToken)
    {
        foreach (var feature in features)
        {
            var definition = definitions.Single(x => x.Code == feature.Code);
            var existing = await dbContext.MacroFeatureValues
                .FirstOrDefaultAsync(x => x.MacroFeatureDefinitionId == definition.Id && x.AsOfDate == asOfDate, cancellationToken);

            if (existing is null)
            {
                dbContext.MacroFeatureValues.Add(new MacroFeatureValue
                {
                    MacroFeatureDefinitionId = definition.Id,
                    DataAsOfDate = asOfDate,
                    AsOfDate = asOfDate,
                    RawValue = feature.RawValue,
                    NormalizedValue = feature.NormalizedValue,
                    ZScore = (feature.NormalizedValue - 0.5m) * 2m,
                    Momentum4Weeks = feature.Momentum4Weeks,
                    Interpretation = feature.Interpretation
                });
                continue;
            }

            existing.DataAsOfDate = asOfDate;
            existing.RawValue = feature.RawValue;
            existing.NormalizedValue = feature.NormalizedValue;
            existing.ZScore = (feature.NormalizedValue - 0.5m) * 2m;
            existing.Momentum4Weeks = feature.Momentum4Weeks;
            existing.Interpretation = feature.Interpretation;
            existing.UpdatedAt = DateTimeOffset.UtcNow;
        }
    }

    private async Task<RegimeRun> UpsertRunAsync(
        RegimeModelVersion version,
        DateOnly asOfDate,
        RegimeType primaryRegime,
        decimal confidence,
        decimal compositeScore,
        string status,
        string summary,
        IReadOnlyCollection<CalculatedFeatureResult> features,
        IReadOnlyCollection<CalculatedRegimeProbability> probabilities,
        CancellationToken cancellationToken)
    {
        var existing = await dbContext.RegimeRuns
            .Include(x => x.Probabilities)
            .Include(x => x.Explanations)
            .FirstOrDefaultAsync(x => x.RegimeModelVersionId == version.Id && x.AsOfDate == asOfDate, cancellationToken);

        RegimeRun run;
        if (existing is null)
        {
            run = dbContext.RegimeRuns.Add(new RegimeRun
            {
                RegimeModelVersionId = version.Id,
                RunDate = DateOnly.FromDateTime(DateTime.Today),
                AsOfDate = asOfDate,
                PrimaryRegime = primaryRegime,
                Confidence = confidence,
                CompositeScore = compositeScore,
                Status = status,
                Summary = summary
            }).Entity;
        }
        else
        {
            run = existing;
            run.RunDate = DateOnly.FromDateTime(DateTime.Today);
            run.PrimaryRegime = primaryRegime;
            run.Confidence = confidence;
            run.CompositeScore = compositeScore;
            run.Status = status;
            run.Summary = summary;
            run.UpdatedAt = DateTimeOffset.UtcNow;
            dbContext.RegimeProbabilities.RemoveRange(run.Probabilities);
            dbContext.RegimeExplanations.RemoveRange(run.Explanations);

            var oldReports = await dbContext.RegimeReports.Where(x => x.RegimeRunId == run.Id).ToListAsync(cancellationToken);
            dbContext.RegimeReports.RemoveRange(oldReports);
        }

        dbContext.RegimeProbabilities.AddRange(probabilities.Select(x => new RegimeProbability
        {
            RegimeRun = run,
            Regime = Enum.Parse<RegimeType>(x.Regime),
            Probability = x.Probability,
            Rank = x.Rank
        }));

        dbContext.RegimeExplanations.AddRange(features
            .OrderByDescending(x => Math.Abs((double)(x.NormalizedValue - 0.5m)))
            .Take(3)
            .Select(x => new RegimeExplanation
            {
                RegimeRun = run,
                Title = x.Name,
                Detail = x.Interpretation,
                Impact = (x.NormalizedValue - 0.5m) * x.Weight,
                FeatureCode = x.Code
            }));

        dbContext.RegimeReports.Add(new RegimeReport
        {
            RegimeRun = run,
            ReportDate = asOfDate,
            Title = $"Report regime-aware {asOfDate:yyyy-MM-dd}",
            Narrative = summary,
            RecommendedAction = status == "Confirmed"
                ? "Applicare eventuali tilt solo entro i vincoli della policy strategica."
                : "Mantenere allocazione strategica e richiedere conferme sui prossimi rilasci macro.",
            ReviewRequired = status != "Confirmed"
        });

        return run;
    }

    private static List<string> BuildWarnings(int macroCount, int marketCount, IReadOnlyCollection<string> missingDimensions)
    {
        var warnings = new List<string>();
        if (macroCount == 0)
        {
            warnings.Add("Nessuna osservazione macro disponibile nello snapshot as-of.");
        }

        if (marketCount == 0)
        {
            warnings.Add("Nessuna osservazione di mercato disponibile nello snapshot as-of.");
        }

        if (missingDimensions.Count > 0)
        {
            warnings.Add($"Dimensioni mancanti: {string.Join(", ", missingDimensions)}.");
        }

        return warnings;
    }

    private static string BuildSummary(RegimeType primaryRegime, decimal compositeScore, decimal confidence, int warningCount)
    {
        var dataQuality = warningCount == 0 ? "copertura dati completa" : "copertura dati incompleta";
        return $"Il motore rule-based classifica il contesto come {primaryRegime} con composite score {compositeScore:P0}, confidence {confidence:P0} e {dataQuality}.";
    }

    private static string Interpret(string dimension, decimal normalized, bool isHigherRiskOn)
    {
        var direction = normalized >= 0.62m ? "forte" : normalized <= 0.38m ? "debole" : "neutrale";
        var riskTone = isHigherRiskOn
            ? normalized >= 0.5m ? "supporta rischio" : "riduce rischio"
            : normalized >= 0.5m ? "aumenta pressione" : "riduce pressione";

        return $"{dimension}: segnale {direction}, {riskTone}.";
    }

    private static decimal FeatureValue(IEnumerable<CalculatedFeatureResult> features, string code)
    {
        return features.FirstOrDefault(x => x.Code == code)?.NormalizedValue ?? 0.5m;
    }

    private static decimal Clamp(decimal value)
    {
        return Math.Min(1m, Math.Max(0m, value));
    }

    private static decimal Abs(decimal value)
    {
        return Math.Abs(value);
    }

    private sealed record FeatureDefinitionSeed(string Code, string Name, string Dimension, string Formula, decimal Weight, bool IsHigherRiskOn);
}
