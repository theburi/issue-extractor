import pytest
import pandas as pd
from src.reporting import generate_problem_report, visualize_problem_frequencies, visualize_trends
import os

def test_generate_problem_report():
    frequency_data = pd.DataFrame({
        "problem": ["Login Issue", "Billing Error"],
        "frequency": [25, 15]
    })
    output_path = "./tests/results/problem_report_test.csv"
    generate_problem_report(frequency_data, output_path)
    assert os.path.exists(output_path)

def test_visualize_problem_frequencies():
    frequency_data = pd.DataFrame({
        "problem": ["Login Issue", "Billing Error"],
        "frequency": [25, 15]
    })
    output_path = "./tests/results/problem_frequencies_test.png"
    visualize_problem_frequencies(frequency_data, output_path)
    assert os.path.exists(output_path)

def test_visualize_trends():
    trend_data = pd.DataFrame({
        "date": ["2024-12-24", "2024-12-25", "2024-12-26"],
        "problems": ["Login Issue", "Login Issue", "Billing Error"],
        "frequency": [5, 10, 8]
    })
    trend_data["date"] = pd.to_datetime(trend_data["date"])
    output_path = "./tests/results/problem_trends_test.png"
    visualize_trends(trend_data, output_path)
    assert os.path.exists(output_path)
