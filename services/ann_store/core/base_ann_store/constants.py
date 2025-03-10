from sentence_transformers import SentenceTransformer

default_data_directory = "./data/default/index/"

DEFAULT_ANN_STORE_CONFIG = {
    "model": SentenceTransformer("all-MiniLM-L12-v2"),
    "index_file_path": f"{default_data_directory}/index_file.bin",
}
