from datetime import datetime
from urllib.parse import urlparse
import json


# Function to read a text file and return its content
def read_text_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return file.read()


# Function to read a JSON file and return its parsed content
def read_json_file(file_path):
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


# Function to extract domain from a given URL
def parse_domain(url):
    parsed_url = urlparse(url)
    return f"{parsed_url.scheme}://{parsed_url.netloc}/"


# Function to get the current timestamp as a formatted string
def get_timestamp_str():
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class FLywheelAnalysis:
    """
    A class to perform analysis on the Flywheel system.

    This class is responsible for processing crawled data, computing statistics,
    and generating analysis reports in a structured manner.
    """

    def __init__(
        self,
        initial_document_file_path,
        generated_queries_file_path,
        scraped_url_file_path,
        filtered_url_file_path,
        crawled_content_file_path,
        document_id=None,
    ):
        # Initialize the Flywheel Analysis with file paths and document ID
        self.id = document_id
        self.initial_document = self.get_initial_document(initial_document_file_path)
        self.generated_queries = self.get_generated_queries(generated_queries_file_path)
        self.scraped_urls = self.get_scraped_urls(scraped_url_file_path)
        self.filtered_urls = self.get_filtered_urls(filtered_url_file_path)
        self.crawled_content = self.get_crawled_content(crawled_content_file_path)

        self.url_data = self.get_url_data()

    @staticmethod
    def get_initial_document(initial_document_file_path):
        # Read and return the initial document content
        initial_document = read_text_file(initial_document_file_path)
        return initial_document

    def get_generated_queries(self, generated_query_file_path):
        # Read generated queries from a JSON file and store them as a set to avoid duplicates
        raw_content = read_json_file(generated_query_file_path)

        generated_queries = set()

        for task in raw_content:
            generated_queries.add(task["result"])

        return list(generated_queries)

    def get_scraped_urls(self, scraped_url_file_path):
        # Read scraped URLs and associate them with their corresponding queries
        raw_content = read_json_file(scraped_url_file_path)
        scraped_urls = {}

        for task in raw_content:
            if task["task"] in self.generated_queries:
                for url_info in task["result"]:
                    scraped_urls[url_info["url"]] = url_info
                    scraped_urls[url_info["url"]]["query"] = task["task"]

        return scraped_urls

    def get_filtered_urls(self, filtered_url_file_path):
        # Read filtered URLs and store them if they were scraped earlier
        raw_content = read_json_file(filtered_url_file_path)
        filtered_urls = []

        for task in raw_content:
            for url_info in task["result"]:
                if url_info["url"] in self.scraped_urls:
                    filtered_urls.append(url_info["url"])

        return filtered_urls

    def get_crawled_content(self, crawled_content_file_path):
        # Read crawled content and store crawl status and extracted content
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
        # Update crawl status for a given URL
        if url in self.crawled_content:
            url_data[url]["crawl_status"] = self.crawled_content[url]["crawl_status"]

            if url_data[url]["crawl_status"] == "SUCCESS":
                url_data[url]["context"] = self.crawled_content[url]["context"]

    def is_filtered(self, url):
        # Check if a URL was filtered
        return url in self.filtered_urls

    def get_url_data(self):
        # Gather URL data including filter status and crawl status
        url_data = {}

        for url in self.scraped_urls:
            url_data[url] = self.scraped_urls[url]
            url_data[url]["filter_status"] = self.is_filtered(url)

            if url_data[url]["filter_status"]:
                self.update_crawl_status(url_data, url)
        return url_data

    def get_rejected_urls(self):
        # Retrieve URLs that were scraped but not filtered for crawling
        return [url for url in self.scraped_urls if not self.is_filtered(url)]

    def get_domain_frequency_in_scraped_urls(self, domain):
        # Count how many times a domain appears in scraped URLs
        return sum(1 for url in self.scraped_urls if parse_domain(url) == domain)

    def get_domain_frequency_in_crawled_urls(self, domain):
        # Count how many times a domain appears in crawled URLs
        return sum(1 for url in self.crawled_content if parse_domain(url) == domain)

    def get_domain_frequency_failed_crawls(self, domain):
        # Count how many times a domain appears in failed crawls
        return sum(
            1
            for url in self.crawled_content
            if parse_domain(url) == domain
            and self.crawled_content[url]["crawl_status"] == "FAILED"
        )

    def generate_report(self):
        # Generate a comprehensive Flywheel data report
        separator = "=" * 90
        report = "\nFLYWHEEL DATA REPORT :=\n\n"
        report += f"{separator}\n\n"

        report += "STATISTICAL OVERVIEW:\n\n"
        report += self.get_stats_report()
        report += f"\n{separator}\n"

        return report


def test_result():
    # Define file paths for testing FlywheelAnalysis
    initial_document_file_path = "./flywheel/data/contexts/initial_context.txt"
    generated_queries_file_path = "./flywheel/data/queries/generated.json"
    scraped_url_file_path = "./flywheel/data/urls/scraped.json"
    filtered_url_file_path = "./flywheel/data/urls/filtered_urls.json"
    crawled_content_file_path = "./tests/data/load_balancer/test_flywheel/results.json"

    # Instantiate FlywheelAnalysis class
    analyzer = FLywheelAnalysis(
        initial_document_file_path,
        generated_queries_file_path,
        scraped_url_file_path,
        filtered_url_file_path,
        crawled_content_file_path,
    )

    # Generate and save the report
    report_output_file_path = (
        f"./analysis/reports/flywheel_report_{get_timestamp_str()}.txt"
    )

    with open(report_output_file_path, "w", encoding="utf-8") as file:
        file.write(analyzer.generate_report())
