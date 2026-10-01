"""CAGR calculation engine handling financial edge cases and flags."""
import math
from typing import Tuple, Optional, Any

def calculate_cagr(base_val: Any, end_val: Any, periods: int) -> Tuple[Optional[float], str, str]:
    """
    Compute CAGR with comprehensive edge-case handling.
    Returns: (cagr_val_or_None, flag, display_string)
    """
    if periods < 3:
        return None, "INSUFFICIENT", "N/A - < 3yr"
    
    try:
        base = float(base_val)
        end = float(end_val)
    except (ValueError, TypeError):
        return None, "INVALID_INPUT", "N/A - invalid"
    
    if math.isnan(base) or math.isnan(end):
        return None, "MISSING_DATA", "N/A - missing"
        
    if base == 0:
        return None, "ZERO_BASE", "N/A - base=0"
        
    if base > 0 and end > 0:
        cagr = ((end / base) ** (1.0 / periods) - 1.0) * 100.0
        return round(cagr, 2), "NORMAL", f"{cagr:.1f}%"
        
    if base > 0 and end < 0:
        return None, "DECLINE_TO_LOSS", "N/A - turned loss"
        
    if base < 0 and end > 0:
        return None, "TURNAROUND", "Turnaround ↑"
        
    if base < 0 and end < 0:
        return None, "BOTH_NEGATIVE", "N/A - both loss"
        
    return None, "UNKNOWN", "N/A"
