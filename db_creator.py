import sqlite3, re, csv, sys, math, os
from gutenberg_cleaner import super_cleaner
import nltk
from nltk.corpus import stopwords

# this step comes after you downloaded all the books 
# each books downloaded will have and entry in the sqlite db


# *************************
# helper classes
# *************************

class Singleton:
    __instance = None
    @staticmethod 
    def getInstance():
        """ Static access method. """
        if Singleton.__instance == None:
            Singleton()
        return Singleton.__instance
    def __init__(self):
        """ Virtually private constructor. """
        if Singleton.__instance != None:
            raise Exception("This class is a singleton!")
        else:
            Singleton.__instance = self

class NameGender(Singleton):
    """ This class is a singleton holding dictionary
    of the authors names and thier gender, keys are the auther names"""
    
    def __init__(self, path):
        self.__path = path
        self.__dict = {}
        self.__create_dict()
        
        
    def get_path(self):
        return self.__path

    def __create_dict(self):
        with open(self.__path, mode ='r')as file:
            csvFile = csv.reader(file)
            for line in csvFile:
                self.__dict[line[0]] = line[1]
    
    def get_gender(self, name):
        if name in self.__dict.keys():
            return self.__dict[name]
        else:
            return "X"
        
    def get_dict(self):
        return self.__dict
    
class Catalog(Singleton):
    """ this class is a singleton holding the relevent data 
    from pg_catalog csv as a dictionary, keys are the book ids"""
    
    def __init__(self, path):
        self.__path = path
        self.__dict = {}
        self.__create_dict()
       
    def get_path(self):
        return self.__path

    def __create_dict(self):
        with open(self.__path, mode ='r')as file:
            csvFile = csv.reader(file)
            index = -1
            for line in csvFile:
                index = index + 1
                if index == 0:
                    continue
                self.__dict[line[0]] = {
                    "title": line[3],
                    "year": line[2].split("-")[0],
                    "authors": line[5],
                    "type": line[1]}
                
    def get_book(self, id):
        if id in self.__dict.keys():
            return self.__dict[id]
        else:
            return None
    
    def get_dict(self):
        return self.__dict

class BookMetadata:
    """ this class holds the metadata of a single book,
    also generates the gender and estimated year automatically """
    
    def __init__(self, name_gender_singelton, book_id, year, title, authors, type, filepath):
        self.__book_id = book_id
        self.__year = year
        self.__title = title
        self.__authors = authors
        self.__gender = "X"
        self.__filepath = filepath
        self.__type = type
        self.__name_gender = name_gender_singelton
        
        self.__update_estimated_year()
        self.__update_gender()
        
    def __repr__(self):
        return f"""(
            {self.__book_id},
            {self.__title},
            {self.__authors},
            {self.__gender},
            {self.__year}
            )"""
        
    def __extract_author_list(self):
        return [author.strip() for author in self.__authors.split(";")]
    
    def __update_estimated_year(self):
        authors = self.__extract_author_list()
        for author in authors:
            amount = 0
            if len(re.findall("\[Illustrator\]",author)) == 0:
                found_years = re.findall("\d\d\d\d", author)
                amount = len(found_years)
            if  amount == 1:
                self.__year = int(found_years[0])
            elif amount > 1:
                sum = 0
                for i in range(amount):
                    sum += int(found_years[i])
                self.__year = math.floor(sum/amount)
    
    def __update_gender(self):
        authors = self.__extract_author_list()
        genders = []
        for author in authors:
            if len(re.findall("\[Illustrator\]",author)) == 0:
                genders.append(self.__name_gender.get_gender(author))
        
        genders = set(genders)
        if "F" in genders and len(genders) == 1:
            self.__gender = "F"
        elif "M" in genders and len(genders) == 1:
            self.__gender = "M"
        
    def get_gender(self):
        return self.__gender

    def get_id(self):
        return int(self.__book_id)
    
    def get_year(self):
        return self.__year
    
    def get_authors(self):
        return self.__authors
    
    def get_type(self):
        return self.__type
    
    def get_title(self):
        return self.__title
    
    def get_filepath(self):
        return self.__filepath
    
