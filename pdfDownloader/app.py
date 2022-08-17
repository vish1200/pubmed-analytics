import os
from chalice import Chalice
import boto3
import json
from chalicelib.multi_processing import Pdf_Job
from chalicelib.helpers import upload_to_s3, zip_file_objects
import csv
import io
import multiprocessing


app = Chalice(app_name='pdfDownloader')
BUCKET_NAME = os.environ.get('BUCKET_NAME', 'pubmed')
s3 = boto3.resource('s3')
sqs = boto3.resource('sqs')
QUEUE_NAME = os.environ.get('QUEUE_NAME', 'pubmed-queue')


# @app.route('/create_job', methods=['POST'])
# def create_job():
#     body = app.current_request.json_body
#     job_id = body.get('job_id')
#     if job_id:
#         try:
#             queue = sqs.get_queue_by_name(QueueName=QUEUE_NAME)
#             response = queue.send_message(MessageBody=json.dumps(body))
#             app.log.info(response)
#             return {
#                 "status": 200,
#                 "message": "Message was successfully added to queue. The process is running on background.",
#                 "messageId": response['MessageId']
#             }
#         except Exception as e:
#             app.log.error("Error: " + str(e))
#             return {
#                 "status": 400,
#                 "message": str(e)
#             }


@app.on_sqs_message(queue=QUEUE_NAME, batch_size=1)
def handle_sqs_message(event):
    for record in event:
        app.log.info("Received message with contents: %s", record.body)

        print("Process count: ", multiprocessing.cpu_count())

        input_dict = json.loads(record.body)
        job_id = input_dict.get('job_id')
        results_dict, results_pdfs = Pdf_Job(job_id)

        zip_obj = zip_file_objects(results_pdfs)
        zip_key = f"jobs/{job_id}/pdfs.zip"
        upload_to_s3(zip_obj, zip_key)

        csv_key = f"jobs/{job_id}/report.csv"
        csv_obj = io.StringIO()

        results_dict = list(results_dict)
        for ind in range(len(results_dict)):
            results_dict[ind].pop('no')

        keys = results_dict[0].keys()
        dict_writer = csv.DictWriter(csv_obj, keys)
        dict_writer.writeheader()
        dict_writer.writerows(results_dict)
        upload_to_s3(csv_obj, csv_key)

    return "OK"


# @app.route('/download_pdf/{job_id}', methods=['POST'])
# def download_pdf(job_id):
#     results_dfs, results_pdfs = Pdf_Job(job_id)
#
#     zip_obj = zip_file_objects(results_pdfs)
#     zip_key = f"jobs/{job_id}/pdfs.zip"
#     upload_to_s3(zip_obj, zip_key)
#
#     csv_key = f"jobs/{job_id}/report.csv"
#     data = merge_dataFrames(results_dfs)
#     csv_obj = data.to_csv()
#     upload_to_s3(csv_obj, csv_key)
#
#     return {
#         'results': "Check downloads folder.",
#         'csv': csv_key,
#         'zip': zip_key
#     }

#
# results_dict, results_pdfs = Pdf_Job('job_1639654383806')
# print("Ended downloading")
# print("Uploading now")

# zip_obj = zip_file_objects(results_pdfs)
# zip_key = "jobs/job_1639654383806/pdfs.zip"
# upload_to_s3(zip_obj, zip_key)

# csv_key = "jobs/job_1639654383806/report1.csv"
# csv_obj = io.StringIO()
#
# results_dict = list(results_dict)
# for ind in range(len(results_dict)):
#     results_dict[ind].pop('no')

# keys = results_dict[0].keys()
# dict_writer = csv.DictWriter(csv_obj, keys)
# dict_writer.writeheader()
# dict_writer.writerows(results_dict)
#
# upload_to_s3(csv_obj, csv_key),
