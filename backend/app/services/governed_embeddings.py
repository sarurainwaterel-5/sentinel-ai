"""Bounded offline embedding adapter; deployment must attest its model policy.

A supplied policy hash is configuration identity, not weight-file verification.
No provider credentials, automatic download or fallback is provided here.
"""
import math

class GovernedEmbeddingAdapter:
    def __init__(self, *, backend, dimension, policy_sha256):
        if type(dimension) is not int or not 1 <= dimension <= 4096:
            raise ValueError('invalid_embedding_dimension')
        if (type(policy_sha256) is not str or len(policy_sha256)!=64
                or any(c not in '0123456789abcdef' for c in policy_sha256)):
            raise ValueError('explicit_embedding_policy_required')
        self._backend=backend
        self.dimension=dimension
        self.policy_sha256=policy_sha256
        self.model_name=backend.get_model_name()
        if type(self.model_name) is not str or not self.model_name.strip() or len(self.model_name)>200:
            raise ValueError('explicit_model_name_required')

    def embed(self, texts):
        if type(texts) not in (tuple,list) or not 1 <= len(texts) <= 32:
            raise ValueError('bounded_embedding_batch_required')
        if any(type(text) is not str or not text or len(text.encode('utf-8'))>65536 for text in texts):
            raise ValueError('invalid_embedding_text')
        if self._backend.get_model_name()!=self.model_name or self._backend.get_dimension()!=self.dimension:
            raise ValueError('embedding_configuration_changed')
        vectors=self._backend.generate_embeddings(list(texts))
        if type(vectors) is not list or len(vectors)!=len(texts):
            raise ValueError('embedding_batch_mismatch')
        result=[]
        for vector in vectors:
            if type(vector) not in (list,tuple) or len(vector)!=self.dimension:
                raise ValueError('embedding_dimension_mismatch')
            if any(type(v) not in (int,float) or not math.isfinite(v) for v in vector):
                raise ValueError('invalid_embedding_value')
            if not any(v!=0 for v in vector): raise ValueError('zero_embedding')
            result.append([float(v) for v in vector])
        if self._backend.get_model_name()!=self.model_name or self._backend.get_dimension()!=self.dimension:
            raise ValueError('embedding_configuration_changed')
        return result
