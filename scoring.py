"""Transparent initial scoring heuristics; not validated predictions."""
DEFAULT_WEIGHTS = {"premium_positioning":25,"ambience_presentation":20,"specialty_or_distinctive":15,"independent_boutique":15,"digital_opportunity":15,"expansion_potential":10}
def score_lead(evidence, weights=None, manual_adjustment=0):
    weights = weights or DEFAULT_WEIGHTS
    total, breakdown = 0, []
    for key, weight in weights.items():
        value = evidence.get(key)
        points = int(weight) if value is True or value == 1 else 0
        total += points
        breakdown.append({"factor":key.replace("_"," ").title(),"weight":int(weight),"evidence":"Yes" if points else ("No" if value is False or value == 0 else "Unknown"),"points":points,"reason":"Research supports this factor" if points else "Unknown or unsupported; no points awarded"})
    try: adjustment = max(-100,min(100,int(manual_adjustment or 0)))
    except (ValueError,TypeError): adjustment = 0
    return max(0,min(100,total+adjustment)), breakdown
def priority_for_score(score): return "High" if score >= 70 else "Medium" if score >= 45 else "Low"
