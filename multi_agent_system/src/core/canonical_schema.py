
from dataclasses import dataclass
from typing import Optional
import datetime

@dataclass
class CanonicalRecord:
    """
    The standard format for a single line item of language service usage.
    Agents must map raw data to this structure.
    """
    source_file: str
    vendor: str
    date: datetime.date
    timestamp_start: Optional[datetime.datetime] = None
    timestamp_end: Optional[datetime.datetime] = None
    
    language: str = "Unknown"
    modality: str = "OPI" # OPI, VRI, OnSite, Translation
    
    minutes_billed: float = 0.0
    calls_count: int = 1 # Usually 1 for line item, but could be aggregated
    
    total_charge: float = 0.0
    rate_per_minute: float = 0.0
    
    # Metadata for tracing
    raw_columns: dict = None
    confidence_score: float = 1.0 # 0.0 to 1.0 based on extraction quality

# Define the expected fields for the Schema Mapper target
CANONICAL_FIELDS = {
    "date": ["date", "call date", "invoice date", "service date", "job date", "start date", "year-month", "month", "period"],
    "language": ["language", "lang", "source language", "target language"],
    "minutes": ["duration", "minutes", "min", "qty", "quantity", "billable time", "connect time (minutes:seconds)", "minuteswithtpd"],
    "charge": ["total charge", "amount", "total", "line total", "extended price", "chargeswithtpd", "charges", "cost", "total cost"],
    "rate": ["rate", "unit price", "price"],
    "modality": ["service line", "service type", "modality", "product"]
}
