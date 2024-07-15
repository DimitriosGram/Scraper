from numpy import int64
import selenium 
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
import time
from selenium.webdriver.chrome.options import Options
import json
import datetime
import pandas as pd
import boto3
import os
from io import StringIO
from tempfile import mkdtemp

load_dotenv()
MoneyFacts_User = os.getenv("MF_username")

def get_secret():

    """
    Retrieves secrets from AWS secret manager, correct policies must be created for this to run properly
    
    Returns:
        database_secrets['PassWord']: Password for MoneyFacts
    """

    secret_name = "MoneyFactsLogin"
    region_name = "eu-west-2"
    
    client = boto3.client('secretsmanager',
        region_name=region_name )

    response = client.get_secret_value(
        SecretId=secret_name
    )

    database_secrets = json.loads(response['SecretString'])

    return database_secrets['PassWord']

def Opening_Browser():
    """
    Browser is opened by the Lambda Function
    
    Returns:
        Global driver: is returned globally so that every function can utilise to navigate the web
    """
    global driver
    
    load_dotenv()
    start_time = time.time()
    chrome_options = Options()
    chrome_options.binary_location = '/opt/chrome/chrome'
    chrome_options.add_argument("--kiosk")
    chrome_options.add_argument('--headless')
    chrome_options.add_argument('--no-sandbox')
    chrome_options.add_argument("--disable-gpu")
    chrome_options.add_argument("window-size=2560x1504.5")
    chrome_options.add_argument("--single-process")
    chrome_options.add_argument("--disable-dev-shm-usage")
    chrome_options.add_argument("--disable-dev-tools")
    chrome_options.add_argument("--no-zygote")
    chrome_options.add_argument(f"--user-data-dir={mkdtemp()}")
    chrome_options.add_argument(f"--data-path={mkdtemp()}")
    chrome_options.add_argument(f"--disk-cache-dir={mkdtemp()}")
    chrome_options.add_argument("--remote-debugging-port=9222")
    
    driver = webdriver.Chrome("/opt/chromedriver", chrome_options=chrome_options)


    # Open the website
    driver.get('https://analyser.moneyfacts.co.uk/forms/frmLogin.aspx')

def loggin_in():
    """
    Function used for logging into Money Facts
    
    Returns:
        None
    """
    # Load credentials from json file
    
    # Select the username box
    id_box = driver.find_element(By.NAME, 'ctl00$body$txtUsername')
    # Select the password box
    id_box = driver.find_element(By.NAME ,'ctl00$body$txtPassword')
    # Send password information
    id_box.send_keys(get_secret())
    # Find login button
    login_button = driver.find_element(By.NAME, 'ctl00$body$btnSignIn')
    # Click login
    login_button.click()

def navigate_to_reports():
    """
    Function used to navigate to reports on MoneyFacts Portal
    
    Returns:
        None
    """
    wait = WebDriverWait(driver, 10)
    #Navigating to required reports
    class_select = driver.find_elements(By.LINK_TEXT,'OPEN ANALYSER')[1]
    
    class_select.click()

    class_select = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, 'Reports')))

    class_select.click()

    # Wait for the Archived Results link to be clickable and then click it
    class_select = wait.until(EC.element_to_be_clickable((By.LINK_TEXT, 'Archived Results')))
    class_select.click()

    #Click the Peers file button

    try:
        driver.find_element(By.XPATH, "/html/body/div/div/div[2]/div/div[2]/div/div[2]/ul/li[5]/span[2]").click()
        
    except:
        print('could not find peers file') 


