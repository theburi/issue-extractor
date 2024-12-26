import pytest
import pandas as pd
from src.analysis import problem_frequency_analysis, map_problems_to_customers, analyze_problem_trends

def test_problem_frequency_analysis():
    data = pd.DataFrame({
        "problems": [["login issue", "billing error"], ["login issue"], ["delivery delay"]]
    })
    result = problem_frequency_analysis(data)
    assert len(result) == 3
    assert result.loc[result["problem"] == "login issue", "frequency"].iloc[0] == 2

def test_map_problems_to_customers():
    data = pd.DataFrame({
        "customer_id": [1, 2, 3],
        "problems": [["login issue"], ["billing error"], ["login issue", "delivery delay"]]
    })
    result = map_problems_to_customers(data)
    assert "login issue" in result["problem"].values
    assert len(result.loc[result["problem"] == "login issue", "customers"].iloc[0]) == 2

def test_analyze_problem_trends():
    data = pd.DataFrame({
        "processed_at": ["2024-12-24", "2024-12-24", "2024-12-25"],
        "problems": [["login issue"], ["billing error"], ["login issue", "delivery delay"]]
    })
    result = analyze_problem_trends(data, date_column="processed_at")
    assert "login issue" in result["problems"].values
    assert result.loc[result["problems"] == "login issue", "frequency"].sum() == 2
