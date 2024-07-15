import pandas as pd
from pandas.testing import assert_frame_equal
from Personal.main import clean_workbooks

import datetime

def test_clean_workbooks():
    # Sample data for dfTable (original table)
    dfTable = pd.DataFrame({
        'Name': ["Existing Bank"],
        'Rate': ["4.5"],
        'Product': ["Existing Account Type"],
        'Date': ["01/01/2024"],
        'Rank': [1]
    })

    # Sample raw scraped data
    data_scrape = pd.DataFrame({
        "2": ["Charter Savings Bank", "Hinckley & Rugby BS", "United Trust Bank"],  # Bank Name / Provider
        "4": ["90 Day Notice Account (Issue 4)", "95 Day Notice - Issue 63", "45 Day Notice Personal Account Issue 14"],  # Account
        "5": ["Variable", "Variable", "Variable"],  # Account Type
        "6": ["10/06/2024", "10/06/2024", "10/06/2024"],  # as of date
        "7": ["90 Day", "95 Day", "45 Day"],  # Term
        "8 ": ["90", '-', "45"],  # Term days
        "9": ["4.9", "4.95", "4.45"],  # AER
    })
    
    # Correct column data type for '8 ' (Term days) before calling the function
    data_scrape.iloc[:, 6] = data_scrape.iloc[:, 6].replace('-', -1)
    data_scrape.iloc[:, 6] = pd.to_numeric(data_scrape.iloc[:, 6], errors='coerce').fillna(-1).astype(int)
    
    # Call the function for a specific round (e.g., round 45)
    result = clean_workbooks(45, dfTable, data_scrape)
    print(result)



