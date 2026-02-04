# Multi-agent architecture (roles)

- Orchestrator: run management, routing  
- Intake Classifier: vendor/client/grain detection  
- Extractor: Excel/PDF/OCR extraction to stg_raw_*  
- Schema Mapper: mapping templates + confidence gating  
- Standardizer: canonical facts (fct_*) + dedupe  
- QA Agent: qa_* + baseline_confidence  
- Aggregator: agg_baseline_* + rate/mix views  
- Benchmark & Scenario Agent: variance + savings tables  
- Recommendation Agent: opportunity_register  
- Report Composer: deliverable generation
