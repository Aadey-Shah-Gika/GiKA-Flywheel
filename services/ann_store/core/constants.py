DEFAULT_FAISS_ANN_STORE_CONFIG = {
    "vector_dimension": 384,
    "nearest_neighbors": 2,
    "index": None,  # Faiss index object. Set in load_index() method.  # noqa: E501
    "similarity_threshold": 0.52,
}
