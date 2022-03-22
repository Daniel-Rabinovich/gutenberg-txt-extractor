import requests, csv, re

# *****************************************
#  Helper functions
# *****************************************

def csv_to_dict(path="pg_catalog.csv"):
    catalog = dict()
    with open(path, mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        line_count = 0
        for row in csv_reader:
            catalog[row['Text#']] = {
                'language':row['Language'],
                'subjects':row['Subjects'],
            }
            line_count += 1
    return catalog

def remove_non_english_books(books_dict):
    keys_to_remove = []
    for id in books_dict.keys():
        if books_dict[id]["language"] != "en":
            keys_to_remove.append(id)

    for key in keys_to_remove:
        books_dict.pop(key, None)

def remove_unwanted_categories(books_dict):
    keys_to_remove = []
    for id in books_dict.keys():
        if not check_good_category(books_dict, id):
            keys_to_remove.append(id)

    for key in keys_to_remove:
        books_dict.pop(key, None)
    
def check_good_category(books_dict, book_id):
    if str(book_id) in books_dict.keys():
        book = books_dict.get(str(book_id))
        subjects = book.get("subjects")
        categories_found = []

        #extract categories
        rows = subjects.split(";")
        for i in rows:
            tmp = i.split(" -- ")
            for j in tmp:
                categories_found.append(j.strip().lower())

        categories_found = set(categories_found)

        for cat in categories_found:
            if cat in ["fiction"]:
                return True
        return False
    else:
        return False

def get_book_ids_from_dict(books_dict):
    ids = []
    for key in books_dict.keys():
        ids.append(key)
    return ids

def parse_id(book_id):
    """ turn 1234 into 1/2/3/1234 """
    book_id_copy = book_id
    book_id = str(book_id)
    book_id = [c for c in book_id]
    return "{}/{}".format("/".join(book_id[:-1]),book_id_copy)

def make_link(path, tag):
    """ extract path from a tag and combine with full url """
    tag = re.findall("\".+\.txt", tag)
    return "{}/{}".format(path, tag[0][1:])
    
def extract_txt_links(path, html_data):
    """ find all the possible *.txt links in the book's page and returns them as a list"""
    results = re.findall("<a href=\".+\.txt\">", html_data)
    return [make_link(path, tag) for tag in results]
        
def save_book(folder, book_txt, book_id):
    """ save the book to txt file in folder"""
    f_book = open("{}/{}.txt".format(folder,book_id), "w", encoding='utf-8')
    f_book.write(book_txt)
    f_book.close()

def get_full_book_path(mirror, book_id):
    """ combine mirror url with book path """
    return "{}/{}".format(mirror,parse_id(book_id))

def get_txt_links_list(book_url):
    """ return all the urls containig .txt"""
    response = requests.get(book_url)
    return extract_txt_links(book_url, response.text)
    
def pull_book(url):
    """ return the book as a string """
    return requests.get(url).text

def choose_url(arr):
    """ choose the right link containing the book """
    return arr[0]


# *****************************************
#  Main
# *****************************************

# read csv with book data
books = csv_to_dict()
remove_non_english_books(books)
remove_unwanted_categories(books)

# get only the ids 
books_ids = get_book_ids_from_dict(books)

# handle pulling books 
mirror = "https://gutenberg.pglaf.org"
main_txt_dir = "books"

for book_id in range(101,120):

    print("starting book #{}".format(book_id))
    
    # parse book url
    book_url = get_full_book_path(mirror, book_id)
    
    # pull txt links from page
    txt_urls = get_txt_links_list(book_url)
    
    # choose url (for now choose the first one)
    chosen_txt_url = choose_url(txt_urls)
    
    # pull book
    book_txt = pull_book(chosen_txt_url)
    
    # save the book 
    save_book(main_txt_dir, book_txt, book_id)
    
    
    
