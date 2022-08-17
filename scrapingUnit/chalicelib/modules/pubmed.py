"""
    Scraping module for only pumbed
"""
import requests
from bs4 import BeautifulSoup
import time
import re
from multiprocessing import Process, Manager
import math
from werkzeug.utils import secure_filename
from .utils import write_csv, excel_out, get_thread_range_pumbed, ThreadWithReturnValue, get_core_count
from datetime import datetime


class ScrapingUnit:
    """
        Scraping Unit
        """

    def __init__(self, keyword, page_number=1):
        self.keyword = keyword
        self.base_url = "https://pubmed.ncbi.nlm.nih.gov/"
        self.page_number = page_number
        self.total_count = 0
        self.results_dict = []
        self.results = []
        self.count = 0
        self.sess = requests.session()

    def get_soup(self, response):
        """
            Return soup object from http response
        :param response:
        :return: BeautifulSoup4 object
        """
        return BeautifulSoup(response.text, "html.parser")

    def get_total_count(self, soup):
        """
        Get Total count of search results
        :param soup
        :return: None
        """
        try:
            results_text = soup.find(attrs={'class': 'results-amount'}).text
            if 'No' in results_text:
                self.total_count = 0
            else:
                self.total_count = int(results_text.replace('results', '').replace(',', '').strip())
        except Exception as ex:
            print(type(ex).__name__, ex.args)
            self.total_count = 1

    def get_text(self, soup, ele, condition):
        """
        Get Text of Element from soup by condition
        :param soup:
        :param ele:
        :param condition:
        :return: string
        """
        try:
            return soup.find(ele, condition).text.strip()
        except Exception as e:
            # print(ele, condition)
            pass
        return ""

    def ajdust_abstract(self, abstract):
        """
        Remove unnecessary blanks and paragraphs
        :param abstract:
        :return: string
        """
        slices = abstract.split('\n')
        full_text = ""
        for i in range(len(slices) - 2):
            if slices[i + 1].strip() == '' and slices[i + 2].strip() == '':
                full_text += slices[i].strip() + '\n\n'
                i += 2
        full_text += slices[len(slices) - 1].strip()
        return full_text

    def get_affiliations(self, article):
        """
        Return affiliation and author email
        :param article:
        :return: string, string
        """
        affiliations_div = article.find('div', {'class': 'affiliations'})
        affiliation = ""
        author_email = []
        if affiliations_div:
            first = True
            for li in affiliations_div.find_all('li'):
                sup_key = self.get_text(li, 'sup', {})
                text = li.text.strip()[len(sup_key):]
                if first:
                    affiliation = text
                    first = False

                lst = re.findall('\S+@\S+', text)
                if len(lst) > 0:
                    for email in lst:
                        author_email.append(email.strip().strip(",").strip(".").strip(";"))
                        text = text.replace(email, '').strip()

                    affiliation = text.replace("Electronic address:", "").replace("Electronic address", '')\
                        .strip().strip(",").strip(".").strip(";")

        return affiliation, author_email

    def get_date(self, full_view):
        """
            Return date of Absctact
            """
        text = self.get_text(full_view, 'span', {"class": "cit"})
        return text.split(";")[0]

    def get_header_information(self, article):
        """
        Return title, DOI, link, author names, abstract, affiliation and author email
        :param article:
        :return: dict
        """
        full_view = article.find('div', {'class': 'full-view'})
        heading_title = self.get_text(full_view, 'h1', {'class': 'heading-title'})
        doi = self.get_text(full_view, 'span', {'class': 'citation-doi'}).strip('doi:')
        pmid = self.get_text(full_view, 'strong', {'class': 'current-id'})
        pmcid = self.get_text(full_view, 'span', {'class': 'identifier pmc'}).strip("PMCID:").strip()
        date = self.get_date(full_view)
        authors_list = []
        authors_spans = full_view.find_all('span', {'class': 'authors-list-item'})
        for author_span in authors_spans:
            name = self.get_text(author_span, 'a', {'class': 'full-name'})
            authors_list.append(name)

        abstract = self.get_text(article, 'div', {'class': 'abstract-content selected'}).replace('\n\n', '')
        abstract = self.ajdust_abstract(abstract)

        affiliation, author_email = self.get_affiliations(article)

        return {
            "Pubmed link": "%s%s" % (self.base_url, pmid),
            "heading_title": heading_title,
            "date": date,
            "abstract": abstract,
            "authors_list": ", \n".join(authors_list),
            "affiliation": affiliation,
            "author_email": ", \n".join(author_email),
            "pmcid": pmcid,
            "doi": doi,
        }

    def get_full_text_links(self, article):
        """
        Return full text links from soup
        :param article:
        :return: array
        """
        full_text_links = []
        full_text_links_list_div = article.find('div', {'class': 'full-text-links-list'})
        if full_text_links_list_div:
            atags = full_text_links_list_div.find_all('a')
            for tag in atags:
                full_text_links.append(tag.attrs['href'])

        return full_text_links

    def get_mesh_terms(self, article):
        """
        Return array of mesh terms from soup
        :param article:
        :return: array
        """
        mesh_terms = []
        mesh_div = article.find('div', {'class': 'mesh-terms keywords-section'})
        if mesh_div:
            keyword_list = mesh_div.find('ul', {'class': 'keywords-list'})
            if keyword_list:
                for button in keyword_list.find_all('button', {'class': 'keyword-actions-trigger'}):
                    mesh_terms.append(button.text.strip())
        return mesh_terms

    def get_publication_types(self, article):
        """
        Return publication types from soup
        :param article:
        :return: array
        """
        pub_types = []
        pub_types_div = article.select('div[class*="publication-types keywords-section"]')
        if len(pub_types_div) > 0:
            keyword_list = pub_types_div[0].find('ul', {'class': 'keywords-list'})
            if keyword_list:
                for button in keyword_list.find_all('button', {'class': 'keyword-actions-trigger'}):
                    pub_types.append(button.text.strip())
        return pub_types

    def parse_soup(self, soup):
        """
        Parse soup object to get necessary information
        :param soup: BeautifulSoup4 Object
        :return: None
        """
        articles_div = soup.find_all('div', {"class": "results-article"})
        results_data = []
        for article in articles_div:
            infor = self.get_header_information(article)
            infor['full_text_links'] = ",\n".join(self.get_full_text_links(article))
            infor['mesh_terms'] = ", \n".join(self.get_mesh_terms(article))
            infor['publication_types'] = ", \n".join(self.get_publication_types(article))
            results_data.append(infor)
            self.count += 1

        lines = []
        for row in results_data:
            lines.append(list(row.values()))

        self.results_dict += results_data
        self.results += lines

    def unique_soup(self, soup):
        articles_div = soup.find('main', {"class": "article-details"})
        results_data = []
        infor = self.get_header_information(articles_div)
        infor['full_text_links'] = ",\n".join(self.get_full_text_links(soup))
        infor['mesh_terms'] = ", \n".join(self.get_mesh_terms(articles_div))
        infor['publication_types'] = ", \n".join(self.get_publication_types(articles_div))
        results_data.append(infor)
        self.count += 1

        lines = []
        for row in results_data:
            lines.append(list(row.values()))

        self.results_dict += results_data
        self.results += lines

    def next_page(self):
        """
            Scrap Next page
        """

        print(f"Scraping is starting in page {self.page_number} : {datetime.now()}")
        data = {
            "term": self.keyword,
            "size": 200,
            "page": self.page_number,
            "format": "abstract"
        }

        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/83.0.4103.97 Safari/537.36"
        }
        res = None
        for i in range(5):
            try:
                res = self.sess.get(self.base_url, params=data, headers=headers)
                time.sleep(0.2)
                break
            except Exception as e:
                print(e, self.page_number, "next_page")
                time.sleep(0.2)

        soup = self.get_soup(res)
        self.parse_soup(soup)

    def do_scraping(self):
        self.results_dict = []
        self.results = []
        if self.page_number < 2:
            print(f"Scraping is starting in page {self.page_number} : {datetime.now()}")
            data = {
                "term": self.keyword,
                "size": 200,
                "page": self.page_number,
                "format": "abstract"
            }
            headers = {
                "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.183 Safari/537.36"
            }

            res = ""
            for try_cnt in range(5):
                try:
                    res = self.sess.get(self.base_url, params=data, headers=headers)
                    if res.status_code == 200:
                        break
                except Exception as e:
                    pass
                time.sleep(0.2)

            soup = self.get_soup(res)
            self.get_total_count(soup)
            if self.total_count == 1:
                self.unique_soup(soup)
            else:
                self.parse_soup(soup)
        else:
            self.next_page()
            # print(self.results_dict)
        print(f"Scraping was ended for page {self.page_number} : {datetime.now()}")


