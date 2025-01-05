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
             # Use regex to locate the JSON-like structure in the output
            json_pattern = re.compile(r'"?Problem"?:.*?"?Severity"?:.*?"?Impact"?:.*?(?=\n\n|$)', re.DOTALL)
            matches2 = json_pattern.findall(output)
            if not matches2:
                raise ValueError("No JSON array found in the output.")
            for match1 in matches2:
                # Add braces to ensure valid JSON
                print ("match ",match1)
                json_block = "{" + match1 + "}"
                parsed_data = json.loads(json_block)

                problems.append({
                    "description": parsed_data.get("Problem", "").strip(),
                    "severity": parsed_data.get("Severity", "").strip(),
                    "impact": parsed_data.get("Impact", "").strip()
                })
        else:           
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