class Library:
    """ this class holds a dictionary of BooksMetadata object """
    
    def __init__(self, path, catalog_path, name_gender_path, db_path):
        self.__books = {}
        self.__catalog = Catalog(catalog_path)
        self.__name_gender = NameGender(name_gender_path)
        self.__db_path = db_path 
        self.__read_books_metadata(path)
        
        self.__remove_no_gender_books()
        self.__remove_non_text_books()
        
        nltk.download('punkt')
        nltk.download('stopwords')
        self.__stop_words = stopwords.words("english")

        
    def __read_books_metadata(self, path):
        for dir, _, filenames in os.walk(path):
            for filename in filenames:
                book_id = filename.split(".")[0]
                book = self.__catalog.get_book(book_id)
                self.__books[book_id] = BookMetadata(
                    self.__name_gender, 
                    book_id, book["year"], 
                    book["title"], 
                    book["authors"],
                    book["type"],
                    f"{dir}{filename}")
        
    def __remove_no_gender_books(self):
        books_to_remove = []
        for key in self.__books.keys():
            if self.__books[key].get_gender() == "X":
                books_to_remove.append(key)
        for book in books_to_remove:
            self.__books.pop(book)
    
    def __remove_non_text_books(self):
        books_to_remove = []
        for key in self.__books.keys():
            if self.__books[key].get_type() != "Text":
                books_to_remove.append(key)
        for book in books_to_remove:
            self.__books.pop(book)
    
    def start(self):
        db = Save(self.__db_path)
        books_ids = self.get_books().keys()
        books_inserted = 0
        total_books = len(books_ids)
        for key in books_ids:
            if db.check_id_exists(key):
                print("book exists {}".format(key))
                continue
            
            book = self.get_book(key)
            print(f"({books_inserted}/{total_books}) inserting book #{key}")
            proccessed_book = []
            
            # insert metadata
            values =[book.get_id(), 
                     book.get_title(), 
                     book.get_authors(), 
                     book.get_gender(), 
                     book.get_year()]
            db.insert("Metadata", values)
            
            # insert book content
            text = self.__read_text_from_file(key)
            text = super_cleaner(text, 5,  600)
            
            text = text.lower()
            text = re.sub("[\\r]*","",text)
            text = text.split("\n\n")
            
            for i in range(len(text)):
                text[i] = re.sub("\n+"," ",text[i])
                text[i] = re.sub("[^a-z0-9\,\.\[\]\"\']"," ",text[i])
                text[i] = text[i].strip()
                text[i] = re.sub("\s+"," ",text[i])
                if text[i] != "[deleted]":
                    proccessed_book.append(text[i])
            
            para_id = 1 
            for paragraph in proccessed_book:
                values = [key,
                        para_id,
                        paragraph,
                        self.__word_count(paragraph),
                        self.__stop_words_count(paragraph)]
                db.insert("Books", values)
                para_id += 1
            books_inserted +=1 
            
            if books_inserted % 20 == 0:
                db.con.commit()
        db.con.commit()
        db.con.close()
        
    def __word_count(self,paragraph):
        tmp = paragraph.split(" ")
        return len(tmp)

    def __stop_words_count(self,paragraph):
        count = 0
        tmp = paragraph.split(" ")
        for x in tmp:
            if x in self.__stop_words:
                count = count + 1
        return count
    
    def __read_text_from_file(self, key):
        f = open(self.get_book(key).get_filepath(),'r',encoding='utf8', errors='ignore')
        return f.read()
    
    def get_books(self):
        return self.__books

    def get_book(self, id):
        if id in self.__books.keys():
            return self.__books[id]
        else:
            return None

class Save:
    
    def __init__(self, db_path):
        self.__path = db_path
        self.con = sqlite3.connect(self.__path)
        #self.__drop_tables()
        self.__create_db()
       
        
        
    def __drop_tables(self):
        self.con.execute("DROP TABLE Metadata")
        self.con.execute("DROP TABLE Books")
        self.con.commit()
        print("removed old tables")
        
    def __create_db(self):
        
        self.con.execute("""
            create table if not exists "Metadata" (
            "book_id"           INTEGER NOT NULL,
            "title"             TEXT NOT NULL,
            "author"            TEXT NOT NULL,
            "gender"            TEXT,
            "year"              INTEGER NOT NULL,
            PRIMARY KEY("book_id")
            );
            """)
        self.con.execute("""
            create table if not exists "Books" (
            "book_id"           INTEGER NOT NULL,
            "paragraph_id"      INTEGER NOT NULL,
            "text"              TEXT NOT NULL,
            "word_count"        INTEGER NOT NULL,
            "stopword_count"    INTEGER NOT NULL,
            PRIMARY KEY("book_id","paragraph_id")
            );
            """)
        self.con.commit()
        print("created Metadata,Books tables")
    
    def insert(self, table, v):
        query = f"INSERT INTO {table} VALUES(?,?,?,?,?)"
        self.con.execute(query,tuple(v))

    def check_id_exists(self,book_id):
        res = self.con.execute(f"SELECT 1 FROM Metadata WHERE book_id = {book_id}")
        return res.fetchone() is not None
# *************************
# Main
# *************************

def main():
    # all the paths to the correct files
    gender_csv_path = "csv/name_gender.csv"
    catalog_csv_path = "csv/pg_catalog.csv"
    books_dir_path = "books/"
    db_path = "data.db"
        
    # init object that holds all the correct books 
    # (automatically filters them)
    lib = Library(books_dir_path, catalog_csv_path, gender_csv_path, db_path)
    
    # start creating db (old db will get deleted)
    lib.start()
    
if __name__ == "__main__":
    main()
