import pandas as pd
import json
import sys
import os
import matplotlib.pyplot as plt

if len(sys.argv) != 2:
    print("Usage: open_in_pandas.py <file_path>")
else:
    file_path = sys.argv[1]
    file_ext = os.path.splitext(file_path)[1].lower()
    
    try:
        if file_ext == '.csv':
            df = pd.read_csv(file_path)
            print(f"CSV file '{file_path}' loaded into DataFrame 'df'.")
        elif file_ext == '.xlsx':
            df = pd.read_excel(file_path)
            print(f"Excel file '{file_path}' loaded into DataFrame 'df'.")
        elif file_ext == '.json':
            with open(file_path, 'r') as f:
                data = json.load(f)
            print(f"JSON file '{file_path}' loaded into dictionary 'data'.")
        else:
            print(f"Unsupported file type: {file_ext}")
            sys.exit(1)
    except Exception as e:
        print(f"Error loading file: {e}")
        sys.exit(1)