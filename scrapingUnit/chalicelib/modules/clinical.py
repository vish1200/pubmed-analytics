import requests
import re
from time import sleep
from bs4 import BeautifulSoup
from multiprocessing import Process, Manager
from chalicelib.modules.utils import get_process_range_clinical, get_thread_page_range, ThreadWithReturnValue


BASE_URL = "https://www.clinicaltrials.gov/ct2/results"


def parse_soup(content):
    return BeautifulSoup(content, 'html.parser')


def get_query_id(content):
    total_count = 0
    soup = parse_soup(content)

    wrappers = soup.select('.ct-inner_content_wrapper > .w3-center')
    if len(wrappers) > 0:
        try:
            total_count = int(wrappers[0].text.split(' ')[0])
        except Exception as e:
            print(e)

    script = soup.find('script', text=re.compile('use strict'))
    if script:
        script_text = script.contents[0]
        _group = re.search('ct2/results/rpc/(.*)"', script_text)
        if _group is not None:
            return _group.group(1), total_count
        else:
            print('Not found group on script tag')
        return None, 0
    else:
        print('Not found Script Tag')
    return None, 0


class Clinical:
    """
    Extract data from clilical using requests module
    """

    def __init__(self, query_id=None, page_range=None):
        self.post_url = ''
        self.query_id = query_id
        self.page_range = page_range
        self.header = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"
        }

    def get_total_count(self, keyword):
        params = {
            'cond': keyword['conditions_disease'],
            'term': keyword['other_terms']
        }
        res = self.do_request(BASE_URL, params)
        if res is not None:
            return get_query_id(res.text)

        return None, 0

    def run(self):
        records = []
        for page in self.page_range:
            response = self.post_request(page*100)
            if response is None or len(response['data']) == 0:
                break
            # total = response['recordsFiltered']
            records += response['data']
        sleep(0.2)
        return records

    def post_request(self, start):
        payload = {
            'start': start,
            'length': 100
        }
        self.post_url = BASE_URL + '/rpc/' + self.query_id

        for try_cnt in range(5):
            try:
                response = requests.post(url=self.post_url, headers=self.header, data=payload)
                return response.json()
            except ConnectionError:
                print(f'Connection Error, Retry {try_cnt + 1}')
                sleep(0.2)
                continue
            except Exception as e:
                print(e)
                return None
        return None

    def do_request(self, url, params):
        response = None
        for try_cnt in range(5):
            try:
                response = requests.request('GET', url=url, headers=self.header, params=params)
                return response
            except ConnectionError:
                print(f'Connection Error, Retry {try_cnt + 1}')
                sleep(0.2)
                continue
            except Exception as e:
                print(e)
                return response
        return response


def thread_job(unit):
    records = unit.run()
    return records


class MultiThread(Process):
    """
        Threading module
        """
    def __init__(self, _range, query_id, results):
        super(MultiThread, self).__init__()
        self._range = _range
        self.query_id = query_id
        self.results = results

    def run(self):
        thread_page_array = get_thread_page_range(thread_count=6, total_count=(self._range[1] - self._range[0]))
        print(thread_page_array)
        threads = []
        for page_array in thread_page_array:
            r_page_array = [x + self._range[0] for x in page_array]
            if len(r_page_array):
                unit = Clinical(query_id=self.query_id, page_range=r_page_array)
                thread = ThreadWithReturnValue(target=thread_job, args=(unit,))
                thread.start()
                threads.append(thread)

        for thread in threads:
            records = thread.join()
            print(f"From {len(self.results)} To {len(self.results) + len(records)}")
            self.results.extend(records)


def get_numbers(keyword):
    """
    Retrieving total NCT numbers by using clinical module
    """
    clinical = Clinical()

    manager = Manager()
    results = manager.list()

    query_id, total_count = clinical.get_total_count(keyword=keyword)
    print(f'Clinical Total Count: {total_count}, Query ID: {query_id}')
    if total_count > 20000:
        total_count = 20000

    if total_count > 0:
        threads = []
        thread_count = 4
        ranges = get_process_range_clinical(thread_count=thread_count, total_count=total_count)
        for _range in ranges:
            thread = MultiThread(
                query_id=query_id,
                _range=_range,
                results=results,
            )
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()
        print("Total Count: ", len(results), ranges)
        return results
    return None
