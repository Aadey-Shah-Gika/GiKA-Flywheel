from sentence_transformers import SentenceTransformer

default_data_directory = "./flywheel/data/defaults/ann_store"

DEFAULT_ANN_STORE_CONFIG = {
    "model": SentenceTransformer("all-MiniLM-L12-v2"),
    "data_directory": default_data_directory,
    "csv_data_file_path": f"{default_data_directory}/encoded_data.csv",
    "index_file_path": f"{default_data_directory}/index_file.index",
    "encoded_csv_data": None  # DataFrame containing encoded data. Set in load_encoded_csv_data() method.  # noqa: E501
}
