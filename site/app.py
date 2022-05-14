from flask import Flask, request, render_template, jsonify
import nltk 
import nltk.data

app = Flask(__name__)

def clean_text(text):
    text = text.lower()
    text = re.sub("[^a-z ]", "",text)
    text = re.sub("[ ]+"," ",text)
    return text

@app.route("/", methods=["POST","GET"])
def hello_world():
    if request.method == 'POST':
        tmp = request.json["book"]
        clean(tmp)
        return jsonify(tmp)
        
    if request.method == 'GET':
        return render_template("index.html")