def download_history():
    """
    Function used to download history of different product reports
    
    Returns:
        global variable: data_scrape -> table of products offers
    """
    
    global data_scrape

    class_select = driver.find_elements(By.CLASS_NAME, 'btn-group')[2]

    class_select.click()
    
    class_select = driver.find_element(By.LINK_TEXT, 'View Report')
    driver.execute_script("arguments[0].click();", class_select)

    
    class_select = driver.find_element(By.LINK_TEXT, 'Grid View')
    driver.execute_script("arguments[0].click();", class_select)

    driver.execute_script("window.scrollTo(0, 500);")
    ###############################################################################################################################################
    num_rows = len(driver.find_elements(By.XPATH, "/html/body/div/div/div[2]/div[2]/div/div/div[5]/table/tbody/tr"))
    num_columns = len(driver.find_elements(By.XPATH, "/html/body/div/div/div[2]/div[2]/div/div/div[5]/table/tbody/tr[2]/td"))

    #Table cut in half must scrape in two
    before_XPath = "/html/body/div/div/div[2]/div[2]/div/div/div[4]/table/tbody/tr["
    aftertd_XPath = "]/td["
    aftertr_xpath = "]"
    before_XPath_section2 = "/html/body/div/div/div[2]/div[2]/div/div/div[5]/table/tbody/tr["

    data_scrape = pd.DataFrame()
    action = ActionChains(driver)
    for t_row in range(1, (num_rows + 1)):
        if t_row % 14 == 0:
            driver.find_element(By.XPATH, before_XPath_section2 + str(t_row) + aftertd_XPath + str(6) + aftertr_xpath).click()
            action.send_keys(Keys.SPACE).perform()
        FinalXPath = before_XPath + str(t_row) + aftertd_XPath + str(3) + aftertr_xpath
        try:
            cell_text = driver.find_element(By.XPATH, FinalXPath).text
            data_scrape.at[t_row, 2] = cell_text
            
            
        except:
            data_scrape.at[t_row, 2] = 'Not Found'
    
    for t_row in range(1, (num_rows + 1)):
        for t_col in range(4, (num_columns + 1)):
            FinalXPath = before_XPath_section2 + str(t_row) + aftertd_XPath + str(t_col) + aftertr_xpath
            try:
                cell_text = driver.find_element(By.XPATH, FinalXPath).text
                data_scrape.at[t_row, t_col] = cell_text
            except:
                data_scrape.at[t_row, t_col] = 'Not Found'
    
    data_scrape = data_scrape.reset_index()
    time.sleep(2)

    class_select = driver.find_element(By.LINK_TEXT,'Reports')

    class_select.click()

    class_select = driver.find_element(By.LINK_TEXT,'Archived Results')

    class_select.click()


    try:
        time.sleep(2)
        driver.find_element(By.XPATH, "/html/body/div/div/div[2]/div/div[2]/div/div[2]/ul/li[5]/span[2]").click()
        print('Done2')
        time.sleep(2)
    except:
        print('could not find peers file 2') 
        

def one_year_report():
    """
    Function used to navigate to 1 year report
    
    Returns:
        global variable: round -> to specify product in other functions
    """
    
    global round
    round = 1

    try:
        driver.find_element(By.XPATH, "/html/body/div/div/div[2]/div/div[2]/div/div[2]/ul/li[6]").click()
        #scroll to see Export to Excel
    except:
        print('could not find xpath for 1 Year')
        

    driver.execute_script("window.scrollTo(0, 500)")

def eighteen_month_report():
    """
    Function used to navigate to 18 month report
    
    Returns:
        global variable: round -> to specify product in other functions
    """
    
    global round
    round = 18

    try:
        driver.find_element(By.XPATH, "/html/body/div/div/div[2]/div/div[2]/div/div[2]/ul/li[8]").click()
        #scroll to see Export to Excel
    except:
        print('could not find xpath for 18 month')
        

    driver.execute_script("window.scrollTo(0, 500)") 

def two_year_report():
    """
    Function used to navigate to 2 year report
    
    Returns:
        global variable: round -> to specify product in other functions
    """
    
    global round
    round = 2

    try:
        driver.find_element(By.XPATH, "/html/body/div/div/div[2]/div/div[2]/div/div[2]/ul/li[10]").click()
        #scroll to see Export to Excel
    except:
        print('could not find xpath for 2 Year')
        

    driver.execute_script("window.scrollTo(0, 500)") 

