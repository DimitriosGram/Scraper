import pandas as pd
import datetime
from Business.main import clean_sheet
import pytest

@pytest.mark.filterwarnings
def test_clean_sheet(mocker):
    # Mocking the opening_files function to return predefined DataFrames
    mock_opening_files = mocker.patch('Business.main.opening_files', return_value=[
        pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(),
        pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
    ])

    # Mocking the download_history function to return a predefined DataFrame
    mock_download_history = mocker.patch('Business.main.download_history', return_value=pd.DataFrame({
        2: ['Bank A', 'Bank B', 'Bank C', 'Bank D'],
        8: ['1 Year Bond', '2 Year Bond', '3 Year Bond', '5 Year Bond'],
        6: ['Notice', 'Notice', 'Notice', 'Notice'],
        7: ['Variable', 'Fixed', '-', '-'],
        15: ['1.5%', '2.5%', '3.5%', '4.5%'],
        5: [datetime.date.today(), datetime.date.today(), datetime.date.today(), datetime.date.today()]
    }).reset_index(drop=True))

    # Ensure the mock DataFrame index starts from 1 to align with your function's expectations
    mock_download_history.return_value.index = range(1, len(mock_download_history.return_value) + 1)

    # Call the clean_sheet function
    df_1year, df_2year, df_3year, df_5year, df_7day, df_35day, df_95day, df_ea, df_6month, df_120day, df_180day = clean_sheet()

    # Assertions to check if the DataFrames are as expected
    assert not df_1year.empty
    assert df_1year.iloc[0]['Name'] == 'Bank A'
    assert df_1year.iloc[0]['Rate'] == '1.5%'
    assert df_1year.iloc[0]['Product'] == '1 Year Bond'

    assert not df_2year.empty
    assert df_2year.iloc[0]['Name'] == 'Bank B'
    assert df_2year.iloc[0]['Rate'] == '2.5%'
    assert df_2year.iloc[0]['Product'] == '2 Year Bond'

    assert not df_3year.empty
    assert df_3year.iloc[0]['Name'] == 'Bank C'
    assert df_3year.iloc[0]['Rate'] == '3.5%'
    assert df_3year.iloc[0]['Product'] == '3 Year Bond'

    assert not df_5year.empty
    assert df_5year.iloc[0]['Name'] == 'Bank D'
    assert df_5year.iloc[0]['Rate'] == '4.5%'
    assert df_5year.iloc[0]['Product'] == '5 Year Bond'

    # Check that other DataFrames are empty
    assert df_7day.empty
    assert df_35day.empty
    assert df_95day.empty
    assert df_ea.empty
    assert df_6month.empty
    assert df_120day.empty
    assert df_180day.empty
