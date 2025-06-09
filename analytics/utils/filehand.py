import csv
from io import StringIO
from typing import List, Dict
def convert_to_csv(data: List[Dict]) -> StringIO:
    """
    Creates a CSV file in memory from a list of dictionaries.

    Args:
        data (List[Dict[str, str]]): The data to write to the CSV. Each dictionary represents a row.

    Returns:
        StringIO: A StringIO object containing the CSV data.
    """
    if not data or not isinstance(data, list) or not all(isinstance(row, dict) for row in data):
        raise ValueError("Data must be a list of dictionaries.")

    csv_buffer = StringIO()
    writer = csv.DictWriter(csv_buffer, fieldnames=data[0].keys())
    writer.writeheader()
    writer.writerows(data)
    csv_buffer.seek(0)
    return csv_buffer.getvalue()
