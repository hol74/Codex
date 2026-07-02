using Finance.Application.Portfolios;
using Finance.Application.PhaseOne;
using Finance.Application.Ledger;
using Finance.Application.MacroRegime;
using Finance.Application.Performance;
using Finance.Infrastructure.Data;
using Finance.Infrastructure.Services;
using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.DependencyInjection;

namespace Finance.Infrastructure;

public static class DependencyInjection
{
    public static IServiceCollection AddFinanceInfrastructure(this IServiceCollection services, string connectionString)
    {
        services.AddDbContext<FinanceDbContext>(options => options.UseSqlite(connectionString));
        services.AddScoped<IPortfolioDashboardService, PortfolioDashboardService>();
        services.AddScoped<IPhaseOneReadService, PhaseOneReadService>();
        services.AddScoped<ILedgerService, LedgerService>();
        services.AddScoped<IPerformanceService, PerformanceService>();
        services.AddScoped<IMacroRegimeService, MacroRegimeService>();
        services.AddSingleton<HttpClient>();
        services.AddScoped<IMacroDataFoundationService, MacroDataFoundationService>();
        services.AddScoped<IRegimeCalculationService, RegimeCalculationService>();

        return services;
    }
}
