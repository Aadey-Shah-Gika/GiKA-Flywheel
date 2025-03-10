import logging
from flask import Flask, request, jsonify
from concurrent.futures import ThreadPoolExecutor

from .core.faiss import FaissANNStore
from .constants import DEFAULT_PORT, ANN_STORE_CONFIGS

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

# * Global ANN Store configuration
GlobalAnnStores = {}

def init_global_ann_store():
    """
    Initialize global Approximate Nearest Neighbor (ANN) stores.
    This function iterates over predefined ANN store configurations and initializes them.
    """
    for ann_store_name, config in ANN_STORE_CONFIGS.items():
        ann_store = FaissANNStore(**config)
        GlobalAnnStores[ann_store_name] = ann_store
    logger.info("Global ANN stores initialized successfully.")

def add_data_async(store_name: str, data):
    """
    Adds data to the specified ANN store asynchronously.
    
    Args:
        store_name (str): The name of the ANN store.
        data (list or any): Data to be added. If a single item is provided, it is wrapped in a list.
    """
    if store_name in GlobalAnnStores:
        if not isinstance(data, list):
            data = [data]  # Ensure data is in list format
        GlobalAnnStores[store_name].add(data)
        logger.info(f"Data successfully added to store: {store_name}")
    else:
        logger.error(f"Failed to add data: Store {store_name} does not exist.")

def get_nearest_neighbor(store_name: str, query, k: int):
    """
    Finds the k-nearest neighbors for a given query in the specified ANN store.
    
    Args:
        store_name (str): The name of the ANN store.
        query (any): The query vector.
        k (int): The number of nearest neighbors to retrieve.
    
    Returns:
        list: A list of nearest neighbors or an empty list if the store does not exist.
    """
    if store_name in GlobalAnnStores:
        return GlobalAnnStores[store_name].search_similar_items([query], k)
    logger.error(f"Failed to search: Store {store_name} does not exist.")
    return []

# * Flask Configuration
app = Flask(__name__)

# Thread pool executor for handling background tasks
executor = ThreadPoolExecutor(max_workers=1)  # Adjust based on system capacity

@app.route("/<store_name>/add", methods=["POST"])
def add_to_store(store_name):
    """
    API endpoint to add data to an ANN store.
    
    Args:
        store_name (str): The name of the ANN store.
    
    Request JSON:
        {
            "data": [...]  # List of data points to be added
        }
    
    Returns:
        JSON response with status message.
    """
    if store_name not in GlobalAnnStores:
        logger.error(f"Add request failed: Store {store_name} not found.")
        return jsonify({"message": f"Error: {store_name} not found.", "status": "error"}), 404

    raw_data = request.get_json()
    data = raw_data.get("data", [])

    try:
        executor.submit(add_data_async, store_name, data)
        logger.info(f"Add request processed successfully for store: {store_name}")
    except Exception as e:
        logger.exception("Error occurred while adding data asynchronously.")
        return jsonify({"message": "Internal server error", "status": "error"}), 500

    return jsonify({"message": "Successfully added", "status": "success"}), 200

@app.route("/<store_name>/nearest_neighbor", methods=["POST"])
def find_nearest_neighbor(store_name):
    """
    API endpoint to find the nearest neighbors for a given query in an ANN store.
    
    Args:
        store_name (str): The name of the ANN store.
    
    Request JSON:
        {
            "query": ...,  # Query vector
            "k": 5         # Number of neighbors to retrieve
        }
    
    Returns:
        JSON response containing nearest neighbors or an error message.
    """
    if store_name not in GlobalAnnStores:
        logger.error(f"Search request failed: Store {store_name} not found.")
        return jsonify({"message": f"Error: {store_name} not found.", "status": "error"}), 404
    
    data = request.get_json()
    query = data.get("query")
    k = data.get("k")

    if query is None or k is None:
        logger.error("Search request failed: Missing required parameters.")
        return jsonify({"message": "Missing required parameters: 'query' and 'k'.", "status": "error"}), 400
    
    try:
        result = get_nearest_neighbor(store_name, query, k)
        logger.info(f"Search successful for store: {store_name}, Query: {query}")
    except Exception as e:
        logger.exception("Error occurred while searching nearest neighbors.")
        return jsonify({"message": "Error: Failed to find nearest neighbor.", "status": "error"}), 500
    
    return jsonify({"data": result, "status": "success"}), 200

if __name__ == "__main__":
    init_global_ann_store()  # Initialize ANN stores when the application starts
    app.run(debug=False, port=DEFAULT_PORT)