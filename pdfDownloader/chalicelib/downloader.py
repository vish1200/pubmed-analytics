import requests
from .helpers import contains_nihgov, parse_urls, get_nihgov_url, get_unique_id_from_url
from .sites import NIHGov
from .helpers import retry


class Downloader:
    def __init__(self, data, download_dir):
        self.data = data
        self.headers = {
            "user-agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/86.0.4240.75 Safari/537.36"
        }
        self.url_resolver_session = requests.session()
        self.url_resolver_session.headers.update(self.headers)
        self.pdf_objects = []
        self.download_dir = download_dir
        print("Thread Data Count", len(self.data))

    # def get_fulltext_urls(self):
    #     data = self.get_data()
    #     return data['Full text link']

    def run(self):
        data = self.data
        for idx in range(len(data)):
            row = data[idx]
            url_list = row['full_text_links']
            pubmed_link = row['Pubmed link']
            print("Started: ", row['no'])
            data[idx]['PDFDownloaded'] = False

            try:
                unique_pdf_id = get_unique_id_from_url(pubmed_link) + ".pdf"
                if not isinstance(url_list, str) or url_list is None:
                    continue
                parsed_list = parse_urls(url_list)
                if contains_nihgov(parsed_list):
                    try:
                        nihgov_obj = NIHGov(get_nihgov_url(parsed_list), self.download_dir, unique_pdf_id)
                        filename, pdf_obj = nihgov_obj.start_scrape()
                        if pdf_obj:
                            data[idx]['PDFDownloaded'] = filename
                            print(filename, "Source: NIHGov", row['no'])
                            self.pdf_objects.append({
                                "filename": filename,
                                "obj": pdf_obj
                            })
                    except Exception as e:
                        print(e)
                else:
                    for url in parsed_list:
                        if not isinstance(url, str):
                            continue
                        if "http" not in url:
                            continue
                        resolved_url = url_resolver(url, self.url_resolver_session)
                        if resolved_url:
                            if "doi" in resolved_url:
                                resolved_url = url_resolver(resolved_url, self.url_resolver_session)
                        url_class = url_classifier(resolved_url)
                        if resolved_url != url:
                            print("Resolved url: %s -> %s" % (url, resolved_url))
                        if url_class:
                            try:
                                klass = url_class(resolved_url, self.download_dir, unique_pdf_id)
                                filename, pdf_obj = klass.start_scrape()

                                if pdf_obj:
                                    data[idx]['PDFDownloaded'] = filename
                                    print(filename, "Source: %s" % type(klass).__name__, row['no'])
                                    self.pdf_objects.append({
                                        "filename": filename,
                                        "obj": pdf_obj
                                    })
                            except Exception as e:
                                print(e)
                print("Ended: ", row['no'])
            except Exception as e:
                print(e)

        return self.pdf_objects, data


def url_classifier(url):
    if not url:
        return False
    if "eprints.whiterose.ac.uk" in url:
        from .sites import WhiteRose
        return WhiteRose
    if "iris.unito.it" in url:
        from .sites import UnitoIt
        return UnitoIt
    if "academic.oup" in url:
        from .sites import OUP
        return OUP
    if "ajmc.com" in url:
        from .sites import AJMC
        return AJMC
    if "nature.com" in url:
        from .sites import Nature
        return Nature
    if "bmj.com" in url:
        from .sites import BMJ
        return BMJ
    if "biologists.org" in url:
        from .sites import Biologists
        return Biologists
    if "karger.com" in url:
        from .sites import Karger
        return Karger
    if "wiley.com" in url:
        from .sites import Wiley
        return Wiley
    return False


@retry(Exception, tries=2, delay=0.5, backoff=1)
def url_resolver(url, session):
    if "hdl.handle.net" in url or "doi.org" in url or "doi.wiley.com" in url:
        location = session.head(url).headers.get('Location')
        if location:
            return location
        return False
    if "academic.oup.com" in url and "article-lookup" in url:
        location = session.head(url).headers.get('Location')
        if location:
            if "http" not in location:
                return "https://academic.oup.com" + location
            return location
        return False

    # if "doi" in url:
    #     return session.head(url).headers.get('Location')
    # try:
    #     location = session.head(url).headers.get('Location')
    #     if location:
    #         return location
    #     raise Exception
    # except Exception:
    return url
