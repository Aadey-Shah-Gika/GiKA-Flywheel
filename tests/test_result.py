from datetime import datetime
from urllib.parse import urlparse
import json


def read_text_file(file_path):
    """
    Read the content of a text file and return it as a string.

    Parameters:
    file_path (str): The path to the text file to be read.

    Returns:
    str: The content of the text file.

    Raises:
    FileNotFoundError: If the specified file_path does not exist.
    PermissionError: If the program does not have permission to read the file.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


def read_json_file(file_path):
    """
    Read and parse a JSON file.

    Parameters:
    file_path (str): The path to the JSON file to be read.

    Returns:
    dict: The parsed JSON data from the file.

    Raises:
    FileNotFoundError: If the specified file_path does not exist.
    json.JSONDecodeError: If the file contains invalid JSON data.
    """
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def parse_domain(url):
    """
    Parse and extract the domain from a given URL.

    Parameters:
    url (str): The URL from which to extract the domain.

    Returns:
    str: The extracted domain, including the scheme (e.g., http, https) and the network location.

    Example:
    >>> parse_domain("https://www.example.com/path/page.html")
    "https://www.example.com/"
    """
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}/"


def get_timestamp_str():
    """
    Generate a timestamp string in the format 'YYYY-MM-DD HH:MM:SS'.

    Parameters:
    None

    Returns:
    str: A timestamp string in the format 'YYYY-MM-DD HH:MM:SS'.
    """
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class FLywheelAnalysis:
    """
    A class to perform analysis on the Flywheel system.

    This class is responsible for processing crawled data, computing statistics,
    and generating analysis reports in a structured manner.
    """

    # Initialize the Flywheel Analysis with file paths and document ID
    def __init__(
        self,
        initial_document_file_path,
        generated_queries_file_path,
        scraped_url_file_path,
        filtered_url_file_path,
        crawled_content_file_path,
        document_id=None,
    ):
        self.id = document_id
        self.initial_document = self.get_initial_document(initial_document_file_path)
        self.generated_queries = self.get_generated_queries(generated_queries_file_path)
        self.scraped_urls = self.get_scraped_urls(scraped_url_file_path)
        self.filtered_urls = self.get_filtered_urls(filtered_url_file_path)
        self.crawled_content = self.get_crawled_content(crawled_content_file_path)

        self.url_data = self.get_url_data()

    @staticmethod
    def get_initial_document(initial_document_file_path):
        """
        Read and return the initial document content from the specified file path.

        Parameters:
        initial_document_file_path (str): The file path of the initial document.

        Returns:
        str: The content of the initial document.
        """
        initial_document = read_text_file(initial_document_file_path)
        return initial_document

    def get_generated_queries(self, generated_query_file_path):
        """
        Read and return the generated queries from the specified JSON file.

        Parameters:
        generated_query_file_path (str): The file path of the JSON file containing the generated queries.

        Returns:
        list: A list of unique generated queries.
        """
        raw_content = read_json_file(generated_query_file_path)

        generated_queries = set()

        for task in raw_content:
            generated_queries.add(task["result"])

        return list(generated_queries)

    def get_scraped_urls(self, scraped_url_file_path):
        """
        Read and return the scraped URLs from the specified JSON file.

        Parameters:
        scraped_url_file_path (str): The file path of the JSON file containing the scraped URLs.

        Returns:
        dict: A dictionary where the keys are the scraped URLs and the values are dictionaries containing
              the URL information and the corresponding query.
        """
        raw_content = read_json_file(scraped_url_file_path)
        scraped_urls = {}

        for task in raw_content:
            if task["task"] in self.generated_queries:
                for url_info in task["result"]:
                    scraped_urls[url_info["url"]] = url_info
                    scraped_urls[url_info["url"]]["query"] = task["task"]

        return scraped_urls

    def get_filtered_urls(self, filtered_url_file_path):
        """
        Read and return the filtered URLs from the specified JSON file.

        Parameters:
        filtered_url_file_path (str): The file path of the JSON file containing the filtered URLs.

        Returns:
        list: A list of filtered URLs.
        """
        raw_content = read_json_file(filtered_url_file_path)
        filtered_urls = []

        for task in raw_content:
            for url_info in task["result"]:
                if url_info["url"] in self.scraped_urls:
                    filtered_urls.append(url_info["url"])

        return filtered_urls

    def get_crawled_content(self, crawled_content_file_path):
        """
        Read and return the crawled content from the specified JSON file.

        Parameters:
        crawled_content_file_path (str): The file path of the JSON file containing the crawled content.

        Returns:
        dict: A dictionary where the keys are the filtered URLs and the values are dictionaries containing
              the crawled content and the corresponding crawl status.
        """
        raw_content = read_json_file(crawled_content_file_path)
        crawled_content = {}

        for task in raw_content:
            if task["task"] in self.filtered_urls:
                crawled_content[task["task"]] = {
                    "context": task["result"],
                    "crawl_status": task["status"],
                }

        return crawled_content

    def update_crawl_status(self, url_data, url):
        """
        Update the crawl status and crawled content of a URL in the provided dictionary.

        Parameters:
        url_data (dict): A dictionary containing URL information.
        url (str): The URL for which the crawl status needs to be updated.

        Returns:
        None. The function updates the provided dictionary in-place.
        """
        if url in self.crawled_content:
            url_data[url]["crawl_status"] = self.crawled_content[url]["crawl_status"]

            if url_data[url]["crawl_status"] == "SUCCESS":
                url_data[url]["context"] = self.crawled_content[url]["context"]

    def is_filtered(self, url):
        """
        Check if a given URL is in the list of filtered URLs.

        Parameters:
        url (str): The URL to be checked.

        Returns:
        bool: True if the URL is in the filtered URLs list, False otherwise.
        """
        return url in self.filtered_urls

    def get_url_data(self):
        """
        Generate a dictionary containing URL information, filter status, crawled content and crawl status.

        Parameters:
        None

        Returns:
        dict: A dictionary where the keys are the scraped URLs and the values are dictionaries containing
              the URL information, filter status, crawled content and crawl status.
        """
        url_data = {}

        for url in self.scraped_urls:
            url_data[url] = self.scraped_urls[url]
            url_data[url]["filter_status"] = self.is_filtered(url)

            if url_data[url]["filter_status"]:
                self.update_crawl_status(url_data, url)
        return url_data

    def get_rejected_urls(self):
        """
        Get a list of URLs that were rejected during the filtering process.

        Parameters:
        None

        Returns:
        list: A list of rejected URLs.
        """
        rejected_urls = []
        for url in self.scraped_urls:
            if not self.is_filtered(url):
                rejected_urls.append(url)
        return rejected_urls

    def get_domain_frequency_in_scraped_urls(self, domain):
        """
        Get the frequency of a specific domain in the scraped URLs.

        Parameters:
        domain (str): The domain for which the frequency needs to be calculated.

        Returns:
        int: The frequency of the domain in the scraped URLs.
        """
        frequency = 0
        for url in self.scraped_urls:
            if parse_domain(url) == domain:
                frequency += 1
        return frequency

    def get_domain_frequency_in_crawled_urls(self, domain):
        """
        Get the frequency of a specific domain in the crawled URLs.

        Parameters:
        domain (str): The domain for which the frequency needs to be calculated.

        Returns:
        int: The frequency of the domain in the crawled URLs.
        """
        frequency = 0
        for url in self.crawled_content:
            if parse_domain(url) == domain:
                frequency += 1
        return frequency

    def get_domain_frequency_failed_crawls(self, domain):
        """
        Get the frequency of a specific domain in the crawled URLs that failed.

        Parameters:
        domain (str): The domain for which the frequency needs to be calculated.

        Returns:
        int: The frequency of the domain in the crawled URLs that failed.
        """
        frequency = 0
        for url in self.crawled_content:
            if (
                parse_domain(url) == domain
                and self.crawled_content[url]["crawl_status"] == "FAILED"
            ):
                frequency += 1
        return frequency

    def get_crawled_domains(self):
        """
        Get a list of unique domains from the crawled URLs.

        Parameters:
        None

        Returns:
        list: A list of unique domains from the crawled URLs.
        """
        domains = set()

        for url in self.crawled_content:
            domain = parse_domain(url)
            domains.add(domain)

        return list(domains)

    def get_domain_stats(self, domain):
        """
        Calculate and return statistics for a specific domain.

        Parameters:
        domain (str): The domain for which the statistics need to be calculated.

        Returns:
        dict: A dictionary containing the domain, total scraped URLs, total successful crawled URLs,
              total failed crawled URLs, filter rejected percentage, and failure percentage.
        """
        total_urls_scraped = self.get_domain_frequency_in_scraped_urls(domain)

        total_urls_crawled = self.get_domain_frequency_in_crawled_urls(domain)
        failed_urls_crawled = self.get_domain_frequency_failed_crawls(domain)
        successful_urls_crawled = total_urls_crawled - failed_urls_crawled

        filter_rejected_percentage = 100 * (
            (total_urls_scraped - total_urls_crawled) / total_urls_scraped
        )
        failure_percentage = 100 * (failed_urls_crawled / total_urls_crawled)

        return {
            "domain": domain,
            "scraped": total_urls_scraped,
            "success": successful_urls_crawled,
            "failed": failed_urls_crawled,
            "rejected_percentage": filter_rejected_percentage,
            "failure_percentage": failure_percentage,
        }

    def get_crawled_domains_info(self):
        """
        Get a list of dictionaries containing statistics for each domain in the crawled URLs.

        Parameters:
        None

        Returns:
        list: A list of dictionaries, where each dictionary contains statistics for a domain.
              The dictionary keys include 'domain', 'scraped', 'success', 'failed',
              'rejected_percentage', and 'failure_percentage'.
        """
        failed_domain_info = []

        domains = self.get_crawled_domains()

        for domain in domains:
            failed_domain_info.append(self.get_domain_stats(domain))

        return failed_domain_info

    def get_failed_crawl_domain_by_percentage(self):
        """
        Get a list of dictionaries containing statistics for each domain in the crawled URLs,
        sorted in descending order of failure percentage.

        Parameters:
        None

        Returns:
        list: A list of dictionaries, where each dictionary contains statistics for a domain.
              The dictionary keys include 'domain', 'scraped', 'success', 'failed',
              'rejected_percentage', and 'failure_percentage'. The list is sorted in descending
              order of failure percentage.
        """
        domain_info = self.get_crawled_domains_info()

        # * Sort the domain in descending order of failure percentage
        domain_info.sort(key=lambda x: x["failure_percentage"], reverse=True)

        return domain_info

    def get_domain_crawled_by_frequency(self):
        """
        Get a list of dictionaries containing statistics for each domain in the crawled URLs,
        sorted in descending order of the total number of crawled URLs.

        Parameters:
        None

        Returns:
        list: A list of dictionaries, where each dictionary contains statistics for a domain.
              The dictionary keys include 'domain', 'scraped', 'success', 'failed',
              'rejected_percentage', and 'failure_percentage'. The list is sorted in descending
              order of the total number of crawled URLs.
        """
        domain_info = self.get_crawled_domains_info()

        # * Sort the domain in descending order of total crawled urls
        domain_info.sort(key=lambda x: x["success"] + x["failed"], reverse=True)

        return domain_info

    def get_rejected_urls_info(self):
        """
        Get a list of dictionaries containing information for each rejected URL.

        Parameters:
        None

        Returns:
        list: A list of dictionaries, where each dictionary contains information for a rejected URL.
              The dictionary keys include 'url', 'query' and 'filter_status'.
        """
        rejected_urls_info = []

        for url in self.get_rejected_urls():
            rejected_urls_info.append(self.url_data[url])

        return rejected_urls_info

    def get_url_info(self, url):
        """
        Retrieve the information for a specific URL from the analysis data.

        Parameters:
        url (str): The URL for which the information needs to be retrieved.

        Returns:
        dict: A dictionary containing the information for the specified URL.
        """
        return self.url_data[url]

    def get_url_info_str(self, url):
        """
        Generate a formatted string containing information about a specific URL.

        Parameters:
        url (str): The URL for which the information needs to be retrieved.

        Returns:
        str: A formatted string containing information about the specified URL.
             The string includes details such as the URL, query, filter status,
             crawl status. EXCEPT: Crawled content
        """
        info_str = ""
        url_info = self.get_url_info(url)

        for attributes in url_info:
            if attributes == "context":
                continue
            info_str += f"\t\t{attributes.upper()}:\n\t\t\t\t{url_info[attributes]}\n\n"

        return info_str

    def get_total_generated_queries(self):
        """
        Get the total number of generated queries.

        Parameters:
        None

        Returns:
        int: The total number of generated queries.
        """
        return len(self.generated_queries)

    def get_total_urls_scraped(self):
        """
        Get the total number of URLs scraped

        Parameters:
        None

        Returns:
        int: The total number of URLs scraped.
        """
        return len(self.scraped_urls)

    def get_total_urls_rejected(self):
        """
        Get the total number of URLs rejected during the filtering process.

        Parameters:
        None

        Returns:
        int: The total number of rejected URLs.
        """
        return len(self.get_rejected_urls())

    def get_total_crawled_urls(self):
        """
        Get the total number of URLs that were successfully crawled.

        Parameters:
        None

        Returns:
        int: The total number of successfully crawled URLs.
        """
        return sum(
            1
            for url in self.url_data
            if self.url_data[url].get("crawl_status") == "SUCCESS"
        )

    def get_total_failed_crawled_urls(self):
        """
        Calculate and return the total number of URLs that failed during crawling.

        Parameters:
        None

        Returns:
        int: The total number of URLs that failed during crawling.
        """
        return sum(
            1
            for url in self.url_data
            if self.url_data[url].get("crawl_status") == "FAILED"
        )

    def get_stats_report(self):
        """
        Generate a report containing various statistics related to the analysis.

        Parameters:
        None

        Returns:
        str: A formatted string containing the total number of generated queries,
             the total number of URLs scraped, the total number of rejected URLs,
             the total number of successfully crawled URLs, and the total number of
             URLs that failed during crawling.
        """
        stats_report = (
            f"Total generated queries: {self.get_total_generated_queries()}\n"
        )
        stats_report += (
            f"Total urls searched(google): {self.get_total_urls_scraped()}\n"
        )
        stats_report += f"Total urls rejected: {self.get_total_urls_rejected()}\n"
        stats_report += f"Total urls crawled success: {self.get_total_crawled_urls()}\n"
        stats_report += (
            f"Total urls crawled failed: {self.get_total_failed_crawled_urls()}\n"
        )
        return stats_report

    def get_url_wise_report(self):
        """
        Generate a report containing detailed information for each URL in the analysis data.

        Parameters:
        None

        Returns:
        str: A formatted string containing detailed information for each URL.
             The string includes the URL, query, filter status and crawl status.

        """
        url_wise_report = ""

        separator = "-" * 70
        counter = 1
        for url in self.url_data:
            url_wise_report += f"\n\n[{counter}]\n"
            url_wise_report += self.get_url_info_str(url) + "\n"
            url_wise_report += separator + "\n\n"
            counter += 1

        return url_wise_report

    def get_query_generation_report(self):
        """
        Generate a report containing all the generated queries.

        Parameters:
        None

        Returns:
        str: A formatted string containing the generated queries. Each query is numbered
             and separated by a newline character.

        """
        query_generation_report = ""
        counter = 1
        for query in self.generated_queries:
            query_generation_report += f"[{counter}] {query}\n\n"
            counter += 1

        return query_generation_report

    def get_initial_document_report(self):
        """
        Generate a report containing the initial document content.

        Parameters:
        None

        Returns:
        str: A formatted string containing the initial document content.

        The initial document content is retrieved from the 'initial_document' attribute of the class instance.
        """
        initial_document_report = f"{self.initial_document}\n\n"
        return initial_document_report

    def get_rejected_urls_report(self, limit=None):
        """
        Generate a report containing detailed information for each rejected URL.

        Parameters:
        limit (int, optional): The maximum number of rejected URLs to include in the report.
                               If not provided, all rejected URLs will be included.

        Returns:
        str: A formatted string containing detailed information for each rejected URL.
             The string includes the URL, query, filter status, and crawl status.
             Each rejected URL is separated by a separator line.
        """
        rejected_urls_report = ""

        rejected_urls = self.get_rejected_urls()

        if isinstance(limit, int) and limit < len(rejected_urls):
            rejected_urls = rejected_urls[:limit]

        separator = "-" * 80
        counter = 1
        for url in rejected_urls:
            rejected_urls_report += f"[{counter}]\n\n"
            rejected_urls_report += f"{self.get_url_info_str(url)}\n"
            rejected_urls_report += f"\n{separator}\n\n"
            counter += 1

        return rejected_urls_report

    def get_failed_crawl_domain_report(self):
        """
        Generate a report containing information about domains with the highest crawling failure percentage.

        Returns:
        str: A formatted string containing information about the domains. Each domain is separated by a separator line.
             The string includes the domain name, crawling failure percentage, number of unsuccessful crawls,
             number of successful crawls, and filter rejected percentage.
        """
        failed_crawl_domain_report = ""

        separator = "-" * 80

        failed_domain_info = self.get_failed_crawl_domain_by_percentage()

        counter = 1
        for domain in failed_domain_info:
            failed_crawl_domain_report += f"[{counter}] {domain['domain']}\n\n"
            failed_crawl_domain_report += (
                f"\tCrawling Failure Percentage: {domain['failure_percentage']}%\n\n"
            )
            failed_crawl_domain_report += (
                f"\tUnsuccessful crawls: {domain['failed']}\n\n"
            )
            failed_crawl_domain_report += (
                f"\tSuccessful crawls: {domain['success']}\n\n"
            )
            failed_crawl_domain_report += (
                f"\tFilter Rejected Percentage: {domain['rejected_percentage']}%\n\n"
            )
            failed_crawl_domain_report += f"{separator}\n\n"
            counter += 1

        return failed_crawl_domain_report

    def get_crawled_content_report(self):
        """
        Generate a report containing the crawled content of successfully crawled URLs.

        Returns:
        str: A formatted string containing the crawled content of successfully crawled URLs.
             Each URL is separated by a separator line. The string includes the URL, query,
             filter status, crawl status, and the crawled content.
        """
        crawled_content_report = ""
        separator = "-" * 70
        for url in self.crawled_content:
            if self.url_data[url]["crawl_status"] == "SUCCESS":
                crawled_content_report += f"{self.get_url_info_str(url)}\n\n"
                crawled_content_report += "CONTEXT:\n\n"
                crawled_content_report += f"{self.url_data[url]['context'][0]}\n\n"
                crawled_content_report += f"{separator}\n\n"
        return crawled_content_report

    def generate_report(self):
        """
        Generate a comprehensive report containing various statistics and detailed information about the analysis.

        Returns:
        str: A formatted string containing the report. The report includes sections such as statistical overview,
             initial document, generated queries, rejected URLs, domains with high crawling failure percentage,
             crawled content, and URL-wise report.
        """
        separator = "=" * 90
        report = "\nFLYWHEEL DATA REPORT :=\n\n"
        report += f"{separator}\n\n"

        report += "STATISTICAL OVERVIEW:\n\n"
        report += self.get_stats_report()
        report += f"\n{separator}\n"

        report += "\n\nINITIAL DOCUMENT:\n\n"
        report += self.get_initial_document_report()
        report += f"\n{separator}\n"

        report += "\n\nGENERATED QUERIES:\n\n"
        report += self.get_query_generation_report()
        report += f"\n{separator}\n"

        report += "\n\nSOME REJECTED URLS:\n\n"
        report += self.get_rejected_urls_report(10)
        report += f"\n{separator}\n"

        report += "\n\nDOMAIN FAILED AT CRAWLING:\n\n"
        report += self.get_failed_crawl_domain_report()
        report += f"\n{separator}\n"

        report += "\n\nCRAWLED CONTENT:\n\n"
        report += self.get_crawled_content_report()
        report += f"\n{separator}\n"

        report += "\n\nURL WISE REPORT:\n\n"
        report += self.get_url_wise_report()
        report += f"\n{separator}\n"

        return report


def test_result():
    """
    This function initializes a FLywheelAnalysis instance with provided file paths,
    generates a comprehensive report, and writes the report to a specified output file.

    Parameters:
    initial_document_file_path (str): The file path to the initial document content.
    generated_queries_file_path (str): The file path to the generated queries.
    scraped_url_file_path (str): The file path to the scraped URLs.
    filtered_url_file_path (str): The file path to the filtered URLs.
    crawled_content_file_path (str): The file path to the crawled content.

    Returns:
    None. The function writes the report to a specified output file.
    """
    initial_document_file_path = "./flywheel/data/contexts/initial_context.txt"
    generated_queries_file_path = "./flywheel/data/queries/generated.json"
    scraped_url_file_path = "./flywheel/data/urls/scraped.json"
    filtered_url_file_path = "./flywheel/data/urls/filtered_urls.json"
    crawled_content_file_path = "./tests/data/load_balancer/test_flywheel/results.json"

    analyzer = FLywheelAnalysis(
        initial_document_file_path,
        generated_queries_file_path,
        scraped_url_file_path,
        filtered_url_file_path,
        crawled_content_file_path,
    )

    report_output_file_path = (
        f"./analysis/reports/flywheel_report_{get_timestamp_str()}.txt"
    )

    with open(report_output_file_path, "w", encoding="utf-8") as file:
        file.write(analyzer.generate_report())
