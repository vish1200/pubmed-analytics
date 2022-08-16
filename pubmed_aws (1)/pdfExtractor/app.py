"""
    Lambda handler to process data from API Request.
    Downloading pdfs.zip file with job_id from s3 bucket,
    Unzipping it into io.ByteIO object, and getting file list inside it.
    Process pdf files one by one in it and Zipping extracted text files,
    Finally uploading it to s3 bucket so that user can download it
    """

from modules.utils import zip_file_objects, upload_to_s3
from modules.multi_processing import Extract_Job


def handler(event, context):
    print(f'Handler is triggering ...')
    records = event['Records']
    print("Request body", records)

    zip_keys = []
    for record in records:
        file_key = record['s3']['object']['key']
        job_id = file_key.split("/")[1]
        print("Job ID", job_id)
        text_data_arr = Extract_Job(job_id)

        # uploading txt zip file to s3
        zipObj = zip_file_objects(text_data_arr)
        txts_zip_key = f"jobs/{job_id}/txts.zip"
        upload_to_s3(zipObj, txts_zip_key)
        zip_keys.append(txts_zip_key)

    return {
        "status": 200,
        "zip": zip_keys
    }


# # testing
# event = {
#     "queryStringParameters": {
#         "job_id": "job_1639659447785"
#     }
# }
# handler(event, None)
