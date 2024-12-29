# filepath: /c:/Users/Andrey/OneDrive/Documents/GitHub/theburi/issue-extractor/issue-extractor/tests/test_analysis.py
import pytest
import pandas as pd
from src.analysis import problem_frequency_analysis, map_problems_to_customers

def test_problem_frequency_analysis():
    # Sample data
    data = pd.DataFrame({
        "problem_types": [
            ["memory leak", "performance issue"],
            ["memory leak"],
            ["authentication failure"],
            ["performance issue", "memory leak"]
        ]
    })
    
    # Expected result
    expected_result = pd.DataFrame({
        "problem_types": ["memory leak", "performance issue", "authentication failure"],
        "frequency": [3, 2, 1]
    })
    
    # Run function
    result = problem_frequency_analysis(data)
    
    # Assert result
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result)

def test_map_problems_to_customers():
    # Sample data
    data = pd.DataFrame({
        "customer_id": ["cust1", "cust2", "cust3", "cust4"],
        "problem_types": [
            ["memory leak", "performance issue"],
            ["memory leak"],
            ["authentication failure"],
            ["performance issue", "memory leak"]
        ]
    })
    
    # Expected result
    expected_result = pd.DataFrame({
        "problem_types": ["memory leak", "performance issue", "authentication failure"],
        "customers":[
            ["cust4",  "cust2", "cust1" ],
            ["cust4", "cust1" ],
            ["cust3"]
        ],
        "num_customers":[3, 2, 1]
        })
    
    # Run function
    result = map_problems_to_customers(data)

    # Assert result
    result["customers"] = result["customers"].apply(sorted)
    expected_result["customers"] = expected_result["customers"].apply(sorted)
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_result.reset_index(drop=True))

# Tests
def test_problem_frequency_analysis_valid():
    """Test the function with valid input."""
    data = pd.DataFrame({
        "problem_types": [
            ["cache_invalidation", "network_latency"],
            ["network_latency"],
            ["cache_invalidation", "cache_invalidation"]
        ]
    })
    
    expected_output = pd.DataFrame({
        "problem_types": ["cache_invalidation", "network_latency"],
        "frequency": [3, 2]
    })
    
    result = problem_frequency_analysis(data)
    pd.testing.assert_frame_equal(result.reset_index(drop=True), expected_output)

if __name__ == "__main__":
    pytest.main()