def three_year_report():
    """
    Function used to navigate to 3 year report
    
    Returns:
        global variable: round -> to specify product in other functions
    """
    
    global round
    round = 3

    try:
        driver.find_element(By.XPATH, "/html/body/div/div/div[2]/div/div[2]/div/div[2]/ul/li[11]").click()
        #scroll to see Export to Excel
    except:
        print('could not find xpath for 3 Year')
        

    driver.execute_script("window.scrollTo(0, 500)") 

def four_year_report():
    """
    Function used to navigate to 4 Year All Competitors report
    
    Returns:
        global variable: round -> to specify product in other functions
    """
    
    global round
    round = 4
    try:
        class_select = driver.find_element(By.XPATH, "/html/body/div/div/div[2]/div/div[2]/div/div[2]/ul/li[12]")
        driver.execute_script("arguments[0].click();", class_select)
        driver.implicitly_wait(3)
    except:
        print('could not find xpath for 4 Year All Competitors')
        

    driver.execute_script("window.scrollTo(0, 500)")

def six_month_report():
    """
    Function used to navigate to 6 month report
    
    Returns:
        global variable: round -> to specify product in other functions
    """
    
    global round
    round = 6

    try:
        class_select = driver.find_element(By.XPATH, "/html/body/div/div/div[2]/div/div[2]/div/div[2]/ul/li[15]")   
        driver.execute_script("arguments[0].click();", class_select)
        driver.implicitly_wait(3)
    except:
        print('could not find xpath for 6 Month')
        

    driver.execute_script("window.scrollTo(0, 500)") 

def five_year_report():
    """
    Function used to navigate to 5 year report
    
    Returns:
        global variable: round -> to specify product in other functions
    """
    
    global round
    round = 5

    try:
        class_select = driver.find_element(By.XPATH, "/html/body/div/div/div[2]/div/div[2]/div/div[2]/ul/li[14]")   
        driver.execute_script("arguments[0].click();", class_select)
        driver.implicitly_wait(3)
    except:
        print('could not find xpath for 5 Year')
        
         

    driver.execute_script("window.scrollTo(0, 500)") 

def ninetyfive_day_report():
    """
    Function used to navigate to 95 day report
    
    Returns:
        global variable: round -> to specify product in other functions
    """

    global round
    round = 95

    try:
        class_select = driver.find_element(By.XPATH, "/html/body/div/div/div[2]/div/div[2]/div/div[2]/ul/li[17]")
        driver.execute_script("arguments[0].click();", class_select)
        driver.implicitly_wait(3)
    except:
        print('could not find xpath 95Day')

    driver.execute_script("window.scrollTo(0, 500)") 

def fourtyfive_day_report():
    """
    Function used to navigate to 45 day report
    
    Returns:
        global variable: round -> to specify product in other functions
    """

    global round
    round = 45

    try:
        class_select = driver.find_element(By.XPATH, "/html/body/div/div/div[2]/div/div[2]/div/div[2]/ul/li[13]") 
        driver.execute_script("arguments[0].click();", class_select)
        driver.implicitly_wait(3)

    except:
        print('could not find xpath 45Day')
    

    driver.execute_script("window.scrollTo(0, 500)") 

def one_twenty_five_day_notice_report():
    """
    Function used to navigate to 125 Day Notice All Competitors report
    
    Returns:
        global variable: round -> to specify product in other functions
    """
    
    global round
    round = 125
    try:
        class_select = driver.find_element(By.XPATH, "/html/body/div/div/div[2]/div/div[2]/div/div[2]/ul/li[7]")
        driver.execute_script("arguments[0].click();", class_select)
        driver.implicitly_wait(3)
    except:
        print('could not find xpath for 125 Day Notice All Competitors')
        

    driver.execute_script("window.scrollTo(0, 500)")

def seven_day_notice_report():
    """
    Function used to navigate to 7 Day Notice All Competitors report
    
    Returns:
        global variable: round -> to specify product in other functions
    """
    
    global round
    round = 7
    try:
        class_select = driver.find_element(By.XPATH, "/html/body/div/div/div[2]/div/div[2]/div/div[2]/ul/li[16]")
        driver.execute_script("arguments[0].click();", class_select)
        driver.implicitly_wait(3)
    except:
        print('could not find xpath for 7 Day Notice All Competitors')
        

    driver.execute_script("window.scrollTo(0, 500)")

