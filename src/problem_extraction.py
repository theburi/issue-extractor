import re
import json
import logging
from typing import Dict, List
from langchain_core.prompts import PromptTemplate 

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
        # Use regex to locate the JSON-like structure in the output
        json_pattern = re.compile(r'"Problem":.*?"Severity":.*?"Impact":.*?(?=\n|$)', re.DOTALL)
        matches = json_pattern.findall(output)

        for match in matches:
            # Add braces to ensure valid JSON
            json_block = "{" + match + "}"
            parsed_data = json.loads(json_block)

            problems.append({
                "description": parsed_data.get("Problem", "").strip(),
                "severity": parsed_data.get("Severity", "").strip(),
                "impact": parsed_data.get("Impact", "").strip()
            })

        return problems  # Return an empty list if parsing fails
    
    return problems

def standardize_problems(problem: Dict, taxonomy: Dict, llm, template) -> Dict:
    """Standardize problems based on taxonomy."""
    try:
        problem_type = None
        severity = problem.get("severity", "low").lower()
        impact = problem.get("impact", "general").lower()
        description = problem.get("description", "")


        # Prepare prompt for LLM to classify problem type
        prompt = PromptTemplate(
            template=template,
            input_variables=["description", "problem_types"]
        )

        # Run LLM chain to classify problem
        chain = prompt | llm
        problem_type = chain.invoke({
            "description": description,
            "problem_types": ", ".join(taxonomy["problem_types"])
        })

        problem_type = next(
            (ptype for ptype in taxonomy["problem_types"] if ptype.lower() in problem_type.lower()),
            "unknown"
        )
        if problem_type == "unknown":
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
