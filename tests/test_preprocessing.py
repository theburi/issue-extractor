import pytest
import pandas as pd
from src.preprocessing import clean_text, clean_data, add_metadata

def test_clean_text():
    raw_text = "Check out our website at http://example.com! It's amazing. :)"
    expected_text = "check out our website at its amazing"
    assert clean_text(raw_text) == expected_text

def test_clean_data():
    raw_data = pd.DataFrame({"communication": ["Hello!", None, "   "]})
    cleaned_data = clean_data(raw_data)
    assert len(cleaned_data) == 1
    assert cleaned_data["communication"].iloc[0] == "hello"

def test_add_metadata():
    data = pd.DataFrame({"communication": ["hello", "world"]})
    metadata_data = add_metadata(data)
    assert "processed_at" in metadata_data.columns
    assert "customer_id" in metadata_data.columns
