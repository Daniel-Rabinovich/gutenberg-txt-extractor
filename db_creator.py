import sqlite3, re, csv, sys, math, os


# this step comes after you downloaded all the books 
# each books downloaded will have and entry in the sqlite db

# 1. get file names 
# 2. loop file names and create entry for each book using catalog + gender

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
                    "authors": line[5]}
                
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
    
    def __init__(self, name_gender_singelton, b_id, year, title, authors, filepath):
        self.__book_id = b_id
        self.__year = year
        self.__title = title
        self.__authors = authors
        self.__gender = "X"
        self.__filepath = filepath
        self.__name_gender = name_gender_singelton
        
        self.__update_estimated_year()
        self.__update_gender()
        
    def __repr__(self):
        return f"({self.__book_id}:{self.__title}:{self.__authors}:{self.__gender}:{self.__year})"
        
    def __extract_author_list(self):
        return [author.strip() for author in self.__authors.split(";")]
    
    
    def __update_estimated_year(self):
        authors = self.__extract_author_list()
        for index in range(len(authors)-1,0,-1):
            found_years = re.findall("\d\d\d\d", authors[index])
            amount = len(found_years)
            if  amount == 1:
                self.__year = int(found_years[0])
            elif amount > 1:
                sum = 0
                for i in range(amount):
                    sum = sum + int(found_years[i])
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
    
    def get_title(self):
        return self.__title
    
    def get_filepath(self):
        return self.__filepath
    
class Library:
    """ this class holds a dictionary of BooksMetadata object """
    
    def __init__(self, path, catalog, name_gender):
        self.__books = {}
        self.__catalog = catalog
        self.__name_gender = name_gender
        self.__read_book_paths(path)
        
        self.__remove_no_gender_books()
        
    def __read_book_paths(self, path):
        for dir, _, filenames in os.walk(path):
            for filename in filenames:
                book_id = filename.split(".")[0]
                book = self.__catalog.get_book(book_id)
                self.__books[book_id] = BookMetadata(
                    self.__name_gender, 
                    book_id, book["year"], 
                    book["title"], 
                    book["authors"],
                    f"{dir}{filename}")
        
    def __remove_no_gender_books(self):
        books_to_remove = []
        for key in self.__books.keys():
            if self.__books[key].get_gender() == "X":
                books_to_remove.append(key)
        for book in books_to_remove:
            self.__books.pop(book)
        
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
        self.__drop_tables()
        self.__create_db()
        
        
    def __drop_tables(self):
        con = sqlite3.connect(self.__path)
        con.execute("DROP TABLE Metadata")
        con.execute("DROP TABLE Books")
        con.commit()
        con.close()
        
    def __create_db(self):
        con = sqlite3.connect(self.__path)
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
        con.close()
    
    def insert_metadata(self, v):
        con = sqlite3.connect(self.__path)
        query = "INSERT INTO Metadata VALUES(?,?,?,?,?)"
        con.execute(query,tuple(v))
        con.commit()
        con.close()

# *************************
# Main
# *************************

def main():
    gender_csv_path = "csv/name_gender.csv"
    catalog_csv_path = "csv/pg_catalog.csv"
    books_dir_path = "books/"
    db_path = "data.db"
    
    gender = NameGender(gender_csv_path)
    catalog = Catalog(catalog_csv_path)
    lib = Library(books_dir_path, catalog, gender)
    books = lib.get_books()
    db = Save(db_path)
    for key in books.keys():
        book = books[key]
        values =[book.get_id(), book.get_title(), book.get_authors(), book.get_gender(), book.get_year()]
        db.insert_metadata(values)

if __name__ == "__main__":
    main()
