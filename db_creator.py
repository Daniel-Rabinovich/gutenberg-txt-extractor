import sqlite3, re, csv, sys, math, os
from gutenberg_cleaner import super_cleaner
import nltk
from nltk.corpus import stopwords
import nltk.data

# *************************
# Helper functions 
# *************************

def read_name_gender_csv(csv_path):
    name_gender_dict = {}
    with open(csv_path, mode ='r') as file:
        csv_file = csv.reader(file)
        for line in csv_file:
            name_gender_dict[line[0]] = line[1]
    return name_gender_dict

def read_gutenberg_csv(csv_path):
    catalog = {}
    with open(csv_path, mode ='r') as file:
        csv_file = csv.reader(file)
        next(csv_file)
        for line in csv_file:
            catalog[line[0]] = {
                "id"        : line[0],
                "title"     : line[3],
                "year"      : line[2].split("-")[0],
                "authors"   : line[5],
                "type"      : line[1],
                "gender"    : "X"
                }
    return catalog

def get_books_ids_from_dir(dir_path):
    books_ids = []
    for dir, _, filenames in os.walk(dir_path):
        for filename in filenames:
            books_ids.append(filename.split(".")[0])
    return books_ids

def keep_downloaded_books(gutenberg_dict, books_ids):
    keys_to_remove = []
    for key in gutenberg_dict.keys():
        if key not in books_ids:
            keys_to_remove.append(key)
    for key in keys_to_remove:
        gutenberg_dict.pop(key)
        
def remove_non_text_books(gutenberg_dict):
    keys_to_remove = []
    for key in gutenberg_dict.keys():
        if gutenberg_dict[key]["type"] != "Text":
            keys_to_remove.append(key)
    for id in keys_to_remove:
        gutenberg_dict.pop(id)
    
def update_estimated_year(gutenberg_dict):
    for key in gutenberg_dict.keys():
        authors = authors_to_list(gutenberg_dict[key]["authors"])
        for author in authors:
            amount = 0
            if len(re.findall("\[Illustrator\]",author)) == 0:
                found_years = re.findall("\d\d\d\d", author)
                amount = len(found_years)
            if  amount == 1:
               gutenberg_dict[key]["year"] = int(found_years[0])
            elif amount > 1:
                sum = 0
                for i in range(amount):
                    sum += int(found_years[i])
                gutenberg_dict[key]["year"] = math.floor(sum/amount)
                
def authors_to_list(authors):
    return [author.strip() for author in authors.split(";")]

def update_genders(gutenberg_dict, name_gender):
    for key in gutenberg_dict.keys():
        authors = authors_to_list(gutenberg_dict[key]["authors"])
        genders = []
        for author in authors:
            # skip illustrators
            if len(re.findall("\[Illustrator\]",author)) == 0:
                genders.append(get_gender_from_dict(name_gender, author))
        genders = set(genders)
        if "F" in genders and len(genders) == 1:
            gutenberg_dict[key]["gender"] = "F"
        elif "M" in genders and len(genders) == 1:
            gutenberg_dict[key]["gender"] = "M"
            
def get_gender_from_dict(name_gender, name):
    if name in name_gender.keys():
        return name_gender[name]
    else:
        return "X"
    
def remove_non_gendered_books(gutenberg_dict):
    keys_to_remove = []
    for key in gutenberg_dict.keys():
        if gutenberg_dict[key]["gender"] == "X":
            keys_to_remove.append(key)
    for key in keys_to_remove:
        gutenberg_dict.pop(key)

def create_tables(con):
    con.execute("""
        create table if not exists "Metadata" (
        "book_id"           INTEGER NOT NULL,
        "title"             TEXT NOT NULL,
        "author"            TEXT NOT NULL,
        "gender"            TEXT,
        "year"              INTEGER NOT NULL,
        PRIMARY KEY("book_id")
        );
        """)
    con.execute("""
        create table if not exists "Books" (
        "book_id"           INTEGER NOT NULL,
        "paragraph_id"      INTEGER NOT NULL,
        "text"              TEXT NOT NULL,
        "word_count"        INTEGER NOT NULL,
        "stopword_count"    INTEGER NOT NULL,
        PRIMARY KEY("book_id","paragraph_id")
        );
        """)
    con.commit()
    
def check_id_exists(con, key):
    res = con.execute(f"SELECT 1 FROM Metadata WHERE book_id = {key}")
    return res.fetchone() is not None

def get_amount_already_in_db(con):
    return con.execute("SELECT COUNT(book_id) FROM METADATA").fetchone()[0]

