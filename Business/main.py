import selenium 
from dotenv import load_dotenv
from selenium import webdriver
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, NoSuchElementException
import time
from selenium.webdriver.chrome.options import Options
import json
import datetime
from datetime import timedelta
from datetime import date
import pandas as pd
import os
from io import StringIO
import boto3
from tempfile import mkdtemp

load_dotenv()
MoneyFacts_User = os.getenv("MF_username")
def get_secret():

    """
    Retrieves secrets from AWS secret manager, correct policies must be created for this to run properly
    
    Returns:
        Password for MoneyFacts
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
    Opening_Browser()
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
    Function used to navigate to reports on MoneyFacts login
    
    Returns:
        None
    """
    loggin_in()

    #Navigating to required reports
    class_select = driver.find_elements(By.LINK_TEXT, 'OPEN ANALYSER')[2]

    class_select.click()

    class_select = driver.find_element(By.LINK_TEXT, 'Reports')

    class_select.click()

    class_select = driver.find_element(By.LINK_TEXT, 'Archived Results')

    class_select.click()

    #Click the Peers file button

    try:
        driver.find_element(By.XPATH, "/html/body/div/div/div[2]/div/div[2]/div/div[2]/ul/li[5]/span[2]").click()
    except:
        print('could not find peers file')

def business_report():
    """
    Function used to navigate to the business reports
    
    Returns:
        None
    """

    navigate_to_reports()
    try:
        driver.find_element(By.XPATH, "/html/body/div/div/div[2]/div/div[2]/div/div[2]/ul/li[6]").click()
        #scroll to see Export to Excel
    except:
        print('could not find xpath for 1 Year')
        
    driver.execute_script("window.scrollTo(0, 500)")

def download_history():
    """
    Function used to scrape online table of banks rates used for all products
    
    Returns:
        data_scrape: table of scraped data
    """
    

    business_report()

    class_select = driver.find_elements(By.CLASS_NAME, 'btn-group')[2]
    class_select.click()
    
    class_select = driver.find_element(By.LINK_TEXT, 'View Report')
    driver.execute_script("arguments[0].click();", class_select)

    class_select = driver.find_element(By.LINK_TEXT, 'Grid View')
    driver.execute_script("arguments[0].click();", class_select)

    driver.execute_script("window.scrollTo(0, 500);")
    num_rows = len(driver.find_elements(By.XPATH, "/html/body/div/div/div[2]/div[2]/div/div/div[5]/table/tbody/tr"))
    num_columns = len(driver.find_elements(By.XPATH, "/html/body/div/div/div[2]/div[2]/div/div/div[5]/table/tbody/tr[2]/td"))

    # Table cut in half must scrape in two
    before_XPath = "/html/body/div/div/div[2]/div[2]/div/div/div[4]/table/tbody/tr["
    aftertd_XPath = "]/td["
    aftertr_xpath = "]"
    before_XPath_section2 = "/html/body/div/div/div[2]/div[2]/div/div/div[5]/table/tbody/tr["

    data_scrape = pd.DataFrame()
    action = ActionChains(driver)
    t_row = 1
    number_pages = 2
    number_of_pages = len(driver.find_elements(By.XPATH, "/html/body/div/div/div[2]/div[2]/div/div/div/ul/li"))
    
    
    while t_row <= num_rows:
        # if number_pages > number_of_pages:
        #     break
        FinalXPath = before_XPath + str(t_row) + aftertd_XPath + str(3) + aftertr_xpath
        try:
            cell_text = driver.find_element(By.XPATH, FinalXPath).text
            data_scrape.at[t_row + ((number_pages - 2)* 150), 2] = cell_text
         
        except:
            data_scrape.at[t_row + ((number_pages-2) * 150), 2] = 'Not Found'

        for t_col in [5, 6, 7, 8, 15]:
            FinalXPath = before_XPath_section2 + str(t_row) + aftertd_XPath + str(t_col) + aftertr_xpath
            try:
                cell_text = driver.find_element(By.XPATH, FinalXPath).text
                data_scrape.at[t_row + ((number_pages-2) * 150), t_col] = cell_text
               
            except:
                data_scrape.at[t_row + ((number_pages-2)* 150), t_col] = 'Not Found'

        if t_row % 14 == 0:
            driver.find_element(By.XPATH, before_XPath_section2 + str(t_row) + aftertd_XPath + str(6) + aftertr_xpath).click()
            action.send_keys(Keys.SPACE).perform()
        
        if t_row == num_rows:
                if number_pages <= number_of_pages:
                    driver.find_element(By.XPATH, "/html/body/div/div/div[2]/div[2]/div/div/div/ul/li[" + str(number_pages) + "]/a").click()
                    t_row = 0
                number_pages += 1
                time.sleep(2)
                num_rows = len(driver.find_elements(By.XPATH, "/html/body/div/div/div[2]/div[2]/div/div/div[5]/table/tbody/tr"))
                
        
        t_row +=1
    time.sleep(2)

    return data_scrape