def onehundered_eighty_day_notice_report():
    """
    Function used to navigate to 180 Day Notice All Competitors report
    
    Returns:
        global variable: round -> to specify product in other functions
    """
    
    global round
    round = 180
    try:
        class_select = driver.find_element(By.XPATH, "/html/body/div/div/div[2]/div/div[2]/div/div[2]/ul/li[9]")
        driver.execute_script("arguments[0].click();", class_select)
        driver.implicitly_wait(3)
    except:
        print('could not find xpath for 180 Day Notice All Competitors')
        

    driver.execute_script("window.scrollTo(0, 500)")

def easy_access_report():
    """
    Function used to navigate to Easy Access All Competitors report
    
    Returns:
        global variable: round -> to specify product in other functions
    """
    
    global round
    round = 0
    try:
        class_select = driver.find_element(By.XPATH, "/html/body/div/div/div[2]/div/div[2]/div/div[2]/ul/li[21]")
        driver.execute_script("arguments[0].click();", class_select)
        driver.implicitly_wait(3)
    except:
        print('could not find xpath for Easy Access All Competitors')


def pull_S3_files():
    """
    Function used to pull data from S3 for each product
    Returns:
        global variable: dfTable -> opened table from S3

    """
    
    global dfTable

    if round == 45:
        product = '45day'
    elif round == 95:
        product = '95day'
    elif round == 18:
        product = '18month'
    elif round == 1:
        product = '1year'
    elif round == 6:
        product = '6month'
    elif round == 2:
        product = '2year'
    elif round == 3:
        product = '3year'
    elif round == 4:
        product = '4year'
    elif round == 5:
        product = '5year'
    elif round == 7:
        product = '7day'
    elif round == 180:
        product = '180day'
    elif round == 0:  # Handling easy access products
        product = 'easyaccess'
    else:
        product = '125day'

    table_name = product + 'history'


    # Load credentials from json file

    bucket_name = os.getenv('AWS_BUCKET')
    object_key_table = 'SavingsMarketOverview-Scraper/' + table_name + '.csv'
    

    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=bucket_name, Key=object_key_table)
    data_tables = obj['Body']
    csv_string_table = data_tables.read().decode('utf-8')


    dfTable = pd.read_csv(StringIO(csv_string_table))

    
def push_S3_files(dfHistory_final):
    """
    Function used to push data from S3 for each product
    Args:
        dfHistory_final: table to push back to S3 for a given product

    """
    if round == 45:
        product = '45day'
    elif round == 95:
        product = '95day'
    elif round == 18:
        product = '18month'
    elif round == 1:
        product = '1year'
    elif round == 6:
        product = '6month'
    elif round == 2:
        product = '2year'
    elif round == 3:
        product = '3year'
    elif round == 4:
        product = '4year'
    elif round == 5:
        product = '5year'
    elif round == 7:
        product = '7day'
    elif round == 180:
        product = '180day'
    elif round == 0:  # Handling easy access products
        product = 'easyaccess'
    else:
        product = '125day'
    
    table_name = 'SavingsMarketOverview-Scraper/' + product + 'history'
     
    
    dict_dataframes = {table_name:dfHistory_final}
    # Load credentials from json file

    bucket_name = os.getenv('AWS_BUCKET')
    
    for name, df in dict_dataframes.items():
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index = False)
        s3_resource = boto3.resource('s3')
        s3_resource.Object(bucket_name, name + '.csv').put(Body=csv_buffer.getvalue())

def filter_data_by_term(data, min_term, max_term):
    """
    Filter the data based on term days within a specified range.
    Args:
        data: DataFrame to be filtered.
        min_term: Minimum term days.
        max_term: Maximum term days.
    Returns:
        Filtered DataFrame.
    """
    data.iloc[:, 6] = data.iloc[:, 6].replace('-', -1).astype(int)

    # Perform the filtering, including rows where notice days is -1 (easy access)
    filtered_data = data[(data.iloc[:, 6] >= min_term) & (data.iloc[:, 6] <= max_term) | (data.iloc[:, 6] == -1)]
    return filtered_data.reset_index(drop=True)

