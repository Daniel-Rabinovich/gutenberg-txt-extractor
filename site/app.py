from flask import Flask, request, render_template, jsonify
import nltk, nltk.data, re, pickle
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
from nltk.corpus import wordnet as wn
from nltk.corpus import stopwords
from collections import defaultdict
from nltk import pos_tag


app = Flask(__name__)

word_Lemmatized = WordNetLemmatizer()
nltk.download('punkt')
nltk.download('wordnet')
nltk.download('omw-1.4')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')

with open("dumptfidf.pkl", 'rb') as file:
    tfidf_vect = pickle.load(file)

with open("dumpsvm.pkl", 'rb') as file:
    svm = pickle.load(file)

def lemmatize_text(text):
    global word_Lemmatized
    tokens = word_tokenize(text)
    tag_map = defaultdict(lambda : wn.NOUN)
    tag_map['J'] = wn.ADJ
    tag_map['V'] = wn.VERB
    tag_map['R'] = wn.ADV
    Final_words = []

    for word, tag in pos_tag(tokens):
        # Below condition is to check for Stop words and consider only alphabets
        if word not in stopwords.words('english') and word.isalpha():
            word_Final = word_Lemmatized.lemmatize(word,tag_map[tag[0]])
            Final_words.append(word_Final)
    return str(Final_words)


def clean_text(text):
    text = text.lower()
    text = re.sub("[^a-z ]", "",text)
    text = re.sub("[ ]+"," ",text)
    return text

@app.route("/", methods=["POST","GET"])
def hello_world():
    if request.method == 'POST':
        tmp = request.json["book"]

        # process book for svm model
        tmp = clean_text(tmp)

        # lemmatize book
        tmp = lemmatize_text(tmp)

        # vectorize text
        tmp = tfidf_vect.transform([tmp])

        # predict
        tmp = svm.predict(tmp)

        if tmp[0] > 0.5:
            ans = "male"
        else:
            ans = "female"

        return jsonify(ans)
        
    if request.method == 'GET':
        return render_template("index.html")


