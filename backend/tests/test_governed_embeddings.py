import pytest
from app.services.governed_embeddings import GovernedEmbeddingAdapter

class Backend:
    name='explicit-local-model';dimension=3
    def get_model_name(self):return self.name
    def get_dimension(self):return self.dimension
    def generate_embeddings(self,texts):return [[1,0,.5] for _ in texts]

def adapter(backend=None):return GovernedEmbeddingAdapter(backend=backend or Backend(),dimension=3,policy_sha256='a'*64)

def test_preserves_batch_and_pins_dimension_and_policy():
    a=adapter(); assert a.embed(['one','two'])==[[1.,0.,.5],[1.,0.,.5]]
    assert a.policy_sha256=='a'*64 and a.model_name=='explicit-local-model'

@pytest.mark.parametrize('texts',[[],['x']*33,[''],[None],['x'*65537]])
def test_bounded_inputs(texts):
    with pytest.raises(ValueError):adapter().embed(texts)

@pytest.mark.parametrize('vectors',[[[1]],[[True,0,1]],[[float('nan'),1,1]],[[0,0,0]],[],[[1,2,3],[1,2,3]]])
def test_malformed_backend_output_rejected(vectors):
    b=Backend();b.generate_embeddings=lambda _:vectors
    with pytest.raises(ValueError):adapter(b).embed(['one'])

def test_model_rotation_during_encode_denies():
    b=Backend()
    def encode(_):b.name='changed';return [[1,0,.5]]
    b.generate_embeddings=encode
    with pytest.raises(ValueError,match='configuration_changed'):adapter(b).embed(['one'])
