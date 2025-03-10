# Discovery Flywheel

## Overview

The **Discovery Flywheel** is a system designed to collect publicly available world knowledge from the internet that is relevant to a given set of data and documents. It automates the process of query generation, URL discovery, content extraction, and summarization, creating an iterative knowledge refinement loop.

## Workflow

1. **Query Generation**: Generates queries based on input data and fires them on Google to discover relevant URLs.
2. **URL Filtering**: Evaluates discovered URLs for relevance using their snippet and title.
3. **Content Crawling & Parsing**: Crawls filtered URLs and extracts content.
4. **Summarization**: Summarizes extracted content to capture key insights.
5. **Iterative Process**: Uses summarized context as input for the next cycle to refine knowledge.
6. **Final Output**: Produces enriched and structured knowledge as the final dataset.

## System Architecture

The Discovery Flywheel leverages **multiprocessing and multithreading** to efficiently process tasks in parallel. It consists of the following modules:

### **1. Query Generator**

- Uses a **Task Queue** to manage incoming documents.
- A **Worker Process** generates queries using an **LLM**.

### **2. Search Engine Handling**

- Queries are processed using a **Load Balancer**.
- Multiple **Handler Ports** process search requests concurrently using **Threads**.
- **Tor circuits** ensure anonymity and prevent rate limiting.

### **3. URL Filtering**

- A **Nearest Neighbor (ANN) Store** filters URLs based on relevance.
- Filtering is performed using multiple processes for efficiency.

### **4. Crawler and Parser**

- **Multithreaded Crawlers** fetch URLs and extract content.
- A **Task Management Queue** tracks pending and completed tasks.
- Extracted data is summarized using an **LLM**.

## Code Workflow

### **Query Generator**

1. Retrieve input tasks from the **Task Queue**.
2. Collect tasks until the queue is empty or enough for batching.
3. Construct an **LLM prompt** for query generation.
4. Send the prompt to the **LLM Manager**.
5. Receive generated queries and submit them for further processing.

### **Search Engine Handling**

1. Process search queries using **Google Search API** with a **Tor proxy**.
2. If a port exceeds its limit, renew the **Tor identity**.
3. Implement a delay to avoid search engine rate limits.
4. Submit successfully fetched URLs for further processing.

### **URL Filtering**

1. Preprocess URL data and normalize it.
2. Transform URL text for **ANN Search**.
3. Retrieve **nearest title and snippet** from the **ANN Store**.
4. If the **similarity score** is above the threshold, add the URL to the **ANN Store** and submit it for crawling.

### **Crawler and Parser**

1. Fetch URLs from the **Filtered Queue**.
2. Discard blocked domains.
3. Enqueue URLs for crawling via **Crawler Service**.
4. Send URL info to the **Collector Process**.
5. **Collector Process** stores crawled content and adds new URLs for further crawling.
6. Continuously monitor crawl status.
7. Summarize crawled content using **LLM**.
8. Store summaries in the **Context Queue** for the next iteration.

### **ANN Store Service**

1. **Index Data**: Converts text to embeddings via **sentence transformers** and stores it in **FAISS Index**.
2. **ANN Search**: Retrieves the nearest neighbor if the similarity is above the threshold.

## Usage Guidelines

### **1. Clone the GitHub Repository**

```sh
 git clone https://github.com/knowledge-hive/Flywheel.git
```

### **2. Navigate to the Project Directory**

```sh
cd Flywheel
```

### **3. Switch to the `dev-code-backup` Branch**

```sh
git checkout dev-code-backup
```

### **4. Install Dependencies**

```sh
pip install -r requirements.txt
```

### **5. Provide Initial Context**

Paste the initial context in the `initial_document.txt` file.

### **6. Start the Flywheel**

```sh
python main.py
```
