
# 🏗️ Multi-Agent Architecture: Language Services Baseline Factory

This diagram illustrates the flow of data through specialized agents, transforming messy vendor files into strategic insights.

```mermaid
graph TD
    %% --- INPUT LAYER ---
    Files[(Vendor Files)] -->|Scanned| Orchestrator[Orchestrator Agent]

    %% --- INTAKE & EXTRACTION ---
    subgraph "Intake & Extraction Layer"
        Orchestrator -->|Analyze Structure| Intake[Intake Classifier]
        Intake -->|Identify File Type| Extractor[Extractor Agent]
        Extractor -->|Raw Data| Schema[Schema Mapper Agent]
        Schema -->|Column Map| Standardizer[Standardizer Agent]
    end

    %% --- ENRICHMENT & QA ---
    subgraph "Enrichment & Quality Assurance"
        Standardizer -->|Missing Costs?| RateCard[Rate Card Agent]
        RateCard -->|Imputed Rates| Standardizer
        
        Standardizer -->|Canonical Record| QA[QA Agent]
        QA -->|Anomlies Flagged| ExceptionQueue[(Exception Queue)]
        QA -->|Clean Record| Aggregator
    end

    %% --- ANALYTICS ---
    subgraph "Analytics & Strategic Layer"
        Aggregator[Aggregator Agent] -->|Baseline Table (v1)| Analyst[Analyst Agent]
        
        Analyst -->|Mix Analysis (v7)| Simulator[Simulator Agent]
        Analyst -->|Benchmark Gaps (v9)| Advisor[Recommendation Agent]
        
        Simulator -->|Savings Scenarios (v10)| Advisor
        
        Advisor -->|Opportunity Register (v12)| Composer[Report Composer]
    end

    %% --- OUTPUT ---
    Composer -->|Final Report| Report[(Baseline Report.pdf)]
```

## Agent Roles & Responsibilities

| Agent Role | Responsibility | Input | Output |
| :--- | :--- | :--- | :--- |
| **Orchestrator** | Manages the workflow, routes files, handles errors. | Project Folder | Task Assignments |
| **Intake Classifier** | Identifies vendor (e.g. "Propio"), file type, and grain. | File Metadata | "Vendor: Propio, Type: Transaction" |
| **Extractor** | Reads Excel/PDF content robustly. | File Path | Raw DataFrame |
| **Schema Mapper** | Maps variable headers to canonical fields. | Raw Columns | `{"Duration": "Minutes"}` |
| **Standardizer** | Normalizes dates, languages, modalities. | Raw Rows + Map | Canonical Record |
| **Rate Card Agent** |  *Specialized:* Looks up contract rates for missing costs. | Vendor + Modality | Imputed Cost |
| **QA Agent** | Validates data logic (e.g. Rate < $10/min). | Canonical Record | Validated Record + Quality Flags |
| **Aggregator** | Compiles the `v1 Baseline` table. | Clean Records | Aggregated DataFrame |
| **Analyst Agent** | Performs "Mix Analysis" (Price vs Volume effect). | Baseline Table | Variance Report |
| **Simulator Agent** | Runs "What-If" scenarios (e.g. VRI->OPI shift). | Baseline + Rates | Savings Totals |
| **Recommendation Agent** | Prioritizes opportunities by ROI. | Savings Totals | Opportunity Register |
| **Report Composer** | Formats final output (Excel/PDF). | All Data | Final Deliverable |
