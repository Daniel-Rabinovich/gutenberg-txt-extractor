import re, sqlite3, csv
import networkx as nx
from networkx import strongly_connected_components

# this script divides dataset into train/test
# same author cant be in train and test

class Book:
    
    def __init__(self,book_id, authors, gender, title):
        self.book_id = book_id
        self.title = title
        self.authors = authors 
        self.gender = gender 
        self.__remove_illustrators()
        
    def __repr__(self):
        return f"({self.book_id}, {self.authors}, {self.gender})"
    
    def get_id(self):
        return self.book_id
    
    def get_title(self):
        return self.title
    
    def get_authors(self):
        return self.authors
    
    def get_gender(self):
        return self.gender
    
    def get_list(self):
        return [self.book_id, self.gender]
    
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
        SELECT book_id,author,gender,title
        FROM Metadata 
        WHERE gender in ('M','F')""")
    
    books = []
    for row in statment:
        book_id = row[0]
        authors = row[1].split(";")
        gender = row[2]
        title = re.sub("[^a-zA-Z0-9\, ]","",row[3])
        books.append(Book(book_id,[a.strip() for a in authors],gender,title))        
        
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

def split_train_test(scc, books, train=0.8, test=0.1,val=0.1):
    male_total, female_total = total_books_by_gender(books)
    
    m_train_target = train*male_total
    m_test_target = test*male_total
    m_val_target = val*male_total
    
    f_train_target = train*female_total
    f_test_target = test*female_total
    f_val_target = val*female_total
    
    m_train, m_test, m_val = [], [], []
    f_train, f_test, f_val = [], [], []
    
    for book_set in scc:
        books_amount = len(book_set)
        gender = list(book_set)[0].get_gender()
        if gender == "M":
            if m_train_target - books_amount > 0:
                for book in book_set:
                    m_train.append(book)
                m_train_target = m_train_target - books_amount
            elif m_test_target - books_amount > 0:
                for book in book_set:
                    m_test.append(book)
                m_test_target = m_test_target - books_amount
            else: 
                for book in book_set:
                    m_val.append(book)
                m_val_target = m_val_target - books_amount
        if gender == "F":
            if f_train_target - books_amount > 0:
                for book in book_set:
                    f_train.append(book)
                f_train_target = f_train_target - books_amount    
            elif f_test_target - books_amount > 0:
                for book in book_set:
                    f_test.append(book)
                f_test_target = f_test_target - books_amount
            else:
                for book in book_set:
                    f_val.append(book)
                f_val_target = f_val_target - books_amount

    return m_train, m_test, m_val, f_train, f_test, f_val

def save_to_csv(male_train, male_test, male_val, female_train, female_test, female_val):
    
    male_train = [x.get_list() for x in male_train]
    male_test = [x.get_list() for x in male_test]
    male_val = [x.get_list() for x in male_val]
    female_train = [x.get_list() for x in female_train]
    female_test = [x.get_list() for x in female_test]
    female_val = [x.get_list() for x in female_val]
    
    
    write_csv("train-test/train.csv", male_train + female_train)
    write_csv("train-test/test.csv", male_test + female_test)
    write_csv("train-test/validate.csv", male_val + female_val)
    
    
def write_csv(name, data):
    with open(name, 'w') as csvfile: 
        csvwriter = csv.writer(csvfile) 
        csvwriter.writerows(data)
        

# **************************
# Main
# **************************

t = get_metadata_table("data.db")
g = build_graph(t)
y = g.to_directed()
scc = strongly_connected_components(y)
m_tr,m_te, m_va, f_tr,f_te, f_va = split_train_test(scc,t,0.8)

save_to_csv(m_tr,m_te,m_va,f_tr,f_te,f_va)
total_male = len(m_tr) + len(m_te) + len(m_va)
total_female = len(f_tr) + len(f_te) + len(f_va)

# print statistics
print(f"""
male_train: {len(m_tr)} ({(100*len(m_tr))/total_male}%)
male_test: {len(m_te)} ({(100*len(m_te))/total_male}%)
male_test: {len(m_va)} ({(100*len(m_va))/total_male}%)
female_train: {len(f_tr)} ({(100*len(f_tr))/total_female}%)
female_test: {len(f_te)} ({(100*len(f_te))/total_female}%)
female_val: {len(f_va)} ({(100*len(f_va))/total_female}%)
""")
print(f"total books in train/test split: {len(m_tr) + len(m_te) + len(m_va) + len(f_tr) + len(f_te) + len(f_va)}")
