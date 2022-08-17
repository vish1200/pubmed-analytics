import requests
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from .clinical import get_numbers
from .pubmed_clinical import Pubmed_Job
from .pubmed import Scraping_Job
from .utils import upload_to_s3


def get_suggestions(term):
    """
        Get suggest terms from pubmed by term keyword
    """
    url = "https://pubmed.ncbi.nlm.nih.gov/suggestions/?term=%s" % term
    res = requests.get(url)
    return res.text


def upload_data_s3(data, job_name):
    # upload csv and excel files to s3 bucket

    csv_obj = data['csv_obj']
    csv_key = f"jobs/{job_name}/{data['file_name']}.csv"
    upload_to_s3(csv_obj, csv_key)
    print(f"Uploaded {csv_key} to S3")

    excel_obj = data['excel_obj']
    exl_key = f"jobs/{job_name}/{data['file_name']}.xlsx"
    upload_to_s3(excel_obj, exl_key)
    print(f"Uploaded {exl_key} to S3")

    json_data = {
        "csv_file": csv_key,
        "excel_file": exl_key,
        "data": data['results']
    }
    json_key = f"jobs/{job_name}/{job_name}.json"
    upload_to_s3(json.dumps(json_data), json_key)
    print(f"Uploaded {json_key} to S3")


def clinical_scrap(conditions_disease, other_terms):
    """
        Clinical && Pumbed scrap

        Extracting NCT records from clinical website and scraping data from pumbed based on them
    """
    print(f"Pumbed scraping with Clinical was started with conditions_disease: {conditions_disease}, other_terms: {other_terms}", datetime.now())

    keyword = {
        'conditions_disease': conditions_disease,
        'other_terms': other_terms
    }

    file_key = '{} {}'.format(keyword['conditions_disease'], keyword['other_terms'])
    file_name = secure_filename(file_key)
    file_name = file_name[:200]
    print(f"File Name is {file_name}")

    print("Getting NCT numbers started.", datetime.now())
    nct_numbers = get_numbers(keyword=keyword)
    if nct_numbers is None:
        return {
            'results': [],
            'excel_obj': '',
            'csv_obj': '',
            'file_name': file_name
        }
    print("Getting NCT numbers ended.", datetime.now())

    print('Pumbed Scraping with NCT Numbers stated.')
    results, csv_obj, excel_obj = Pubmed_Job(numbers=nct_numbers)

    print(f"Pumbed scraping with Clinical was ended.", datetime.now())
    return {
        'results': results,
        'excel_obj': excel_obj,
        'csv_obj': csv_obj,
        'file_name': file_name
    }


def pubmed_scrap(keyword):
    """ Extracting data from pumbed """
    print(f"Only pumbed scraping was started with keyword {keyword}", datetime.now())
    results, csv_obj, excel_obj, file_name = Scraping_Job(keyword=keyword)
    print(f"Only pumbed scraping was ended", datetime.now())
    return {
        'results': results,
        'excel_obj': excel_obj,
        'csv_obj': csv_obj,
        'file_name': file_name
    }