def clean_sheet():
    """
    Function used to clean scraped data
    
    Returns:
        df_1year, df_2year, df_5year, df_95day, df_ea, df_6month: table of scraped data is broken down further into different products
    """

    df_1year, df_2year, df_3year, df_5year, df_7day, df_35day, df_95day, df_ea, df_6month, df_120day, df_180day = opening_files()

    data = download_history()
    

    data = data.rename(columns = {2: 'Bank Name', 8:'Account', 6: 'Notice', 7: 'Notice Days', 15: 'AER', 5: 'As_Of_Date'}) ### Account column is actually Term column on Moneyfacts reports :(
    data_ea = pd.DataFrame(columns = ['Rank', 'Name', 'Rate', 'Product', 'Date'])
    data_7 = pd.DataFrame(columns = ['Rank', 'Name', 'Rate', 'Product', 'Date'])
    data_35 = pd.DataFrame(columns = ['Rank', 'Name', 'Rate', 'Product', 'Date'])
    data_95 = pd.DataFrame(columns = ['Rank', 'Name', 'Rate', 'Product', 'Date'])
    data_1 = pd.DataFrame(columns = ['Rank', 'Name', 'Rate', 'Product', 'Date'])
    data_2 = pd.DataFrame(columns = ['Rank', 'Name', 'Rate', 'Product', 'Date'])
    data_3 = pd.DataFrame(columns = ['Rank', 'Name', 'Rate', 'Product', 'Date'])
    data_5 = pd.DataFrame(columns = ['Rank', 'Name', 'Rate', 'Product', 'Date'])
    data_6 = pd.DataFrame(columns = ['Rank', 'Name', 'Rate', 'Product', 'Date'])
    data_120 = pd.DataFrame(columns = ['Rank', 'Name', 'Rate', 'Product', 'Date'])
    data_180 = pd.DataFrame(columns = ['Rank', 'Name', 'Rate', 'Product', 'Date'])

    data_ea_row = 1
    data_7_row = 1 
    data_35_row = 1
    data_1_row = 1
    data_2_row = 1
    data_3_row = 1
    data_5_row = 1
    data_95_row = 1
    data_6_row = 1
    data_120_row = 1
    data_180_row = 1
    date = datetime.date.today()
    

    for i in range(1, len(data) + 1):
       
        if data.at[i, 'Account'] == '1 Year Bond' or data.at[i, 'Account'] == '12 Month Bond':
            data_1.at[data_1_row, 'Rank'] = data_1_row
            data_1.at[data_1_row, 'Name'] = data.at[i, 'Bank Name']
            data_1.at[data_1_row, 'Rate'] = data.at[i, 'AER']
            data_1.at[data_1_row, 'Product'] = data.at[i, 'Account']
            data_1.at[data_1_row, 'Date'] = date
            
            data_1_row += 1

        elif data.at[i, 'Account'] == '5 Year Bond' or data.at[i, 'Account'] == '60 Month Bond':
            data_5.at[data_5_row, 'Rank'] = data_5_row
            data_5.at[data_5_row, 'Name'] = data.at[i, 'Bank Name']
            data_5.at[data_5_row, 'Rate'] = data.at[i, 'AER']
            data_5.at[data_5_row, 'Product'] = data.at[i, 'Account']
            data_5.at[data_5_row, 'Date'] = date

            data_5_row += 1

        elif data.at[i, 'Account'] == '2 Year Bond' or data.at[i, 'Account'] == '24 Month Bond':
            data_2.at[data_2_row, 'Rank'] = data_2_row
            data_2.at[data_2_row, 'Name'] = data.at[i, 'Bank Name']
            data_2.at[data_2_row, 'Rate'] = data.at[i, 'AER']
            data_2.at[data_2_row, 'Product'] = data.at[i, 'Account']
            data_2.at[data_2_row, 'Date'] = date

            data_2_row += 1
        
        elif data.at[i, 'Account'] in ('3 Year Bond', '36 Month Bond') or '3 Year' in data.at[i, 'Account'] or '3 year' in data.at[i, 'Account']:
            
            data_3.at[data_3_row, 'Rank'] = data_3_row
            data_3.at[data_3_row, 'Name'] = data.at[i, 'Bank Name']
            data_3.at[data_3_row, 'Rate'] = data.at[i, 'AER']
            data_3.at[data_3_row, 'Product'] = data.at[i, 'Account']
            data_3.at[data_3_row, 'Date'] = date

            data_3_row += 1

        elif data.at[i, 'Notice Days'] == '5' or data.at[i, 'Notice Days'] == '7' or data.at[i, 'Notice Days'] == '12':
            data_7.at[data_7_row, 'Rank'] = data_7_row
            data_7.at[data_7_row, 'Name'] = data.at[i, 'Bank Name']
            data_7.at[data_7_row, 'Rate'] = data.at[i, 'AER']
            data_7.at[data_7_row, 'Product'] = data.at[i, 'Account']
            data_7.at[data_7_row, 'Date'] = date

            data_7_row += 1
        
        elif data.at[i, 'Notice Days'] == '30' or data.at[i, 'Notice Days'] == '35' or data.at[i, 'Notice Days'] == '40':
            data_35.at[data_35_row, 'Rank'] = data_35_row
            data_35.at[data_35_row, 'Name'] = data.at[i, 'Bank Name']
            data_35.at[data_35_row, 'Rate'] = data.at[i, 'AER']
            data_35.at[data_35_row, 'Product'] = data.at[i, 'Account']
            data_35.at[data_35_row, 'Date'] = date

            data_35_row += 1 


        elif data.at[i, 'Notice Days'] == '90' or data.at[i, 'Notice Days'] == '95' or data.at[i, 'Notice Days'] == '100':
            data_95.at[data_95_row, 'Rank'] = data_95_row
            data_95.at[data_95_row, 'Name'] = data.at[i, 'Bank Name']
            data_95.at[data_95_row, 'Rate'] = data.at[i, 'AER']
            data_95.at[data_95_row, 'Product'] = data.at[i, 'Account']
            data_95.at[data_95_row, 'Date'] = date

            data_95_row += 1

        elif data.at[i, 'Notice Days'] == '100' or data.at[i, 'Notice Days'] == '120' or data.at[i, 'Notice Days'] == '130':
            data_120.at[data_120_row, 'Rank'] = data_120_row
            data_120.at[data_120_row, 'Name'] = data.at[i, 'Bank Name']
            data_120.at[data_120_row, 'Rate'] = data.at[i, 'AER']
            data_120.at[data_120_row, 'Product'] = data.at[i, 'Account']
            data_120.at[data_120_row, 'Date'] = date

            data_120_row += 1 
        
        elif data.at[i, 'Notice Days'] == '160' or data.at[i, 'Notice Days'] == '180' or data.at[i, 'Notice Days'] == '190':
            data_180.at[data_180_row, 'Rank'] = data_180_row
            data_180.at[data_180_row, 'Name'] = data.at[i, 'Bank Name']
            data_180.at[data_180_row, 'Rate'] = data.at[i, 'AER']
            data_180.at[data_180_row, 'Product'] = data.at[i, 'Account']
            data_180.at[data_180_row, 'Date'] = date

            data_180_row += 1
        
        

        elif data.at[i, 'Notice'] == 'Instant' or data.at[i, 'Notice'] == 'None':
            data_ea.at[data_ea_row, 'Rank'] = data_ea_row
            data_ea.at[data_ea_row, 'Name'] = data.at[i, 'Bank Name']
            data_ea.at[data_ea_row, 'Rate'] = data.at[i, 'AER']
            data_ea.at[data_ea_row, 'Product'] = data.at[i, 'Account']
            data_ea.at[data_ea_row, 'Date'] = date

            data_ea_row += 1

        elif data.at[i, 'Account'] == '6 Month Bond':
            data_6.at[data_6_row, 'Rank'] = data_6_row
            data_6.at[data_6_row, 'Name'] = data.at[i, 'Bank Name']
            data_6.at[data_6_row, 'Rate'] = data.at[i, 'AER']
            data_6.at[data_6_row, 'Product'] = data.at[i, 'Account']
            data_6.at[data_6_row, 'Date'] = date

            data_6_row += 1

        
    
    data_frame = [data_1, data_2, data_3, data_5, data_7, data_35, data_95, data_ea, data_6, data_120, data_180]
    df_index = 0
   

    for df_clean in data_frame:
        
        # Identify duplicates and keep the first occurrence
        duplicates = df_clean.duplicated(subset='Name', keep='first')
        
        # Drop duplicate rows
        df_clean = df_clean[~duplicates].reset_index(drop=True)
        
        # Remove rows with invalid rates
        df_clean = df_clean[df_clean['Rate'] != '-']
        
        # Update the rank
        df_clean['Rank'] = range(1, len(df_clean) + 1)
        
        data_frame[df_index] = df_clean
       
        df_index += 1
    

        

    df_1year = pd.concat([df_1year, data_frame[0] ], axis = 0, ignore_index = True)
    df_2year = pd.concat([df_2year, data_frame[1]], axis = 0, ignore_index = True)
    df_3year = pd.concat([df_3year, data_frame[2]], axis = 0, ignore_index = True)
    df_5year = pd.concat([df_5year, data_frame[3]], axis = 0, ignore_index = True)
    df_7day = pd.concat([df_7day, data_frame[4]], axis = 0, ignore_index = True)
    df_35day = pd.concat([df_35day, data_frame[5]], axis = 0, ignore_index = True)
    df_95day = pd.concat([df_95day, data_frame[6]], axis = 0, ignore_index = True)
    df_ea = pd.concat([df_ea, data_frame[7]], axis = 0, ignore_index = True)
    df_6month = pd.concat([df_6month, data_frame[8]], axis = 0, ignore_index = True)
    df_120day = pd.concat([df_120day, data_frame[9]],axis=0, ignore_index= True)
    df_180day = pd.concat([df_180day, data_frame[10]],axis=0, ignore_index= True)


   
    return df_1year, df_2year, df_3year, df_5year, df_7day, df_35day, df_95day, df_ea, df_6month, df_120day, df_180day

