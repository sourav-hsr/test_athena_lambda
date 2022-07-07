# HSR Infrastructure Dockerized Lambdas Template

This repository explains how to create your own dockerized lambda functions

## Lambdas Structure
* The existing lambda functions directory is not something you need for your own lambda functions.  I included it so that you can see examples of how to call the download data and upload data to db functions that I have written and are available on our AWS cloud.

## Environment Setup
### Prerequisites
* Installing Node.js
  * Download and Install Node.js from this link - https://nodejs.org/en/download/ (the default installation options should be fine)
* Installing python and pipenv
  * Download and Install python from this link - https://www.python.org/downloads/ (Currently Using python 3.7 but any version you prefer should be fine)
  * in the terminal go to the path of the python directory's scripts folder (C:/Python37/Scripts)
  * run "pip install pipenv"
* Installing Serverless (Requires Node.js) (Documentation - https://www.serverless.com/)
  * Open the terminal and go to the path for this Repository
  * run "npm install"
  * run "npm install -g serverless"
  * run "serverless plugin install -n serverless-python-requirements"
* Install AWS CLI
  * Download and Install the AWS CLI from this link - https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html 
  * After installing the AWS CLI go to the terminal and type in `aws configure` to set your default access keys to aws.  See this documentation - https://docs.aws.amazon.com/cli/latest/userguide/getting-started-quickstart.html

## Modifying the Stack for your Own Function
* ./build/git_update.sh
  * at the moment no changes need to be made to this file
* ./templateFunction
  * rename this folder to be the name of your function. I will advise to use all lowercase.
  * ./events
    * You will want to change the test01.json file to have the event parameters of your function for local testing
  * ./lib
    * If you want to import other py files then throw them in here and call them using the example in the app.py file
  * app.py 
    * this is the bare skeleton that you need to run the lambda function from events
    * you will put your main python code for the lambda function here
  * app-example.py
    * this is an example of the clean TRI data lambda that I created so feel free to use it as reference
  * Dockerfile
    * from lines 2 through 5 you will want to replace `templateFunction` with the `name of this folder`
  * local.py
    * no need to change this file and it is used to do local testing of the lambda function
  * requirements.txt
    * will need to update this with the packages required for your lambda function
  * test_event.ipynb
    * this is an example of how I tested the lambda function after the repository was built and the lambda was live on aws.  Can use it as a reference to help you test your lambda functions at that stage.
* serverless.yml
  * update line 1 from `hsr-dockerized-lambdas-template` to `hsr-dockerized-lambdas-yourfunctionname`
  * depending on what you are doing you might need to update the IAM roles from line 21 down
  * If your function needs access to a specific S3 bucket, you should add it to the resources after line 48, by copying lines 47 and 48 and replacing `INTERNAL_PRODUCTS_BUCKET` with `yourbucketname` as specified in environment.yml
  * nothing else in this file needs to be changed
* ./serverlessResources
  * environment.yml
    * the environment variables here are used throughout the serverlessResources yml files 
    * the main one to change is modifying the end of the `LAMBDA_ARN_BASE` from `hsr-dockerized-lambdas-template` to `hsr-dockerized-lambdas-yourfunctionname` that you made in the serverless.yml file
    * you might need to add more environment variables here depending on your script
    * only update the ones / add to the `stg` section as thats the only one were using at the moment
    * most of the common ones I have used are in here so you might not need to add any more
  * functions-lambda.yml
    * change line 1 to be the name of your function
    * change line 2 from `lambdatemplatefunction:v0.1.1` to `yourfunctionname:v0.1.1`
    * NOTE: you will need to update the tag from v0.1.1 when the github actions pushes a new version to ECR.  v0.1.1 is the default tag given to the repository when it is first pushed
    * change the description in line 3 
    * change the memorySize of your function to what you need.  10GB is the maximum allowed, Not sure what the minimum is but lowest i put mine are at 512MB.  Try to keep it as low as you can though cause this is the memory we are charged for.
    * line 12 down are the environment variables that are defined for your lambda function feel free to change these to be environment variables you need in your lambda
  * resources-ecr.yml
    * change line 1 to be the name of your function
    * change line 5 to be the name of your function 
  * resources-eventbridge.yml
    * change line 3 to be `EventRuleyourFunctionName`
    * change line 6 to be `stg-rule-yourfunctionname`
    * change in line 10: `templateFunctionEvent` to `yourFunctionNameEvent` and `templateFunction` to `yourFunctionName`
    * in line 12 and 18 change `hsr-dockerized-lambdas-template-stg-templateFunction` to `line1fromServerless.yml-stg-yourFunctionName`
    * in lines 13 replace `templateFunction` with `yourFunctionName`
    * NOTE: line 10 defines the pattern matching for the lambda event
      * Examples on how you define the event to contain the information to trigger the lambda can be found in `./existingLambdaFunctions/lambda_functions_package.py` in lines 9, 32, and 33 for triggering the download data lambda with the geometry datatype
* .github\workflows\templatefunction.yml
  * rename this file to be the `name of your function`
  * on line 2 update the description to Build and Push `your function name` Lambda Image to AWS ECR
  * make sure to indicate the correct branch on line 5
  * on line 34 update the `ECR_REPOSITORY` environment variable from `templatefunction` to `your function name`
  * on line 37 update the build path from `"./templateFunction/Dockerfile"` to `"./name of your lambda folder/Dockerfile"`
* package.json
  *. You need to make sure the aws profile  specified at the end of line 6 to 10 is recognised on your local PC.
  *. To configure this, go into D:\Users\{your_user_name}\.aws 
  *. Inside the config and credential files, make sure to use the same [profile name]  in package.json. In most cases, you can use "default".
  *. Make sure that the config file has "region = us-east-1" and "output = json" 


## Testing Lambda Functions Locally
* open a command prompt or terminal and cd to your function's folder (cd ./templateFunction)
* run `pipenv shell`
* run `pip install -r requirements.txt`
* run `python local.py --event .\events\test01.json`
* to leave the virtual environment run `exit`
### Running the stack
* Setup AWS Secret keys on github
    * go to the settings for your repository
    * on the left hand side click on Secrets then Actions
    * put in the two components of your aws secret keys in there
* Open terminal and navigate to the root of this repository
* run `npm i`
    * Inititally comment out the line 72 and 73 of the serverless.yml. Then run 
    `npm run stg:deploy` to allow the ECR repository to be built first.
    * An error will be thrown in the terminal saying "UPDATE_ROLLBACK_COMPLETE". When this occurs, login to the cloudformation console at
    console.aws.amazon.com/cloudformation/ and delete the stack which should be on top of the list
    * uncomment line 73 of the serverless.yml
    * push the repository to github to publish the docker image to the ecr repository you created in the first npm run command
    * wait for the github actions to successfully push your container to ecr. Take note of the version number assigned to the repository on github
    * uncomment line 72 of serverless.yml
    * go into ./ServerlessResources/functions-lambda.yml and update the version number on line 2 to match that on github
    * run `npm run stg:deploy`

## Dockerized Lambda Functions
* Resources
    * https://www.youtube.com/watch?v=LbbuuD88Rwo
    * https://www.youtube.com/watch?v=Hv5UcBYseus
    * https://www.serverless.com/blog/container-support-for-lambda
    * https://github.com/amazon-archives/aws-lambda-container-image-converter/actions/runs/340248336/workflow
    * https://github.com/antonputra/tutorials/blob/main/lessons/086/README.md
    * https://aws.amazon.com/blogs/compute/using-amazon-rds-proxy-with-aws-lambda/
    * https://montecha.com/blog/creating-an-rds-proxy-using-serverless-framework/
    
