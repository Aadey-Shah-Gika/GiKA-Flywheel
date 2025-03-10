from .core.base_ann_store.main import BaseANNStore
from .core.faiss import FaissANNStore

#default model
ANNStore = FaissANNStore

__all__ = ['BaseANNStore', 'FaissANNStore', 'ANNStore']