# Fase B Import Dati e Diagnostica Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implementare la Fase B del piano operativo: report diagnostico import/config, superficie Web read-only per la diagnostica e batch CLI multi-data per popolare lo storico.

**Architecture:** La validazione diventa un use case applicativo indipendente dal filesystem concreto; Infrastructure fornisce l'adapter JSON e il renderer markdown della diagnostica. CLI e Web riusano lo stesso modello diagnostico senza cambiare il Domain e senza introdurre database o rete runtime.

**Tech Stack:** C# net10.0, xUnit, Razor Pages, JSON file-based, Markdown artifact.

---

## File Structure

- Create `src/MacroRegime.Application/Import/ImportValidation.cs`: command/result/read model per diagnostica import/config.
- Create `src/MacroRegime.Application/Ports/IImportValidationService.cs`: porta applicativa per validare input e configurazioni.
- Create `src/MacroRegime.Infrastructure/Import/JsonImportValidationService.cs`: validazione file JSON e as-of usando gli stessi mapper degli adapter esistenti.
- Create `src/MacroRegime.Infrastructure/Import/ImportValidationMarkdownRenderer.cs`: artifact markdown leggibile.
- Modify `src/MacroRegime.Cli/Program.cs`: opzioni `--validate-only`, `--validate-report`, `--batch-from`, `--batch-to`, `--data-dir`, `--portfolio-dir`; single run invariata.
- Modify `src/MacroRegime.Web/Services/MacroRegimeWebAnalysisService.cs`: metodo per caricare diagnostica read-only.
- Create `src/MacroRegime.Web/Pages/ImportDiagnostics.cshtml(.cs)`: pagina diagnostica import/config.
- Modify `src/MacroRegime.Web/Pages/Shared/_Layout.cshtml`: link alla diagnostica.
- Test: Application/Infrastructure/CLI/Web con TDD.
- Docs: checkpoint `docs/checkpoints/0022-fase-b-import-diagnostica-done.md`, aggiornamento `docs/0001-piano-operativo.md` e `docs/0002-riepilogo-lavoro-svolto.md`.

## Task 1: Validate-Only Diagnostics Core

**Files:**
- Create: `src/MacroRegime.Application/Import/ImportValidation.cs`
- Create: `src/MacroRegime.Application/Ports/IImportValidationService.cs`
- Create: `src/MacroRegime.Infrastructure/Import/JsonImportValidationService.cs`
- Create: `src/MacroRegime.Infrastructure/Import/ImportValidationMarkdownRenderer.cs`
- Test: `tests/MacroRegime.Infrastructure.Tests/Import/JsonImportValidationServiceTests.cs`

- [ ] Step 1: Write failing tests for valid input, missing non-strict input warning, strict missing input error, and markdown content.
- [ ] Step 2: Run targeted Infrastructure tests and verify failures because types do not exist.
- [ ] Step 3: Implement minimal Application contracts and Infrastructure service/renderer.
- [ ] Step 4: Run targeted Infrastructure tests and verify pass.

## Task 2: CLI Validate-Only and Validation Report

**Files:**
- Modify: `src/MacroRegime.Cli/Program.cs`
- Test: `tests/MacroRegime.Cli.Tests/MacroRegimeCliTests.cs`

- [ ] Step 1: Write failing CLI tests for `--validate-only` writing markdown without run artifacts and for strict missing data returning exit code 2 with validation report.
- [ ] Step 2: Run targeted CLI tests and verify failures.
- [ ] Step 3: Add CLI options and validation execution path before the normal pipeline.
- [ ] Step 4: Run targeted CLI tests and verify pass.

## Task 3: CLI Multi-Date Batch Import

**Files:**
- Modify: `src/MacroRegime.Cli/Program.cs`
- Test: `tests/MacroRegime.Cli.Tests/MacroRegimeCliTests.cs`

- [ ] Step 1: Write failing CLI test for `--batch-from` / `--batch-to` using `--data-dir` and `--portfolio-dir` with files named `macro-data-yyyy-MM-dd.json` and `current-portfolio-yyyy-MM-dd.json`.
- [ ] Step 2: Run targeted CLI test and verify failure.
- [ ] Step 3: Implement batch loop over existing `RunRegimeAnalysisUseCase`, with manifest upsert per date and continue-on-error summary.
- [ ] Step 4: Run targeted CLI tests and verify pass.

## Task 4: Web Import Diagnostics

**Files:**
- Modify: `src/MacroRegime.Web/Services/MacroRegimeWebAnalysisService.cs`
- Create: `src/MacroRegime.Web/Pages/ImportDiagnostics.cshtml`
- Create: `src/MacroRegime.Web/Pages/ImportDiagnostics.cshtml.cs`
- Modify: `src/MacroRegime.Web/Pages/Shared/_Layout.cshtml`
- Test: `tests/MacroRegime.Web.Tests/MacroRegimeWebTests.cs`

- [ ] Step 1: Write failing Web test for `/ImportDiagnostics` rendering input statuses and validation report.
- [ ] Step 2: Run targeted Web tests and verify failure.
- [ ] Step 3: Implement read-only page using the shared validation service.
- [ ] Step 4: Run targeted Web tests and verify pass.

## Task 5: Documentation and Verification

**Files:**
- Create: `docs/checkpoints/0022-fase-b-import-diagnostica-done.md`
- Modify: `docs/0001-piano-operativo.md`
- Modify: `docs/0002-riepilogo-lavoro-svolto.md`

- [ ] Step 1: Run full build.
- [ ] Step 2: Run full test suite.
- [ ] Step 3: Run smoke CLI validate-only and batch.
- [ ] Step 4: Run smoke Web diagnostics.
- [ ] Step 5: Update docs with evidence.

