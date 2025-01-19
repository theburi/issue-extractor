
import logging
from typing import Dict, List

def standardize_problems(problem: Dict, taxonomy: Dict) -> Dict:
    """Standardize problems based on taxonomy."""
    try:
        problem_type = None
        severity = problem.get("severity", "low").lower()
        impact = problem.get("impact", "general").lower()
        description = problem.get("description", "")

        for p_type in taxonomy["problem_types"]:
            if p_type in description.lower():
                problem_type = p_type
                break

        if not problem_type:
            problem_type = "unknown"
            severity = "low"

        return {
            "problem_type": problem_type,
            "severity": severity,
            "impact": impact,
            "description": description
        }

    except Exception as e:
        logging.error(f"Error in standardizing problem: {str(e)}", exc_info=True)
        return None
