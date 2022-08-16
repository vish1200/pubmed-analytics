import os
from datetime import datetime
import boto3
import io
import zipfile
import textract


BUCKET_NAME = os.environ.get("BUCKET_NAME", "pumbed")


def get_current_time():
    return datetime.now().strftime("%H:%M:%S")


def download_zip(zip_path):
    """
        Downloading Zip file from s3 and get file list inside it.
        Returning Zip file Object and its file list
        """
    s3 = boto3.resource("s3")
    bucket = s3.Bucket(BUCKET_NAME)

    print(f"Downloading zip: {zip_path} from s3", get_current_time())
    obj = bucket.Object(zip_path)
    zipObj = io.BytesIO(obj.get()["Body"].read())
    zipObj.seek(0)

    file_list = []
    with zipfile.ZipFile(zipObj, mode='r') as zipf:
        file_list = zipf.namelist()
    print("Finished downloading zip", get_current_time())

    return zipObj, file_list


def extract_file(zipObj, filename):
    """
        Extract specific file from Zip Object and save it with filename.
        """
    # print(f"Extracting file {filename} from Zip", get_current_time())
    # Read the file as a zipfile and process the members
    with zipfile.ZipFile(zipObj, mode='r') as zipf:
        fname = filename.replace("/tmp/", "")
        file_contents = zipf.read(fname)
        with open(filename, mode='wb') as f:
            f.write(file_contents)

    print(f"Extracted file {filename} from Zip", get_current_time())


def delete_file(file_path):
    """
        Deleting file with its path
        """
    # print(f"Deleting file {file_path}", get_current_time())
    if os.path.exists(file_path):
        os.remove(file_path)
        print(f"Deleted: {file_path}", get_current_time())
    else:
        print(f"The file {file_path} does not exist")


def extract_text(pdf_path):
    """
        Extracting text from a pdf by its path,
        and returning its name and text data
        """
    print(f"Extracting: {pdf_path}", get_current_time())
    text = textract.process(pdf_path)
    print(f"Extracted: {pdf_path}", get_current_time())
    return {
        "pdf": pdf_path,
        "text": text
    }


def zip_file_objects(text_data_arr):
    """
        Zipping all extract text files into one,
        and returning Zip object
        """
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "a", zipfile.ZIP_DEFLATED, False) as zipper:
        for text_data in text_data_arr:
            file_name = text_data['pdf'].split('/')[-1].replace('.pdf', '.txt')
            zipper.writestr(file_name, text_data['text'])

    return zip_buffer


def upload_to_s3(file_obj, key):
    s3 = boto3.client('s3')
    """
        Upload file to S3 bucket and make it public
    """
    print(f"Uploading to s3, key is {key}", get_current_time())
    if type(file_obj) == str:
        s3.put_object(Bucket=BUCKET_NAME, Key=key, Body=file_obj.encode('utf-8'), ACL='public-read')
    else:
        file_obj.seek(0)
        s3.put_object(Bucket=BUCKET_NAME, Key=key, Body=file_obj.read(), ACL='public-read')
    print(f"Uploaded to s3, key is {key}", get_current_time())


def process_unit(zipObj, filename):
    """
        Textracting Unit for one file from zipObject
        """
    pdf_path = "/tmp/" + filename
    extract_file(zipObj, pdf_path)
    text_data = extract_text(pdf_path)
    delete_file(pdf_path)
    return text_data


def process(zip_key):
    """
        Process all pdf files inside one zip file for testing
        """
    text_data_arr = []
    zipObj, file_list = download_zip(zip_key)
    for filename in file_list:
        text_data = process_unit(zipObj, filename)
        text_data_arr.append(text_data)

    return text_data_arr


def splitter(data, count):
    """
        Split list of data into sub lists of count
        """
    row_count = len(data)
    interval = row_count // count
    if interval < 0:
        return [data]
    splitter_data = []
    for i in range(row_count):
        start = i * interval
        end = (i + 1) * interval
        if i == row_count - 1:
            end = row_count
        dt = data[start:end]
        splitter_data.append(dt)

    return splitter_data
