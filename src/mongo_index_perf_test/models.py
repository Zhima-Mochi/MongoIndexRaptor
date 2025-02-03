from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional

@dataclass
class TestResult:
    """Data class for test results"""
    query: Dict[str, Any]
    hint: Dict[str, int]
    iteration: int
    warmup_iteration: int
    sample_interval: int
    avg_time: float
    min_time: float
    max_time: float
    stdev_time: float
    percentile_95: float = 0.0
    percentile_99: float = 0.0
    avg_docs_examined: float = 0.0
    avg_keys_examined: float = 0.0
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert test result to dictionary"""
        return asdict(self)


@dataclass
class TestQuery:
    """Data class for test query configuration"""
    name: str
    query: Dict[str, Any]
    hints: List[Dict[str, int]]
    database: str
    collection: str

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TestQuery":
        """Create TestQuery instance from dictionary"""
        if "database" not in data:
            raise ValueError(f"database is required")
        if "collection" not in data:
            raise ValueError(f"collection is required")
        return cls(
            name=data["name"],
            query=data["query"],
            hints=data.get("hints", []),
            database=data["database"],
            collection=data["collection"],
        )

    def __hash__(self):
        return hash((str(self.query), str(self.hints)))
