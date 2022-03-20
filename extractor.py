import requests, csv, re


# TODO
# [X] read csv file
# [X] filter unneeded book
# [V] extract books

# ****** extra info for this script ******
# gutenberg mirror list: https://www.gutenberg.org/MIRRORS.ALL
#
# high speed mirror link: https://gutenberg.pglaf.org/
#
# All eBooks are arranged by eBook number, with a unique subdirectory
# based on that eBook number (starting with numbers 1-9).  To get to the
# files for a particular eBook, you need to "drill down" a few
# subdirectory levels.  For example, eBook #11 is in this subdirectory:1/11
# and eBook #12714 is in this subdirectory: 1/2/7/1/12714

def parse_id(book_id):
    """ turn int: 1234 into str: 1/2/3/1234 """
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
    links = []
    results = re.findall("<a href=\".+\.txt\">", html_data)
    for tag in results:
        links.append(make_link(path, tag))
    return links
    
def get_book(book_id):
    """ fetch book as string and return it """
    query = "https://gutenberg.pglaf.org/{}".format(parse_id(book_id))
    response = requests.get(query)
    links = extract_txt_links(query, response.text)
    
    # for now get only the first link
    print(links[0])
    # TODO add utf-8 check
    return requests.get(links[0]).text
        
def save_book(folder, book_id):
    """ save the book to txt file in folder"""
    f_book = open("{}/{}.txt".format(folder,book_id), "w")
    f_book.write(get_book(book_id))
    f_book.close()

# testing
# if you run this script manually create "t" folder
for i in range(101,120):
    save_book("t",i)