def clean_workbooks(round, dfTable, data_scrape):
    """
    Functions used to clean the scraped table and concat to original table
    Args:
        round: Keeps track of what product we are on
        dfTable: final data for the scraped table that is concatenatedd to S3 table
        data_scrape: raw data scraped from online table
    """
    global dfHistory_final
    todays_date = datetime.datetime.today().strftime('%d/%m/%Y')

    # Filter the data based on the round
    if round == 45:
        data_scrape = filter_data_by_term(data_scrape, 30, 45)
    elif round == 7:
        data_scrape = filter_data_by_term(data_scrape, 2, 7)
    elif round == 125:
        data_scrape = filter_data_by_term(data_scrape, 100, 125)
    elif round == 180:
        data_scrape = filter_data_by_term(data_scrape, 175, 185)
    elif round == 0:
        pass

    # Adding today's date
    data_scrape['date'] = todays_date

    # Deleting duplicates
    unique_banks = set()
    g = 0
    while g < len(data_scrape):
        bank_name = data_scrape.iloc[g, 1]
        if bank_name in unique_banks:
            data_scrape = data_scrape.drop(g, axis=0)
            data_scrape = data_scrape.reset_index(drop=True)
        else:
            unique_banks.add(bank_name)
            g += 1


    if round == 45:
        data_scrape = data_scrape.rename(columns={
            2: 'Bank Name', 4: 'Account', 5: 'Account Type', 6: 'as_of_date', 7: 'Term', 8: 'Term Days', 9: 'AER'})
    elif round == 95:
        data_scrape = data_scrape.rename(columns={
            2: 'Bank Name', 4: 'Account', 5: 'Account Type', 6: 'as_of_date',7: 'Term', 8: 'Term Days', 9: 'AER'})
    elif round == 125:
        data_scrape = data_scrape.rename(columns={
            2: 'Bank Name', 4: 'Account', 5: 'Account Type', 6: 'as_of_date',7: 'Term', 8: 'Term Days', 9: 'AER'})
    elif round == 180:
        data_scrape = data_scrape.rename(columns={
            2: 'Bank Name', 4: 'Account', 5: 'Account Type', 6: 'as_of_date', 7: 'Notice', 8: 'Notice (Days)', 9: 'AER'})
    elif round == 7:
        data_scrape = data_scrape.rename(columns={
            2: 'Bank Name', 4: 'Account', 5: 'Account Type', 6: 'Wef Date', 7: 'Notice', 8: 'Notice (Days)', 9: 'AER'})
    elif round == 0:  # Easy access products
        data_scrape = data_scrape.rename(columns={
            2: 'Bank Name', 4: 'Account', 5: 'Account Type', 6: 'Wef Date', 7: 'Notice', 8: 'Notice (Days)', 9: 'AER'})
    elif round == 18:
        data_scrape = data_scrape.rename(columns={
            2: 'Bank Name', 4: 'Account', 5: 'Account Type', 6: 'AER',7: 'Term', 8: 'Term Days'})
    elif round == 1:
        data_scrape = data_scrape.rename(columns={
            2: 'Bank Name', 4: 'Account', 5: 'Account Type', 6: 'AER',7: 'Term', 8: 'Term Days'})
    elif round == 6:
        data_scrape = data_scrape.rename(columns={
            2: 'Bank Name', 4: 'Account', 5: 'Account Type', 6: 'AER',7: 'Term', 8: 'Term Days'})
    elif round == 2:
        data_scrape = data_scrape.rename(columns={
            2: 'Bank Name', 4: 'Account', 5: 'Account Type', 6: 'AER',7: 'Term', 8: 'Term Days'})
    elif round == 3:
        data_scrape = data_scrape.rename(columns={
            2: 'Bank Name', 4: 'Account', 5: 'Account Type', 6: 'AER',7: 'Term', 8: 'Term Days'})
    elif round == 4:
        data_scrape = data_scrape.rename(columns={
            2: 'Bank Name', 4: 'Account', 5: 'Account Type', 6: 'AER',7: 'Term', 8: 'Term Days'})
    elif round == 5:
        data_scrape = data_scrape.rename(columns={
            2: 'Bank Name', 4: 'Account', 5: 'Account Type', 6: 'AER',7: 'Term', 8: 'Term Days'})
    else:
        # Default renaming if round is not explicitly handled
        data_scrape = data_scrape.rename(columns={
            2: 'Bank Name', 4: 'Account', 5: 'Account Type', 6: 'AER',7: 'Term', 8: 'Term Days'})

    # Ensure we have the correct columns
    expected_columns = ['Bank Name', 'AER', 'Account Type', 'date']
    for col in expected_columns:
        if col not in data_scrape.columns:
            print(f"Missing expected column: {col} in round {round}")
            return

    # Selecting and renaming columns for bank_data
    bank_data = data_scrape[['Bank Name', 'AER', 'Account Type', 'date']]
    bank_data = bank_data.rename(columns={
        'Bank Name': 'Name', 'AER': 'Rate', 'Account Type': 'Product', 'date': 'Date'})
    bank_data['Rank'] = range(1, len(bank_data) + 1)


    # Concatenating to final DataFrame
    dfHistory_final = pd.concat([dfTable, bank_data], axis=0, ignore_index=True)
    return dfHistory_final

    
