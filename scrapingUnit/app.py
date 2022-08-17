import os
from chalice import Chalice, Response, Cron
import boto3
import time
import jinja2
import json
import multiprocessing
from datetime import datetime
from chalicelib.modules.utils import upload_to_s3, get_from_s3
from chalicelib.modules.functions import clinical_scrap, pubmed_scrap, upload_data_s3
from chalicelib.auth.db import get_user
from chalicelib.auth.auth import is_authorized
from chalicelib.modules.cron_utils import delete_s3_files_in_folder
from urllib.parse import unquote


app = Chalice(app_name='scrapingUnit')

sqs = boto3.resource('sqs')
bucket_name = os.environ.get('BUCKET_NAME', 'pubmed')
QUEUE_NAME = os.environ.get('QUEUE_NAME', 'pubmed-queue')


def render(tpl_path, context):
    path, filename = os.path.split(tpl_path)
    return jinja2.Environment(loader=jinja2.FileSystemLoader(path or "./")).get_template(filename).render(context)


@app.route('/login', methods=['GET', 'POST'], content_types=['application/x-www-form-urlencoded', 'text/html', 'application/json'])
def login():
    error = None
    if app.current_request.method == 'POST':
        str_body = app.current_request.raw_body.decode('utf-8')
        params = dict(pair.split('=') for pair in str_body.split('&'))
        user_info = get_user(params['username'], params['password'])

        credentials = {
            "username": params['username'],
            "expires_at": datetime.now().timestamp() + 7200
        }
        next_url = unquote(params.get('next', 'api/'))
        if user_info:
            return Response(
                body='',
                headers={
                    'Location': next_url,
                    'Set-Cookie': "credentials=\"%s\"" % credentials
                },
                status_code=302
            )
        error = "Invalid username or password."

    next_url = app.current_request.query_params.get('next', 'api/')
    return Response(render('chalicelib/templates/login.html', {"error": error, "next": next_url}), status_code=200,
                    headers={"Content-Type": "text/html", "Access-Control-Allow-Origin": "*"})


@app.route('/')
def index():
    if is_authorized(app):
        template_path = "chalicelib/templates/index.html"
        template = render(template_path, {})
        return Response(template, status_code=200,
                        headers={"Content-Type": "text/html", "Access-Control-Allow-Origin": "*"})
    else:
        return Response(
            body='',
            headers={'Location': 'api/login?next=/api'},
            status_code=302
        )


@app.route('/clinical')
def index():
    if is_authorized(app):
        template_path = "chalicelib/templates/clinical.html"
        template = render(template_path, {})
        return Response(template, status_code=200,
                        headers={"Content-Type": "text/html", "Access-Control-Allow-Origin": "*"})

    else:
        return Response(
            body='',
            headers={'Location': '/api/login?next=/api/clinical'},
            status_code=302
        )


@app.route('/create_job', methods=['POST'])
def create_job():
    # if is_authorized(app):
    body = app.current_request.json_body
    print("Handler is triggering with the following data ...")
    print(body)

    action_type = body.get('action_type', 'scrap')
    file_key = None
    data = {}
    job_id = ""

    if action_type == 'scrap':
        """
            Create New Job to scrap sites
            """
        type = body.get('type')
        timestamp = round(time.time() * 1000)
        job_id = f"job_{timestamp}"

        data = {
            "type": type,
            "id": job_id,
        }

        if type == 'pubmed':
            data['keyword'] = body.get('keyword')
        elif type == 'clinical':
            data['conditions_disease'] = body.get('conditions_disease')
            data['other_terms'] = body.get('other_terms')
        file_key = f"events/{job_id}.json"

    elif action_type == 'extract':
        """
            Create New Job to extracts texts from pdf files
            """
        job_id = body.get('job_id')
        file_key = f"jobs/{job_id}/extract.json"
        data = {
            "id": job_id
        }

    try:
        upload_to_s3(json.dumps(data), file_key)
        print(f"Job was created successfully with this name: {job_id}")
        return {
            "status": 200,
            "jobId": job_id
        }
    except Exception as e:
        print(e)
        return {
            "status": 400,
            "message": f"There is an error in creating job with name {job_id}"
        }
    # else:
    #     return {
    #         "status": 401,
    #         "message": "Unauthorized"
    #     }


@app.on_s3_event(bucket=bucket_name, events=['s3:ObjectCreated:Put'], prefix='events/', suffix='.json')
def process(event):
    print(event.key)
    body = json.loads(get_from_s3(event.key))
    print(body)

    print("Core count", multiprocessing.cpu_count())
    print("Successfully Started!!!", datetime.now())

    type = body.get('type')
    job_name = body.get('id')

    if type == 'pubmed':
        keyword = body.get('keyword')
        data = pubmed_scrap(keyword=keyword)
        upload_data_s3(data=data, job_name=job_name)

    elif type == 'clinical':
        conditions_disease = body.get('conditions_disease')
        other_terms = body.get('other_terms')
        data = clinical_scrap(conditions_disease=conditions_disease, other_terms=other_terms)
        upload_data_s3(data=data, job_name=job_name)

    print("Successfully Done!!!", datetime.now())


@app.route('/create_pdf_job', methods=['POST'])
def create_pdf_job():
    # if is_authorized(app):
    json_body = app.current_request.json_body
    job_id = json_body.get('job_id')
    body = app.current_request.raw_body.decode()
    if job_id:
        try:
            print("Message body", body)
            queue = sqs.get_queue_by_name(QueueName=QUEUE_NAME)
            response = queue.send_message(MessageBody=body)
            app.log.info(response)
            return {
                "status": 200,
                "message": "Message was successfully added to queue. The process is running on background.",
                "messageId": response['MessageId']
            }
        except Exception as e:
            app.log.error("Error: " + str(e))
            return {
                "status": 400,
                "message": str(e)
            }

    # return {
    #     "status": 401,
    #     "message": "Unauthorized"
    # }



"""
def test_process(body):
    print(body)

    print("Core count", multiprocessing.cpu_count())
    print("Successfully Started!!!", datetime.now())

    type = body.get('type')
    job_name = body.get('id')

    if type == 'pubmed':
        keyword = body.get('keyword')
        data = pubmed_scrap(keyword=keyword)
        upload_data_s3(data=data, job_name=job_name)

    elif type == 'clinical':
        conditions_disease = body.get('conditions_disease')
        other_terms = body.get('other_terms')
        data = clinical_scrap(conditions_disease=conditions_disease, other_terms=other_terms)
        upload_data_s3(data=data, job_name=job_name)

    print("Successfully Done!!!", datetime.now())


# test_dict = {
#     "type": "clinical",
#     "conditions_disease": "COVID-19 Pneumonia study",
#     "other_terms": "",
#     "id": "clinical_test"
# }
# test_process(test_dict)
"""


@app.schedule(Cron(0, 0, "*", "*", "?", "*"))
def cron_handler(event):
    print("Handler is triggering ...")
    tday = time.time()
    duration = 86400 * 3
    expire_limit = tday - duration

    prefix = "jobs/"
    delete_s3_files_in_folder(bucket=bucket_name, prefix=prefix, expire_limit=expire_limit)

    prefix = "events/"
    delete_s3_files_in_folder(bucket=bucket_name, prefix=prefix, expire_limit=expire_limit)

    return "OK"
