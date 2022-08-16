FROM public.ecr.aws/lambda/python:3.8

RUN yum -y update
RUN yum -y install poppler-utils flac sox swig

COPY . ./

RUN pip3 install -r requirements.txt

CMD ["app.handler"]