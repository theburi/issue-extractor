import pytest
import pandas as pd
from src.summarization import summarize_text, batch_summarize

def test_summarize_text():
    raw_text = "I am unable to log into my account. The system keeps showing an error."
    summary = summarize_text(raw_text)
    assert isinstance(summary, str)
    assert len(summary) > 0

def test_batch_summarize():
    data = pd.DataFrame({"communication": [
        "I am unable to log into my account.",
        "The billing system charged me twice for the same transaction."
    ]})
    summarized_data = batch_summarize(data, text_column="communication")
    assert "summary" in summarized_data.columns
    assert len(summarized_data["summary"]) == len(data)
