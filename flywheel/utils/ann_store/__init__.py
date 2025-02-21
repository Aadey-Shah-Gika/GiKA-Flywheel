from .main import BaseANNStore
from .faiss.main import FaissANNStore

#default model
ANNStore = FaissANNStore

__all__ = ['BaseANNStore', 'FaissANNStore', 'ANNStore']