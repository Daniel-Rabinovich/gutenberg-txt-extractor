import re, sqlite3
import networkx as nx

# this script divides dataset into train/test
# same author cant be in train and test
# 1. pull all the authors

class Book:
    
    def __init__(self,book_id, authors, gender):
        self.book_id = book_id
        self.authors = authors 
        self.gender = gender 
        
    def __repr__(self):
        return f"({self.book_id}, {self.authors}, {self.gender})"
    def get_id(self):
        return int(self.book_id)
    
    def get_authors(self):
        return self.authors
    
    def get_gender(self):
        return self.gender
    
    def in_authors(self,name):
        if name in self.authors:
            return True
        False

def get_metadata_table(path):
    """ this function return list of books with book_id, gender, author column """
    con = sqlite3.connect(path)
    cur = con.cursor()
    statment = cur.execute("SELECT book_id,author,gender FROM Metadata WHERE gender in ('M','F')")
    books = []
    for row in statment:
        book_id = row[0]
        authors = row[1].split(";")
        gender = row[2]
        #books.append([row[0],[a.strip() for a in authors],row[2]])
        
        books.append(Book(book_id,[a.strip() for a in authors],gender))        
    con.close() #close connection 
    return books

def build_graph(books):
    g = nx.Graph()
    
    # build nodes (each book is a node )
    for book in books:
        g.add_node(book)
    
    # build edges (if authors is in 2 books there will be a egde between them )
    for book in books:
        for author in book.get_authors():
            for other_book in books:
                if other_book.get_id() != book.get_id():
                    if other_book.in_authors(author):
                        g.add_edge(book, other_book)
    return g 
    

# **************************
# Main
# **************************

t = get_metadata_table("../project/database/data.db")
g = build_graph(t)
#print(list(g.edges))

amount = 0
for edge in list(g.edges):
    print(edge)
    amount = amount + 1
    
print(amount)
#m,f = get_male_female_authors(t)
#print(f"{len(m)}, {len(f)}, total: {len(m)+len(f)}")
#print(f"male books:{int(male*100/(male+female))}%\nfemale books:{int(100*female/(female+male))}%")
        
