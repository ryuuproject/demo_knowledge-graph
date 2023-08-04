  Knowledge base question answering is also called knowledge graph question answering, which is a comprehensive task of reasoning and querying input questions to get the correct answer by combining the model with the knowledge graph. Knowledge graph question answering methods can be divided into two categories, one is based on information retrieval, the other is based on semantic analysis. The way of information retrieval does not need to generate intermediate results, and directly gets the answer to the question, which is very concise, but the processing ability of complex problems is limited. Semantic parsing requires semantic parsing of input natural language problems, and then reasoning, with the ability to solve complex problems. This tutorial uses the method of information retrieval to discuss.

Data set:
Use the open question and answer dataset WikiQA

WikiQA uses the Bing query log as a source of questions, each question links to a Wikipedia page that may have an answer, the summary section of the page provides important information about the question, and WikiQA uses sentences from it as candidate answers to the question. The data set contains a total of 3047 questions and 29,258 sentences.

The WikiQA question answering dataset can be used for the training of question answering systems. The data set contains the text of the question, the knowledge base data corresponding to each question, and the corresponding answer.

The knowledge base of this dataset is the summary of the document retrieved through the question, and each sentence in the summary is used as a candidate answer. So we can turn the question and answer problem into a matching problem between two sentences. For the subsequent training of the model, we load the data as <question,answer,label> ;  Such triples.

The label is 1 if answer is the correct answer to question, and 0 if not.

Each triplet is stored with a dictionary.

Define the load function. Use csv to read in the file, specify '\t' in csv.reader as the delimiter, automatically split the data. Go through each row in turn and load the data according to the above data structure