def opening_files():
    """
    Function used open files from S3
    
    Returns:
        df_1year, df_2year, df_5year, df_95day, df_ea, df_6month: files opened from S3 including the historical data for those products
    """

    df_1year = pull_S3_files('1yearhistorybusiness')
    df_2year = pull_S3_files('2yearhistorybusiness')
    df_3year = pull_S3_files('3yearhistorybusiness')
    df_5year = pull_S3_files('5yearhistorybusiness')
    df_7day = pull_S3_files('7dayhistorybusiness')
    df_35day = pull_S3_files('35dayhistorybusiness')
    df_95day = pull_S3_files('95dayhistorybusiness')
    df_ea = pull_S3_files('eahistorybusiness')
    df_6month = pull_S3_files('6monthhistorybusiness')
    df_120day = pull_S3_files('120dayhistorybusiness')
    df_180day =pull_S3_files('180dayhistorybusiness')
    
    return df_1year, df_2year, df_3year, df_5year, df_7day, df_35day, df_95day, df_ea, df_6month, df_120day, df_180day

def pushing_files():
    """
    Function used to clean scraped data
    
    Returns:
        df_1year, df_2year, df_5year, df_95day, df_ea, df_6month: pushing concatenated files with new scraped data into S3
    """
    df_1year, df_2year, df_3year, df_5year, df_7day, df_35day,  df_95day, df_ea, df_6month, df_120day, df_180day = clean_sheet()
    
    push_S3_files(df_1year, '1yearhistorybusiness')
    push_S3_files(df_2year, '2yearhistorybusiness')
    push_S3_files(df_3year, '3yearhistorybusiness')
    push_S3_files(df_5year, '5yearhistorybusiness')
    push_S3_files(df_7day, '7dayhistorybusiness')
    push_S3_files(df_35day, '35dayhistorybusiness')
    push_S3_files(df_95day, '95dayhistorybusiness')
    push_S3_files(df_ea, 'eahistorybusiness')
    push_S3_files(df_6month, '6monthhistorybusiness')
    push_S3_files(df_120day, '120dayhistorybusiness')
    push_S3_files(df_180day, '180dayhistorybusiness')
    
    