def insert(con, table, v):
    query = f"INSERT INTO {table} VALUES(?,?,?,?,?)"
    con.execute(query,tuple(v))

def read_text_from_file(dir_path, key):
    f = open(f"{dir_path}/{key}.txt",'r',encoding='utf8', errors='ignore')
    return f.read()

def get_counter_stats(sents, sw):
    swc, wc = 0, 0
    for word in sents:
        if word in sw:
            swc += 1
        wc += 1
    return swc, wc
# *************************
# Main
# *************************

if __name__ == "__main__":
    
    # paths
    name_gender_csv_path = "csv/name_gender.csv"
    gutenberg_catalog_csv_path = "csv/pg_catalog.csv"
    raw_books_path = "books/"
    database_path = "tmp.db"
    
    # read author-gender csv into a dict
    # key = name, value = gender
    name_gender_dict = read_name_gender_csv(name_gender_csv_path)
    print(f"Loaded authors_gender csv with {len(name_gender_dict.keys())} authors")
    
    # read gutenberg catalog into a dict
    # key = book id, value = dictionary of properties
    gutenberg_dict = read_gutenberg_csv(gutenberg_catalog_csv_path)
    print(f"Loaded gutenberg csv with {len(gutenberg_dict.keys())} Books")
    
    # read all the ids of the downloaded books in dir
    books_ids = get_books_ids_from_dir(raw_books_path)
    print(f"Found {len(books_ids)} Books in dir\n")
    
    # remove all the books that were not downloaded from the catalog
    # TODO: needs optimization!!! 
    # these step takes alot of time because each key in searched 
    # in a list of 13k values for all the 60k books 
    print(f"Removing books that weren't downloaded from dictionary...")
    keep_downloaded_books(gutenberg_dict, books_ids)
    
    # remove non text books from catalog
    print(f"Removing non text books (audiobooks etc)...")
    remove_non_text_books(gutenberg_dict)
    
    # update enstimated year
    print(f"Updating estimated year...")
    update_estimated_year(gutenberg_dict)
    
    # update book genders by authors
    print("Updating books gender...")
    update_genders(gutenberg_dict, name_gender_dict)
    
    # remove books with no gender
    print("Removing books without a gender")
    remove_non_gendered_books(gutenberg_dict)
    
    print(f"Total books left in dictionary: {len(gutenberg_dict.keys())}")
    
    # preparing connection
    con = sqlite3.connect(database_path)
    
    # check if user would like to recreate tables
    reset_db = input("Would you like to reset the database? [y/n]:")
    if reset_db.lower() == "y" :
        con.execute("DROP TABLE Metadata")
        con.execute("DROP TABLE Books")
        con.commit()

    # create new tables if dont exists
    create_tables(con)
    
    # stats and vars
    nltk.download('punkt')
    nltk.download('stopwords')
    stop_words = stopwords.words("english")
    tokenizer = nltk.data.load('tokenizers/punkt/english.pickle')
    books_in_db = get_amount_already_in_db(con)
    total = len(gutenberg_dict.keys())
    
    # start main loop
    for key in gutenberg_dict.keys():
        if check_id_exists(con, key):
            print(f"#{key} Already in database, skipping")
            continue
        
        b = gutenberg_dict[key]
        print(f"({books_in_db}/{total}) Inserting #{key} ")
        
        # insert into metadata 
        insert(con, "Metadata", 
               [b["id"],
                b["title"],
                b["authors"],
                b["gender"],
                b["year"]])
        
        # get book text
        text = read_text_from_file(raw_books_path, key)
        
        # clean text and prep for insert
        text = super_cleaner(text, 5,  600)
        text = text.lower()
        text = re.sub("[\\r]*","",text)
        text = text.split("\n\n")
        
        # split into sentences
        proccessed = []
        for i in range(len(text)):
            text[i] = re.sub("\n+"," ",text[i])
            text[i] = re.sub("[^a-z0-9\,\.\[\]\"\']"," ",text[i])
            text[i] = text[i].strip()
            text[i] = re.sub("\s+"," ",text[i])
            if text[i] != "[deleted]":
                s = tokenizer.tokenize(text[i])
                for j in s:
                    proccessed.append(j)
        
        sents_id = 1 
        for sents in proccessed:
            swc, wc = get_counter_stats(sents, stop_words)
            values = [key, sents_id, sents, wc, swc]
            insert(con, "Books", values)
            sents_id += 1
        
        books_in_db += 1
        
        if books_in_db % 20 == 0:
            con.commit()
            
    con.commit()
    con.close()
