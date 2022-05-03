from collections import defaultdict
from nltk.corpus import stopwords
from nltk.corpus import wordnet as wn
from nltk import pos_tag
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize
import sqlite3

BATCH_SIZE = 1000
# Initializing WordNetLemmatizer()
word_Lemmatized = WordNetLemmatizer()

def preprocess(text):
    global word_Lemmatized 
    lower = text.lower()
    # Tokenization
    tokens = word_tokenize(lower)
    # Remove Stop words, Non-Numeric and perfom Word Stemming/Lemmenting.
    # WordNetLemmatizer requires Pos tags to understand if the word is noun or verb or adjective etc. By default it is set to Noun
    tag_map = defaultdict(lambda : wn.NOUN)
    tag_map['J'] = wn.ADJ
    tag_map['V'] = wn.VERB
    tag_map['R'] = wn.ADV 
    Final_words = []
    # pos_tag function below will provide the 'tag' i.e if the word is Noun(N) or Verb(V) or something else.
    for word, tag in pos_tag(tokens):
        # Below condition is to check for Stop words and consider only alphabets
        if word not in stopwords.words('english') and word.isalpha():
            word_Final = word_Lemmatized.lemmatize(word,tag_map[tag[0]])
            Final_words.append(word_Final)
    return str(Final_words)


with sqlite3.connect("./data.db") as source:
    with sqlite3.connect("./complete.db") as dest:
        #-----------------------
        # create tables in dest
        #-----------------------
        dest.execute( """CREATE TABLE IF NOT EXISTS "Metadata" (
            "book_id"           INTEGER NOT NULL,
            "title"             TEXT NOT NULL,
            "author"            TEXT NOT NULL,
            "gender"            TEXT,
            "year"              INTEGER NOT NULL,
            PRIMARY KEY("book_id")
            );""")

        dest.execute( """CREATE TABLE IF NOT EXISTS "Books" (
            "book_id"           INTEGER NOT NULL,
            "paragraph_id"      INTEGER NOT NULL,
            "text"              TEXT NOT NULL,
            "word_count"        INTEGER NOT NULL,
            "stopword_count"    INTEGER NOT NULL,
            PRIMARY KEY("book_id","paragraph_id")
            );""")

        #------------------------
        # Copy Metadata
        #------------------------
        
        source_metadata = source.execute(""" select book_id,title,author,gender,year from Metadata""").fetchall()
        for (book_id,title,author,gender,year) in source_metadata:
            dest.execute(""" insert into Metadata (book_id,title,author,gender,year)
                values (?,?,?,?,?)""",(book_id,title,author,gender,year) )

        print("Metadata ready")
        #---------------------------
        # Copy Book and process text
        #---------------------------
        cur = source.execute("""select book_id,paragraph_id,text,word_count,stopword_count from books""")
        rows = cur.fetchmany(BATCH_SIZE)
        while (rows != []):
            for (book_id,paragraph_id,text,word_count,stopword_count) in rows:
                processed_text = preprocess(text)
                dest.execute(""" insert into Books (book_id,paragraph_id,text,word_count,stopword_count)
                    values (?,?,?,?,?)""",(book_id,paragraph_id,processed_text,word_count,stopword_count) )
            rows = cur.fetchmany(BATCH_SIZE)

            

            
    
            
