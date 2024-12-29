import re
import json
import logging
from typing import Dict, List

def parse_llm_output(output: str) -> List[Dict]:
    """Parse LLM output to extract problems, severity, and impact."""
    problems = []
    problem_pattern = re.compile(r'\d+\.\s*({.*?})')

    matches = problem_pattern.findall(output)
    for match in matches:
        try:
            problem = json.loads(match)
            problems.append({
                "description": problem.get("Problem", "").strip(),
                "severity": problem.get("Severity", "").strip(),
                "impact": problem.get("Impact", "").strip()
            })
        except json.JSONDecodeError as e:
            logging.error(f"Error parsing problem JSON: {str(e)}")
            continue

    return problems

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
            impact = "general"

        return {
            "problem_type": problem_type,
            "severity": severity,
            "impact": impact,
            "description": description
        }

    except Exception as e:
        logging.error(f"Error in standardizing problem: {str(e)}", exc_info=True)
        return None
