# AI Market Research System

An agent-based AI market research application that automates research planning, web search, evidence extraction, evidence validation, market analysis, and report generation.

## Features

- **Research planning:** Breaks a research question into focused research tasks.
- **Web search:** Finds relevant sources using Tavily.
- **Evidence extraction:** Extracts claims and supporting information from research sources.
- **Evidence validation:** Classifies evidence as accepted, needs review, or rejected.
- **Market analysis:** Aggregates accepted evidence into findings, trends, and charts.
- **Report generation:** Generates a structured research report with citations.
- **PDF export:** Produces a downloadable PDF report.

## Architecture

The application uses six agents:

1. Planner
2. Search
3. Extract
4. Validate
5. Aggregate
6. Report

Supporting services handle language-model access, web-page fetching, source credibility, chart generation, and PDF creation.

## Technology Stack

- Python
- Google Gemini API
- Tavily Search API
- Pydantic
- Matplotlib
- Plotly
- ReportLab

## Project Setup

### 1. Clone or download the project

Open a terminal in the project directory.

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows PowerShell:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file in the project root:

```env
GEMINI_API_KEY=your_gemini_api_key
GEMINI_MODEL=your_gemini_model
TAVILY_API_KEY=your_tavily_api_key
```

Replace the example values with your own credentials.

**Never commit or share your actual `.env` file.**

## Run the Application

Example:

```bash
python orchestrator.py "Artificial Intelligence market opportunities and challenges in India" --geography India --timeframe "2025-2030" --industry "Artificial Intelligence"
```

The orchestrator executes the research pipeline and generates the report.

## Output

Generated files are stored under `storage/`:

- `storage/jobs/` — Research plans, validated evidence, reports, and run summaries.
- `storage/reports/` — Generated PDF reports.
- `storage/charts/` — Generated chart images.

## Testing

Run the offline regression tests:

```bash
python test_report_rules.py
python test_text_cleaning.py
python test_report_snapshot.py
python test_aggregate_rules.py
python test_aggregate_competitors.py
python test_pdf.py
python test_charts.py
```

Some additional `test_*_ai.py` tests call external APIs and may require valid API keys and internet access.

Compile the application:

```bash
python -m compileall -q orchestrator.py schemas.py agents services
```

## Important Notes

- Only accepted evidence is used for the main findings and charts.
- Evidence requiring review is kept separate from accepted findings.
- Generated research reports should be reviewed before being used for business decisions or publication.
- Market estimates and forecasts depend on the sources collected and are not independently guaranteed to be accurate.