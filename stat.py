import matplotlib.pyplot as plt
import sqlite3, re



def get_gender(DB_PATH):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    r = cur.execute("SELECT gender from Metadata")
    genders = ["male", "female"]
    amount = [0,0]
    for x in r:
        if x[0] == "M":
            amount[0] += 1
        elif x[0] == "F":
            amount[1] += 1

    con.close()
    plt.title("Books by Fender")
    plt.xlabel("Gender")
    plt.ylabel("Amount")
    plt.bar(genders, amount)
    plt.savefig('statistics/gender.png')
    plt.close()

def get_century(DB_PATH):
    
    # set x,y axis
    century = ["17th","18th","19th","20th","21th"]
    amount = [0,0,0,0,0]
    
    
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    r = cur.execute("SELECT year from Metadata")
    for x in r:
        cent = str((x[0]) // 100 + 1) + "th"
        for y in enumerate(century):
            if y[1] == cent:
                amount[y[0]] = amount[y[0]] + 1 
    con.close()
    plt.title("Books by century")
    plt.xlabel("Century")
    plt.ylabel("Amount")
    plt.bar(century, amount)
    plt.savefig('statistics/century.png')
    plt.close()

def get_book_length(DB_PATH):
    
    # get book_ids
    book_ids =[]
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    r = cur.execute("SELECT book_id from Metadata")
    for x in r:
        book_ids.append(x[0])
    
    # get each book length
    book_lengths = []
    number_of_paragraphs = []
    for x in book_ids:
        r = cur.execute("SELECT word_count FROM Books WHERE book_id = ?",(x,))
        paragraphs = 0
        length = 0
        for y in r:
            paragraphs = paragraphs + 1
            length = length + y[0]
        
        book_lengths.append(length)
        number_of_paragraphs.append(paragraphs)
        print(x,length)
    
    plt.hist(number_of_paragraphs, 15, facecolor='blue', alpha=0.5, range=[0,7500])
    plt.title("Number of calculated sentences per book")
    plt.xlabel("Sentences")
    plt.ylabel("Amount")
    plt.savefig('statistics/sentences.png')
    plt.close()

    plt.hist(book_lengths, 15, facecolor='blue', alpha=0.5, range=[0,300000])
    plt.title("Book lengthes")
    plt.xlabel("length")
    plt.ylabel("amount")
    plt.savefig('statistics/book_lengths.png')
    plt.close()
    con.close()

def stop_words_count(DB_PATH):

    book_ids = []
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    r = cur.execute("SELECT book_id from Metadata")
    for x in r:
        book_ids.append(x[0])

    stopwords_pre_book = []
    for x in book_ids:
        stopwords = 0
        r = cur.execute("SELECT stopword_count FROM Books WHERE book_id = ?",(x,))
        for y in r:
            stopwords = stopwords + y[0]
        stopwords_pre_book.append(stopwords)

    con.close()
    plt.hist(stopwords_pre_book, 15, facecolor='blue', alpha=0.5, range=[0,150000])
    plt.title("Number of calculated stopwords per book")
    plt.xlabel("Stopwords")
    plt.ylabel("Amount")
    plt.savefig('statistics/stopwords.png')
    plt.close()

def vocb_size_per_book(DB_PATH):
    book_ids = []
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    r = cur.execute("SELECT book_id from Metadata")
    
    for x in r:
        book_ids.append(x[0])

    vocab_amount = []
    for x in book_ids:
        vocab = set()
        r = cur.execute("SELECT text from Books WHERE book_id = ?",(x,))
        for y in r:
            y = y[0]
            y = re.sub(r"[^a-z ]",'',y)
            y = y.split(" ")
            for z in y:
                vocab.add(z)
        vocab_amount.append(len(vocab))
        print(f"{x} {len(vocab)}")

    con.close()
    plt.hist(vocab_amount, 15, facecolor='blue', alpha=0.5, range=[0,20000])
    plt.title("Size of vocabulary pre book")
    plt.xlabel("Vocabulary size")
    plt.ylabel("Amount")
    plt.savefig('statistics/vocabulary.png')
    plt.close()


if __name__ == "__main__":
    db = "data.db"
    #get_century(db)
    #get_book_length(db)
    #stop_words_count(db)
    #vocb_size_per_book(db)
    get_gender(db)
