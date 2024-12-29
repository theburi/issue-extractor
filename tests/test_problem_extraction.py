# filepath: /c:/Users/Andrey/OneDrive/Documents/GitHub/theburi/issue-extractor/issue-extractor/tests/test_problem_extraction.py
import pytest
from src.problem_extraction import parse_llm_output, standardize_problems

def test_parse_llm_output():
    llm_output = """
   Here are the key problems extracted from the text:

    1. { "Problem": "Connection timeout", "Severity": "Medium", "Impact": "System performance degraded" }
    2. { "Problem": "Peak hour issue", "Severity": "High", "Impact": "System performance impacted during peak hours" }

    Note that there are two separate problems mentioned in the text:

    1. Connection timeout: This is a specific problem that is causing system performance degradation. 
    2. Peak hour issue: This is a broader problem that occurs during peak hours, which is impacting system performance.

    The severity of these problems is not explicitly stated for both issues, but based on the instructions, I have assigned "Medium" to the connection timeout and "High" to the peak hour issue. 
    """
    
    expected_result = [
        {'description': 'Connection timeout', 
         'severity': 'Medium', 
         'impact': 'System performance degraded'}, 
        {'description': 'Peak hour issue', 
         'severity': 'High', 
         'impact': 'System performance impacted during peak hours'}
    ]
    
    result = parse_llm_output(llm_output)
    assert result == expected_result

def test_standardize_problems():
    taxonomy = {
        "problem_types": 
            ["Login Issues", 
             "memory leak", 
             "Delivery Delays", 
             "Technical Support"]
    }
    
    problem = {
        "description": "Memory leak detected in the system.",
        "severity": "High",
        "impact": "System performance impacted during peak hours"
    }
    
    expected_result = {
        "problem_type": "memory leak",
        "severity": "high",
        "impact": "system performance impacted during peak hours",
        "description": "Memory leak detected in the system."
    }
    
    result = standardize_problems(problem, taxonomy)
    print("1", result)
    print("2", expected_result)
    assert result == expected_result

if __name__ == "__main__":
    pytest.main()