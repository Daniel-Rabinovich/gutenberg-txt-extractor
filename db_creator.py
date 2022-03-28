import sqlite3, re, csv, sys


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

    def __init__(self, path):
        self.__path = path
        self.__create_dict()
        
    def get_path(self):
        return self.__path

    def __create_dict(self):
        self.__dict = {}
        with open(self.__path, mode ='r')as file:
            csvFile = csv.reader(file)
            for line in csvFile:
                self.__dict[line[0]] = line[1]
    
    def get_gender(self, name):
        if name in self.__dict.keys():
            return self.__dict["name"]
        else:
            return "X"
    
class Catalog(Singleton):
    
    def __init__(self, path):
        self.__path = path
        self.__create_dict()
        
    def get_path(self):
        return self.__path

    def __create_dict(self):
        pass

class BookMetadata:
    
    def __init__(self, name_gender_singelton, b_id, year, title, authors):
        self.__book_id = b_id
        self.__year = year
        self.__title = title
        self.__authors = authors
        self.__gender = "X"
        self.__name_gender = name_gender_singelton
        
    def __extract_author_list(self):
        return [author.strip() for author in self.authors.split(";")]
    
    
    def __update_estimated_year(self):
        authors = self.__extract_author_list():
        for index in reversed(len(authors)):
            found_years = re.findall("\d\d\d\d", authors[index])
            if found_years > 1:
                
            
    
    def get_gender(self):
        return self.__gender

    def get_id(self):
        return self.__book_id
    
    def get_year(self):
        return self.__year
    
    def get_authors(self):
        return self.__authors
    
    def get_title(self):
        return self.__title
    
    
class Library:
    
    def __init__(self, path):
        self.__path = path # path to books dir
        
    



# *************************
# Main
# *************************

def main():
    gender_csv_path = "csv/name_gender.csv"
    catalog_csv_path = "csv/pg_catalog.csv"
    books_dir_path = "books/"
    
    
    gender = NameGender(gender_csv_path)
    catalog = Catalog(catalog_csv_path)
    
    


if __name__ == "__main__":
    main()