def log_out():
    """
    Log_out function is used to log out of Money Facts - if you do not log out it will not allow you to log in the following time
    """
    
    class_select = driver.find_element(By.LINK_TEXT, 'Back to Portal')

    class_select.click()

    class_select = driver.find_element(By.LINK_TEXT,'Logout')

    class_select.click()

    driver.quit()

def handler(event = None, context = None):
    
    try:

        Opening_Browser()
        loggin_in()
        navigate_to_reports()
        one_year_report()
        download_history()
        pull_S3_files()
        clean_workbooks(round, dfTable, data_scrape)
        push_S3_files(dfHistory_final)
        one_twenty_five_day_notice_report()
        download_history()
        pull_S3_files()
        clean_workbooks(round, dfTable, data_scrape)
        push_S3_files(dfHistory_final)
        seven_day_notice_report()
        download_history()
        pull_S3_files()
        clean_workbooks(round, dfTable, data_scrape)
        push_S3_files(dfHistory_final)
        onehundered_eighty_day_notice_report()
        download_history()
        pull_S3_files()
        clean_workbooks(round, dfTable, data_scrape)
        push_S3_files(dfHistory_final)
        four_year_report()
        download_history()
        pull_S3_files()
        clean_workbooks(round, dfTable, data_scrape)
        push_S3_files(dfHistory_final)
        easy_access_report()
        download_history()
        pull_S3_files()
        clean_workbooks(round, dfTable, data_scrape)
        push_S3_files(dfHistory_final)
        five_year_report()
        download_history()
        pull_S3_files()
        clean_workbooks(round, dfTable, data_scrape)
        push_S3_files(dfHistory_final)
        ninetyfive_day_report()
        download_history()
        pull_S3_files()
        clean_workbooks(round, dfTable, data_scrape)
        push_S3_files(dfHistory_final)
        fourtyfive_day_report()
        download_history()
        pull_S3_files()
        clean_workbooks(round, dfTable, data_scrape)
        push_S3_files(dfHistory_final)
        two_year_report()
        download_history()
        pull_S3_files()
        clean_workbooks(round, dfTable, data_scrape)
        push_S3_files(dfHistory_final)
        six_month_report()
        download_history()
        pull_S3_files()
        clean_workbooks(round, dfTable, data_scrape)
        push_S3_files(dfHistory_final)
        eighteen_month_report()
        download_history()
        pull_S3_files()
        clean_workbooks(round, dfTable, data_scrape)
        push_S3_files(dfHistory_final)
        three_year_report()
        download_history()
        pull_S3_files()
        clean_workbooks(round, dfTable, data_scrape)
        push_S3_files(dfHistory_final)
        log_out()
    except Exception as e:
        print(e)
        log_out()
        print("Logged out of MoneyFacts")
        raise e
