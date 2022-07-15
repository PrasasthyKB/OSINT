import os
import torch
import numpy as np
import torch.nn as nn
import bentoml
from bentoml.frameworks.pytorch import PytorchModelArtifact
from bentoml.adapters import DataframeInput
from bentoml.service.artifacts.common import PickleArtifact
from transformers import AutoModel, BertTokenizerFast


@bentoml.env(
    pip_packages=['bentoml==0.13.1', 'transformers',
                  'iocextract', 'regex'])
@bentoml.env(pip_extra_index_url=['https://download.pytorch.org/whl/cpu'])
@bentoml.artifacts([PytorchModelArtifact('model'),
                    PickleArtifact('tokenizer')])
class Text_classification(bentoml.BentoService):

    def predict(self, to_predict):

        tokenizer = self.artifacts.tokenizer
        model = self.artifacts.model
        # encode text
        sent_id = tokenizer.batch_encode_plus(
            to_predict, return_token_type_ids=False, padding='max_length',
            max_length=512, truncation=True)

        test_seq = torch.tensor(sent_id['input_ids']).squeeze(1)
        test_mask = torch.tensor(sent_id['attention_mask'])

        # get predictions for data
        with torch.no_grad():
            preds = model(test_seq.to('cpu'), test_mask.to('cpu'))
            preds = preds.detach().cpu().numpy()
        model_output = preds
        preds = np.argmax(preds, axis=1)
        return preds, model_output

    @bentoml.api(input=DataframeInput(), batch=True)
    def classify_text(self, df):
        preds, model_outputs = self.predict([df])
        return preds[0]
