import re
import json
import logging
from typing import Dict, List

def parse_llm_output(output: str) -> List[Dict]:
    """Parse LLM output to extract problems, severity, and impact using regex."""
    problems = []
    parsed_data={}
    try:
        # Use regex to locate the JSON array in the output
        json_pattern = re.compile(r'\[\s*{.*?}\s*]', re.DOTALL)
        match = json_pattern.search(output)
        if not match:
            raise ValueError("No JSON array found in the output.")
        
        # Extract the JSON block
        json_block = match.group(0)
        parsed_data = json.loads(json_block)
        
        # Process each problem in the JSON list
        for problem in parsed_data:
            problems.append({
                "description": problem.get("Problem", "").strip(),
                "severity": problem.get("Severity", "").strip(),
                "impact": problem.get("Impact", "").strip()
            })
    except (json.JSONDecodeError, ValueError) as e:
        logging.error(f"Error parsing LLM output JSON: {output} \n Exception: {str(e)}")
        return problems  # Return an empty list if parsing fails
    
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

        return {
            "problem_type": problem_type,
            "severity": severity,
            "impact": impact,
            "description": description
        }

    except Exception as e:
        logging.error(f"Error in standardizing problem: {str(e)}", exc_info=True)
        return None