def thread_job(unit):
    unit.do_scraping()
    return unit


class MultiProcess(Process):
    """
        Threading module
        """
    def __init__(self, keyword, page_range, results, results_dict):
        super(MultiProcess, self).__init__()
        self.page_range = page_range
        self.keyword = keyword
        self.results = results
        self.results_dict = results_dict

    def run(self):
        print("Page range for this thread:", self.page_range, datetime.now())
        thread_count = 6
        for i in range(0, len(self.page_range), thread_count):
            threads = []
            for j in range(thread_count):
                if i + j < len(self.page_range):
                    unit = ScrapingUnit(keyword=self.keyword, page_number=self.page_range[i + j])
                    thread = ThreadWithReturnValue(target=thread_job, args=(unit,))
                    thread.start()
                    threads.append(thread)

            for thread in threads:
                obj = thread.join()
                if len(obj.results) > 0:
                    print("Before", obj.page_number, len(self.results), len(self.results_dict))
                    self.results += obj.results
                    self.results_dict += obj.results_dict
                    print("After", obj.page_number, len(self.results), len(self.results_dict))


def Scraping_Job(keyword):
    manager = Manager()
    results = manager.list()
    results_dict = manager.list()

    results.append([
        "Pubmed link", "Title", "Date", "Abstract", "Authors", "Author affiliation", "Author email", "PMCID", "DOI",
        "Full text link", "Mesh terms", "Publication type"
    ])

    print("Getting total count", datetime.now())
    total_count = 0
    unit = ScrapingUnit(keyword=keyword)
    unit.do_scraping()

    results += unit.results
    results_dict += unit.results_dict
    total_count += unit.total_count
    if total_count > 10000:
        total_count = 10000
    print(f"Total Count: {total_count}")
    print("END total count", datetime.now())

    threads = []
    # Thread count
    process_count = get_core_count()
    ranges = get_thread_range_pumbed(process_count=process_count, total_count=math.ceil(total_count/200))

    for page_range in ranges:
        if len(page_range):
            thread = MultiProcess(
                keyword=keyword,
                page_range=page_range,
                results=results,
                results_dict=results_dict
            )
            thread.start()
            threads.append(thread)

    for thread in threads:
        thread.join()

    file_name = secure_filename(keyword)
    file_name = file_name[:200]
    csv_obj = write_csv(results[:])
    excel_obj = excel_out(csv_obj)

    return results_dict[:], csv_obj, excel_obj, file_name
