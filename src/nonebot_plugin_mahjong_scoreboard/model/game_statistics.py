from typing import NamedTuple, List, Optional


class GameStatistics(NamedTuple):
    total: int
    total_east: int
    total_south: int
    rates: List[float]
    avg_rank: float
    pt_expectation: Optional[float]
    flying_rate: float
