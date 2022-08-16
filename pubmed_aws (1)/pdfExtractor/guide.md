    
    aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin 938870576265.dkr.ecr.eu-west-2.amazonaws.com
    
    
    docker build -t textractor .
    
    docker tag textractor:latest 938870576265.dkr.ecr.eu-west-2.amazonaws.com/textractor:latest
    
    docker push 938870576265.dkr.ecr.eu-west-2.amazonaws.com/textractor:latest