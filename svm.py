#!/usr/bin/env python
# coding: utf-8

import pandas as pd
import numpy as np
from sklearn.preprocessing import LabelEncoder
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn import svm
from sklearn.metrics import accuracy_score,f1_score,precision_score,recall_score,confusion_matrix
import sqlite3, sys

if len(sys.argv) != 3:
    print("exmaple: python -u svm.py 25 100")
    print("first arg is sentence amount")
    print("second arg is vocabulary size")
    exit()

CONFIG={
    # concatenation
    "number_of_sentance" : sys.argv[1]
    # vocabluary size
    ,"tf_idf_max_features" : sys.argv[2]
    # SVM config
    ,"svm": {
        'C':1.0
        ,'kernel':'linear'
        ,'degree':3
        ,'gamma':'auto'
    }
}
    

def open_data(path):
    with sqlite3.connect(path) as con:
        query = """SELECT b.book_id,paragraph_id,text,gender,word_count
        FROM Books b,Metadata m 
        WHERE b.book_id=m.book_id"""
        return pd.read_sql_query(query,con)

def concatenation(df):
    data = {"book_id":[], "text":[], "gender":[]}
    book_ids = set(df["book_id"])
    for id in book_ids:
        book_paragraphs = df[df["book_id"] == id ].sort_values(by=['paragraph_id'])
        counter = 0
        sen = []
        gender = book_paragraphs.iloc[0]["gender"]
        for row in book_paragraphs.iterrows():
            if counter < CONFIG["number_of_sentance"]:
                if(len(eval(row[1]['text']))):
                    sen += eval(row[1]['text'])
                    counter += 1

            else:
                counter = 0
                data["book_id"].append(id)
                data["text"].append(str(sen))
                data["gender"].append(gender)
                sen = []
        if counter > 0:
            data["book_id"].append(id)
            data["text"].append(str(sen))
            data["gender"].append(gender)
    
    return pd.DataFrame(data)

Corpus = concatenation(open_data("data.db"))

# ### Train test validate split

train_ids = set(pd.read_csv('train-test/train.csv')['book_id'])
test_ids = set(pd.read_csv('train-test/test.csv')['book_id'])
validate_ids = set(pd.read_csv('train-test/validate.csv')['book_id'])

Train_X = []
Train_Y = []
Test_X = []
Test_Y = []
Validate_X = []
Validate_Y = []

for row in Corpus.iterrows():
    if row[1]['book_id'] in train_ids:
        Train_X.append(row[1]['text'])
        Train_Y.append(row[1]['gender'])
    elif row[1]['book_id'] in test_ids:
        Test_X.append(row[1]['text'])
        Test_Y.append(row[1]['gender'])
    elif row[1]['book_id'] in validate_ids:
        Validate_X.append(row[1]['text'])
        Validate_Y.append(row[1]['gender'])


# ### Encoding

Encoder = LabelEncoder()
Train_Y = Encoder.fit_transform(Train_Y)
Test_Y = Encoder.fit_transform(Test_Y)
Validate_Y = Encoder.fit_transform(Validate_Y)

Tfidf_vect = TfidfVectorizer(max_features=CONFIG["tf_idf_max_features"])
Tfidf_vect.fit(Corpus['text'])
Train_X_Tfidf = Tfidf_vect.transform(Train_X)
Test_X_Tfidf = Tfidf_vect.transform(Test_X)
Validate_X_Tfidf = Tfidf_vect.transform(Validate_X)


# ### SVM

# Classifier - Algorithm - SVM
# fit the training dataset on the classifier
SVM = svm.SVC(**CONFIG["svm"])
SVM.fit(Train_X_Tfidf,Train_Y)

print("===============================================")
print("Test:")
test_predicions_svm = SVM.predict(Test_X_Tfidf)
print("SVM Accuracy Score -> ",accuracy_score(test_predicions_svm, Test_Y))
print("SVM precision Score -> ",precision_score(test_predicions_svm, Test_Y))
print("SVM recall Score -> ",recall_score(test_predicions_svm, Test_Y))
print("SVM f1 Score -> ",f1_score(test_predicions_svm, Test_Y))
print("SVM confusion matrix-> \n",confusion_matrix(test_predicions_svm, Test_Y))

print("===============================================")
print("Validate:")
validation_predicions_svm = SVM.predict(Validate_X_Tfidf)
print("SVM Accuracy Score -> ",accuracy_score(validation_predicions_svm, Validate_Y))
print("SVM precision Score -> ",precision_score(validation_predicions_svm, Validate_Y))
print("SVM recall Score -> ",recall_score(validation_predicions_svm, Validate_Y))
print("SVM f1 Score -> ",f1_score(validation_predicions_svm, Validate_Y))
print("SVM confusion matrix-> \n",confusion_matrix(validation_predicions_svm, Validate_Y))
