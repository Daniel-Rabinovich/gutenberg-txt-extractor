import re, sqlite3
import networkx as nx
from networkx import strongly_connected_components

# this script divides dataset into train/test
# same author cant be in train and test

class Book:
    
    def __init__(self,book_id, authors, gender):
        self.book_id = book_id
        self.authors = authors 
        self.gender = gender 
        self.__remove_illustrators()
        
    def __repr__(self):
        return f"({self.book_id}, {self.authors}, {self.gender})"
    
    def get_id(self):
        return int(self.book_id)
    
    def get_authors(self):
        return self.authors
    
    def get_gender(self):
        return self.gender
    
    def __remove_illustrators(self):
        new_authors = []
        for author in self.authors:
            tmp = re.findall("\[Illustrator\]",author)
            if len(tmp) == 0:
                new_authors.append(author)
        self.authors = new_authors
            
    def in_authors(self,name):
        if name in self.authors:
            return True
        False

    
def get_metadata_table(path):
    """ this function return list of books with book_id, gender, author column """
    con = sqlite3.connect(path)
    cur = con.cursor()
    statment = cur.execute("""
        SELECT book_id,author,gender 
        FROM Metadata 
        WHERE gender in ('M','F')""")
    
    books = []
    for row in statment:
        book_id = row[0]
        authors = row[1].split(";")
        gender = row[2]
        books.append(Book(book_id,[a.strip() for a in authors],gender))        
        
    con.close() #close connection 
    
    return books

def build_graph(books):
    
    g = nx.Graph()
    
    # build nodes (each book is a node )
    for book in books:
        g.add_node(book)
    
    # build edges (if authors is in 2 books 
    # there will be a egde between the books )
    for book in books:
        for author in book.get_authors():
            for other_book in books:
                if other_book.get_id() == book.get_id():
                    continue
                if other_book.in_authors(author):
                    g.add_edge(book, other_book)
    return g 
    
def total_books_by_gender(books):
    male, female = 0,0
    for book in books:
        if book.get_gender() == "M":
            male = male + 1
        if book.get_gender() == "F":
            female = female + 1
    return male, female

def split_train_test(scc, books, split=0.8):
    male_total, female_total = total_books_by_gender(books)
    m_train_target = split*male_total
    m_test_target = (1-split)*male_total
    f_train_target = split*female_total
    f_test_target = (1-split)*female_total
    
    m_train, m_test = [], []
    f_train, f_test = [], []
    
    for book_set in scc:
        books_amount = len(book_set)
        gender = list(book_set)[0].get_gender()
        if gender == "M":
            if m_train_target - books_amount > 0:
                for book in book_set:
                    m_train.append(book)
                m_train_target = m_train_target - books_amount
            else:
                for book in book_set:
                    m_test.append(book)
                m_test_target = m_test_target - books_amount
        if gender == "F":
            if f_train_target - books_amount > 0:
                for book in book_set:
                    f_train.append(book)
                f_train_target = f_train_target - books_amount    
            else:
                for book in book_set:
                    f_test.append(book)
                f_test_target = f_test_target - books_amount

    return m_train, m_test, f_train, f_test

# **************************
# Main
# **************************

t = get_metadata_table("../project/database/data.db")
g = build_graph(t)
y = g.to_directed()
scc = strongly_connected_components(y)
m_tr,m_te,f_tr,f_te = split_train_test(scc,t,0.8)

print(f"m_tr: {len(m_tr)},m_te: {len(m_te)},f_tr: {len(f_tr)},f_te: {len(f_te)}")