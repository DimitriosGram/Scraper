# Savings Web Scraper


## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
- [Usage](#usage)
- [Docker Image](#docker-image)
  - [How to create and puch your docker image to a Lambda function and ECR in an automated way](#how-to-create-and-push-your-docker-image-to-a-lambda-function-and-ecr-in-an-automated-way)
- [API Gateway and Lambda Function](#api-gateway-and-lambda-function)
- [Manually Running the Lambdas in Dev](#manually-running-the-lambdas-in-dev)
- [Common Errors](#common-errors)
- [Configuration](#configuration)
- [Adding new products](#adding-new-products)
  - [Business products](#business-products)
  - [Personal products](#personal-products)
- [Deployment](#deployment)
  - [test](#test)
  - [build-and-deploy](#build-and-deploy)
- [Contributing](#contributing)
- [License](#license)

## Overview

This project was developed to automate manual effort done by the savings Team to pull data from MoneyFacts. Further to this it also enhances the process by pulling data over different products for 100+ banks.

## Features
        
- Products: over 20 proudcts being scraped from MoneyFaacts for both Business and Personal products.

- Banks: Over 100 banks being tracked through this excercise on a daily basis.

- Scheduling: Jobs run on a daily basis at 13:15pm and 13:30pm and are scheduled using EventBridge.

- Storage: Scraped data is formatted by Lambda function and storred in S3 bucket. 


## Getting Started

This project includes four components, to fully understand the pipeline you can review these components on the AWS Console

- Lambda Function: Personal (rb-rbcore-depositsoverview-db-changes) runs at 13:30pm and Business (rb-rbcore-market-overview-business) runs at 13:15pm. These functions log on to the Moneyfacts portal at https://analyser.moneyfacts.co.uk/forms/frmLogin.aspx. Once here they interact with Secrets Manager to pull the password for the user Ama5m63, then navigates to the page that includes the products and there reports, and starts scraping these products, formatting the data and storing it in S3. Finally the Lambda functions logs out of the portal as you cannot log into it again if you do not log out of your last session.

- EventBridge: Is used to triger both Lambda functions at the respective times mentioned above. It is important that these functions do not overlap as two concurrent sessions cannot be activate on the Moneyfacts portal.

- S3 Bucket: s3://rb-rbcore/SavingsMarketOverview-Scraper/ stores all product files that will include historical product data. The Lambda function pulls these concats the formatted scraped data and then pushes it back into this S3 location. This S3 Location is versioned thus we can use this feature to view files generated at different dates.


### Prerequisites

To use these Lambda functions a Moneyfacts account needs to be created - in our case we are using the user Ama5m6. The scrapers will not work with any account, prior to running them in a new account the reports that are scraped need to be created on the MoneyFacts portal for each product.

## Usage

If you want to use or test the code locally you can do so by ammending the code slightly. 

<pre>
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

</pre>

Needs to be replaced with -

<pre>
def Opening_Browser():
    """
    Browser is opened by your local machine
    Returns:
        Global driver: is returned globally so that every function can utilise to navigate the web
    """
    global driver

    load_dotenv()

    start_time = time.time()
    # Using Chrome to access web
    #driver = webdriver.Chrome()
    chrome_options = Options()
    chrome_options.add_argument("--kiosk")
    driver = webdriver.Chrome(chrome_options=chrome_options)


    # Open the website
    driver.get('https://analyser.moneyfacts.co.uk/forms/frmLogin.aspx')
</pre>

AWS credentials should be set on local device too so that local runs have access to Secrets Manager and S3 for the files. 

Note: when running locally do not save files generated on S3 but mend code so that files are saved locally.

To run locally you must install the following python libraries:
* selenium
* pandas
* python-dotenv

And the latest chrome-driver must be installed on your local device too.

NOTE: MAKE SURE YOU DO NOT TEST AROUND THE TIME THAT THE PROD FUNCTIONS ARE RUNNING AS THIS MIGHT CAUSE A CONFLICT.

## Docker Image

The docker file used for these lambdas is pretty simple - one thing it must include is a download script for both chrome-driver and chromium. That is why we need the RUN yum install -y line in the docker file. The Lambda function uses this to interact with chrome.

<pre>
FROM public.ecr.aws/lambda/python@sha256:9cc6f47de700608ee0420246dac500edd34d059174ff0f7ea54f5230bda4e537 as build
RUN yum install -y unzip && \
    curl -Lo "/tmp/chromedriver.zip" "https://chromedriver.storage.googleapis.com/105.0.5195.52/chromedriver_linux64.zip" && \
    curl -Lo "/tmp/chrome-linux.zip" "https://www.googleapis.com/download/storage/v1/b/chromium-browser-snapshots/o/Linux_x64%2F1027016%2Fchrome-linux.zip?alt=media" && \
    unzip /tmp/chromedriver.zip -d /opt/ && \
    unzip /tmp/chrome-linux.zip -d /opt/

FROM public.ecr.aws/lambda/python@sha256:9cc6f47de700608ee0420246dac500edd34d059174ff0f7ea54f5230bda4e537
RUN yum install atk cups-libs gtk3 libXcomposite alsa-lib \
    libXcursor libXdamage libXext libXi libXrandr libXScrnSaver \
    libXtst pango at-spi2-atk libXt xorg-x11-server-Xvfb \
    xorg-x11-xauth dbus-glib dbus-glib-devel -y
RUN pip install selenium
RUN pip install pandas
RUN pip install python-dotenv
COPY --from=build /opt/chrome-linux /opt/chrome
COPY --from=build /opt/chromedriver /opt/
COPY main.py ./
CMD [ "main.handler" ]
</pre>

### How to create and push your docker image to a Lambda function and ECR in an automated way.
When working on this project or other projects in the future you realise that creating, tagging and pushing an image to AWS can be a repetative task. So below you will find instructions on how we automated this proccess and how you can follow it:

Before going into the steps, make sure you have your docker desktop up and running if not your image will not be created and the build and deploy operation will fail. More information on how to do that [click here](https://github.com/RecogniseBank-Tech/Lambda-Savings-Aggregator?tab=readme-ov-file#docker-image).

1. Have a .sh file in your project folder. In this case you will see above the document called ```build_and_deploy.sh``` . The contents of the file are located under the scripts folder in this repo ```script/build_and_deploy.sh``` . 
 
  - At the top of the file you have the "Variables" these are the variables that you will need to call in the one command that we will use to create, tag, deploy and attach to our lambda.
  - Next you will see all of the commands you would have used in order to do all of the work mentioned above.

2. First you need to make sure you have created and have an SSO profile. Single sign-on (SSO) is an authentication solution that allows users to log in to multiple applications and websites with one-time user authentication.
   - Configure your sso got to your project path via your cmd and type this command ```aws configure sso``` .
   - Details you will need for the set up are: "https://d-9c6704b420.awsapps.com/start/" and "sso:account:access"
   - Name your profile with a naming convention that is suitable to the AWS account and profile you are wishing to use.
     
3. After you have made sure you have an sso profile its time to start to build our docker image. In your cmd run ```aws sso login --profile <your-profile-name>``` . This will open up an AWS tab on your browser, it will provide you with a code. Make sure it matched the code on your CMD.
4. The final part will be calling your "build_and_deploy.sh" file. Type in your CMD ```../build_and_push.sh <account_id> eu-west-2 <repo_name> <image_tag> <lambda_function_name> <sso_profile>``` .
5. Then go on AWS and check at your Lambda's Image uri. You will see your image with the tag you have given it.

## API Gateway and Lambda Function

![Architecture diagram](./Architecture.png)

1. EventBridge Triggers the Lambda function at a designated time (1:15pm or 1:30pm).

2. Lambda execution logs are captured in CloudWatch.

3. Lambda access the web and executed the workflow to scrape and format data from MoneyFacts Portal.

4. Lambda saves all files into the designated S3 location.

## Manually Running the Lambdas in Dev

As of 03/04/2024 the scrapper exists also in the dev enviroment. The lambdas although dont have EventBridge triggers attached to them, that is to cut down on costs in AWS. 

The Lambdas are manually run in the AWS CLI with the following command: ```aws lambda invoke --function-name <add-your-function-name> response.json```

## Common Errors

Sometimes when running the Lambda you get this error: 
<pre>
  [ERROR] NoSuchElementException: Message: no such element: Unable to locate element: 
{
    "method": "link text",
    "selector": "Reports"
}
</pre>

This can be one of two things:

1. Lambda has not logged out from the MoneyFacts website so the new run is unable to access the reports, that leads to the above error.
2. Now if you have made sure that the last lambda logged out from the MF website and there is no other user that is logged in this will be a server issue and there is nothing you can do from a dev's point of view. Wait 5 minutes and try again. If it persists wait longer. Then test the lambda and run it again.


## Configuration

EventBridge:

Event Bridge is currently configured to trigger the Lambda function one at 13:15 and another at 13:30, this can be configured easily to trigger at any other time. Do not set the executions of the Lambda functions to run concurrently or over run one another this will crash the process as you can only have one login to the portal at once.

Lambda Configuration:

* Memory - 1000 MB
* Ephemeral storage - 1000 MB 
* Timeout - 10 Minutes

## Adding new Products
 Adding new products to the scrapper needs to be done in two seperate steps. 
 1. First step would be to ensure the information about the product you are wishing to add is on Moneyfacts in a report. If not you will have to create a new report on the website.
 2. The second step would be to update the filtering within the code. That being on the Business or Personal sides.
    
### Creating a Moneyfacts report
[Here](https://github.com/RecogniseBank-Tech/rb-rbcore-SavingsMarketOverview/blob/feature/updating_docs_v3/MF_Reports_Creation/MF_README.md) is a step by step on how to create a report on Moneyfacts.
 
### Updating the code
There are seperate code files, one is for Business and one is for Personal products, below is a high level explanation on how and were you update that code. 

### Business products
1. In the Business folder go to your ```main.py``` file. Find the ```clean_sheet()``` function.
2. In the clean sheet function add a new variable with the name of the new product, that happens on the first line of code inside the function (where opening_files() is being called).
3. Also create a new dataframe just below that code should look like this ```<your-product-name> = pd.DataFrame(columns = ['Rank', 'Name', 'Rate', 'Product', 'Date'])``` .
4. Then below in the for loop, look at the other products that are already there. That is the main filtering and through this code you get the information into the s3 bucket.
5. At the end of the function, dont forget to concat and return the new product.
6. Continuing, in the ```opening_files()``` function create a variable like done for the other products.
7. Then do the same in the ```pushing_files()``` function.
8. Finnaly make sure you have created a csv with the name of the new product (make sure you follow the naming convetion that is there with other files) and add it in your S3 bucket. Path should be ```rb-rbcore-dev/Savings-Market-Overview-Scrapper/``` .

### Personal products
1. For the personal products the proccess is slightly different. You need to create a function with the name of the new product you wish to add. Look at the other functions for reference.
2. The only thing you will need to change in the function is the XPATH of the Moneyfacts report. For reference this is what that part of the code looks like ```class_select = driver.find_element(By.XPATH, "/html/body/div/div/div[2]/div/div[2]/div/div[2]/ul/li[14]")``` this report has a position of 14 in the list. Whern you create a new report on MF you will need to inspect the css and see what possition that is.
3. The add the new product in the ```pull_s3_files()``` function.
4. Same for the ```push_s3_files()``` function.
5. Lastly call the new report in the handler, make sure you call it like the other functions are being called, this will make sure that the data will fed in the csv file in the bucket.
   
## Deployment

There has been no CI/CD built for this workflow. To deploy you must use Docker to build an image then AWS CLI to push image to ECR Repo. Once container is in the ECR Repo you can Deploy a new image to your Lambda function via the CLI or AWS Management Console.

CI/CD can be developed see PricingAPI Repo for reference 

### test

Currently no testing is in place - this can be developed as in PricingAPI repo.

### build-and-deploy

1. Build image using Docker

2. Push container into ECR using AWS CLI

3. Deploy new image on Lmabda using AWS CLI or Management Console



## Contributing

To contribute to this project you must have access to the private repository (which I assume you do as you are reading this document). Create a feature branch and when your changes are complete create a pull request into the dev branch. There is a compulsary peer review that needs to be completed before you are able to merge into the Dev or Main branches. Both of these branches are locked otherwise. Main branch is only to be merged with the Dev branch on a set period, for this project we are following Thursday deployments. 

## License

This code must not be used or deployed on any other AWS account or outside of the Recognise Bank network. 

---
