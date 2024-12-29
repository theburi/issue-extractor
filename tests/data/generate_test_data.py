import json
import random
from datetime import datetime, timedelta
from pymongo import MongoClient

def generate_test_data(num_records=100):
    problems = [
        "Login authentication failure",
        "Slow application response",
        "Data sync issues",
        "UI not responding",
        "Connection timeout",
        "Invalid configuration",
        "Memory leak detected",
        "API rate limit exceeded",
        "Database connection error",
        "Cache invalidation problem"
    ]
    
    customers = [f"customer_{i}" for i in range(1, 21)]
    severity = ["low", "medium", "high", "critical"]
    
    dataset = []
    
    for i in range(num_records):
        record = {
            "customer_id": random.choice(customers),
            "timestamp": (datetime.now() - timedelta(days=random.randint(0, 30))).isoformat(),
            "communication": f"""
                Issue Report:
                Customer is experiencing {random.choice(problems)}.
                Impact: System performance degraded by {random.randint(10, 90)}%.
                Attempted Solutions: Restart service, clear cache.
                Additional Notes: Issue occurs during peak hours.
            """.strip(),
            "severity": random.choice(severity),
            "status": random.choice(["open", "in_progress", "resolved"])
        }
        dataset.append(record)
    
    return dataset

if __name__ == "__main__":
    data = generate_test_data()
    client = MongoClient("mongodb://localhost:27017/")
    db = client["issue_extractor"]
    collection = db["test_data"]

    collection.insert_many(data)