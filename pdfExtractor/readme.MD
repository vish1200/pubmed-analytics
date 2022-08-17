PDFExtractor
=============
This project is using Docker Image in aws lambda function.


How to deploy?
--------------
Need to install awscli and configure credentials first. (region should be eu-west-2: London)

Create new aws ECR Repository here. <br>
    https://eu-west-2.console.aws.amazon.com/ecr/repositories?region=eu-west-2
    
    
Build docker image and upload it with following command
    
    aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin <ID>.dkr.ecr.eu-west-2.amazonaws.com
    
    
    docker build -t <TAG> .
    
    docker tag textractor:latest <ID>.dkr.ecr.eu-west-2.amazonaws.com/<TAG>:latest
    
    docker push <ID>.dkr.ecr.eu-west-2.amazonaws.com/<TAG>:latest


After uploading docker image, create aws lambda function with it and add trigger source as SQS.