def pull_S3_files(table_name):
    """
    Function pull data from S3
    Args:
        table_name: name of table to pull

    """

    # Load credentials from json file

    bucket_name = os.getenv('AWS_BUCKET')
    object_key_table = 'SavingsMarketOverview-Scraper/' + table_name + '.csv'
    

    s3 = boto3.client('s3')
    obj = s3.get_object(Bucket=bucket_name, Key=object_key_table)
    data_tables = obj['Body']
    csv_string_table = data_tables.read().decode('utf-8')


    dfTable = pd.read_csv(StringIO(csv_string_table))

    return dfTable

def push_S3_files(dfHistory_final, table_name):
    """
    Function push data to S3
    Args:
        table_name: name of table to push
        dfHistory_final: data to push

    """
    table_name = 'SavingsMarketOverview-Scraper/' + table_name
     
    
    dict_dataframes = {table_name:dfHistory_final}
    # Load credentials from json file

    bucket_name = os.getenv('AWS_BUCKET')
    
    for name, df in dict_dataframes.items():
        csv_buffer = StringIO()
        df.to_csv(csv_buffer, index = False)
        s3_resource = boto3.resource('s3')
        s3_resource.Object(bucket_name, name + '.csv').put(Body=csv_buffer.getvalue())


def log_out():
    """
    Log_out function is used to log out of Money Facts - if you do not log out it will not allow you to log in the following time
    """
    pushing_files()
    
    class_select = driver.find_element(By.LINK_TEXT, 'Back to Portal')

    class_select.click()

    class_select = driver.find_element(By.LINK_TEXT,'Logout')

    class_select.click()

    driver.quit()


def handler(event = None, context = None):
    try:
        log_out()
    except Exception as e:
        print(e)
        log_out()
        print("Logged out of MoneyFacts")
        raise e
