Deployment on AWS services
==========================


Project Structures
------------------

This project is using AWS S3 Bucket, Lambda function, Cloudwatch, ApiGateway and SQS. <br>
The project diagram is <a href="">here</a>

![alt text](https://github.com/upworka0/pubmed_aws/blob/master/scrapingUnit/vendor/statics/img/project-diagram.png?raw=true)


The project includes 3 lambda functions, they are scrapingUnit, pdfDownloader and pdfExtractor

    - ScrapingUnit
        Includes webinterface and scraping modules, is triggering by http request and s3 object creation event

    - pdfDownloader
        Includes pdf downloading module, is triggering by SQS event

    - pdfExtractor
        Includes pdf text extracting module, is triggering by s3 object creation event
    

How to deploy the whole project?
--------------------------------
The project includes 3 lambda functions so that need to deploy one by one.
Every directory is one function. scrapingUnit, pdfDownloader and pdfExtractor

For scrapingUnit, <a href="/scrapingUnit/readme.MD">please check here</a> <br>

For pdfDownloader, <a href="/pdfDownloader/readme.MD">please check here</a> <br>

For pdfExtractor, <a href="/pdfExtractor/readme.MD">please check here</a> <br>
