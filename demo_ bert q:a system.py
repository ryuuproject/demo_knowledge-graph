# -*- coding: utf-8 -*-


conda install -c huggingface transformers
conda install -c huggingface -c conda-forge datasets
import numpy as np
import pandas as pd
import os
import warnings
import torch
import evaluate
import transformers
from transformers import BertPreTrainedModel, BertModel, BertTokenizer, BertConfig, get_scheduler
from datasets import Dataset
from torch import nn
from torch.utils.data import DataLoader
from torch.optim import AdamW
from tqdm import tqdm

model_name = "bert-base-uncased"

warnings.filterwarnings('ignore')
transformers.logging.set_verbosity_error()

tokenize = BertTokenizer.from_pretrained(model_name)
config = BertConfig.from_pretrained("bert-base-uncased")

def load(filename):
    result = []
    with open(filename, 'r', encoding='utf-8') as csvfile:
        spamreader = pd.read_csv(filename, sep="\t", header=None)
        for i in range(len(spamreader)):
            row = spamreader.iloc[i]
            res = {}
            res['question'] = str(row[0])
            res['answer'] = str(row[1])
            res['label'] = int(row[2])
            if res['question'] == "" or res['answer'] == "" or res['label'] == None:
                continue
            result.append(res)
    return result


train_file = load('data/WikiQA-train.txt')
valid_file = load('data/WikiQA-dev.txt')
test_file = load('data/WikiQA-test.txt')


def get_data(name_file):
    input_ids = []
    attention_mask = []
    token_type_ids = []
    labels = []

    for i, dic in enumerate(name_file):
        question = dic["question"]
        answer = dic["answer"]
        label = dic["label"]

        output = tokenize.encode_plus(text=question,
                                    text_pair=answer,
                                    max_length=64,
                                    truncation=True,
                                    add_special_tokens=True,
                                    padding="max_length")

        input_ids.append(output["input_ids"])
        attention_mask.append(output["attention_mask"])
        token_type_ids.append(output["token_type_ids"])
        labels.append(label)

    dic = {"input_ids": input_ids,
            "attention_mask": attention_mask,
            "token_type_ids": token_type_ids,
            "labels": labels}
    return dic

train_dataset = Dataset.from_dict(get_data(train_file))
eval_dataset = Dataset.from_dict(get_data(valid_file))
test_dataset = Dataset.from_dict(get_data(test_file))

train_dataset.set_format("torch")
eval_dataset.set_format("torch")
test_dataset.set_format("torch")
'''
h_p
'''
batch_size = 8
lr = 5e-5
num_epochs = 3


train_dataloader = DataLoader(train_dataset, shuffle=True, batch_size=batch_size)
eval_dataloader = DataLoader(eval_dataset, batch_size=batch_size)
test_dataloader = DataLoader(test_dataset, batch_size=batch_size)


class BertQA(BertPreTrainedModel):
    def __init__(self, config, freeze=True):
        super(BertQA, self).__init__(config)
        self.num_labels = config.num_labels
        self.bert = BertModel.from_pretrained("bert-base-uncased")

        if freeze:
            for p in self.bert.parameters():
                p.requires_grad = False
        self.qa_ouputs = nn.Linear(config.hidden_size, 2)
        self.loss_fn = nn.CrossEntropyLoss()
        self.init_weights()

    def forward(self, input_ids, attention_mask=None, token_type_ids=None, labels=None):
        outputs = self.bert(input_ids, attention_mask, token_type_ids)
        logits = self.qa_ouputs(outputs[1])

        predicted_labels = torch.softmax(logits, dim=-1)

        if labels is not None:
            loss = self.loss_fn(predicted_labels, labels)
            return {"loss": loss, "predicted_labels": predicted_labels}

        else:
            return {"predicted_labels": predicted_labels}


device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
model = BertQA(config)
model.to(device)


optimizer = AdamW(model.parameters(), lr=lr)
num_training_steps = num_epochs * len(train_dataloader)
lr_scheduler = get_scheduler(
    name="linear",
    optimizer=optimizer,
    num_warmup_steps=0,
    num_training_steps=num_training_steps
)


def eval(eval_dataloader):
    metric = evaluate.load("accuracy")
    model.eval()
    for batch in eval_dataloader:
        batch = {k: v.to(device) for k, v in batch.items()}
        with torch.no_grad():
            outputs = model(**batch)

        predictions = torch.argmax(outputs["predicted_labels"], dim=-1)
        metric.add_batch(predictions=predictions, references=batch["labels"])

    return metric.compute()


progress_bar = tqdm(range(num_training_steps))

for epoch in range(num_epochs):
    model.train()
    for batch in train_dataloader:
        # k: 'input_ids', 'attention_mask', 'token_type_ids', 'labels'
        # v: input_ids.to(device)
        batch = {k: v.to(device) for k, v in batch.items()}
        outputs = model(**batch)
        loss = outputs['loss']
        loss.backward()

        optimizer.step()
        lr_scheduler.step()
        optimizer.zero_grad()
        progress_bar.update(1)

    print('train:', eval(train_dataloader))

print('eval:', eval(eval_dataloader))
