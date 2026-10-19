MODEL_ID = 'selimsef-dfdc-efficientnet-b7-final-777-facetorch'
REPO = 'tomas-gajarsky/facetorch-deepfake-efficientnet-b7'
REVISION = '4acc494f37eb63d7457166eff2acb45c5b04b9a6'
FILENAME = 'model.pt'
CHECKSUM = 'e36197ae83fa7c050e8ceba267a1f028f2d74d8ad805bf5d5037a26e8ca96c13'
PREPROCESSING = 'dfdc-mtcnn-rgb-thirds-isotropic-pad380-imagenet-v1'


def metadata():
    return {'identifier': MODEL_ID, 'repository': REPO, 'revision': REVISION,
            'checkpoint_sha256': CHECKSUM, 'preprocessing_version': PREPROCESSING,
            'license': 'MIT', 'device': 'cpu', 'input': 'single face frame',
            'output_mapping': 'sigmoid(single logit), higher = fake'}
