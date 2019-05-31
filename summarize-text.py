import string, sys, math, nltk, re, os, urllib.request
from urllib.error import URLError, HTTPError
from operator import itemgetter
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from bs4 import BeautifulSoup

def extract_article(article_url):
    url = "http://boilerpipe-web.appspot.com/extract?output=text&url="
    url = url + article_url
    print(url)
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        response = urllib.request.urlopen(req)
    except HTTPError as e:
        sys.exit('Error: Server unable to fulfil request. Error code: ' + str(e.code))
    except URLError as e:
        sys.exit('Error: No network connection, or server does not exist. Reason: ' + str(e.reason))
    soup = BeautifulSoup(response, features="html.parser")
    return soup.get_text()

def tokenize(text):
    """Return array of split words with trailing/preceeding punctuation removed."""
    word_tokens = []
    for word in text.split():
        word = word.strip(string.punctuation+"“ ”–—")
        word = word.lower()
        if word:
            word_tokens.append(word)
    if not word_tokens:
        sys.exit("Error: URL returned no article text.")
    return word_tokens

def clean_sentence(sentence):
    """Remove tabs and newlines."""
    sentence = sentence.replace("\t", "")
    sentence = sentence.replace("\n", "")
    return sentence

def boost(score, index, num_sentences):
    """Weight sentences that appear at the beginning and end more."""
    if (index > num_sentences/2):
        index = num_sentences - (index + 1)
    factor = 1 + math.exp((index*(-1)) / num_sentences/2)
    return (score * factor)

def main():
    ps = PorterStemmer() # stems words to their roots
    stop_words = set(stopwords.words('english'))
    summary_len = input("How many sentences should be in the summary? ")
    while summary_len == "0":
        print("Error: Please enter a nonzero amount.")
        summary_len = input("How many sentences should be in the summary? ")
    # title = input('Please enter the title of the text: ')
    # title = tokenize(title)
    # title = [ps.stem(word) for word in title]
    # text = read_input()
    article_url = input("Enter url for article you wish to summarize:")
    text = extract_article(article_url)
    
    # Clean up text
    text = re.sub(r'[“”]', '"', text) # replace special quotes with normal ones
    # Remove lines that do not end in punctuation e.g. titles, captions, meta-data etc
    lines = text.split("\n")  
    lines_filtered = [line for line in lines if line and (line[-1] == "." or \
        line[-1] == "?" or line[-1] == "!" or line[-2:] == '."' or line[-2:] == '!"' or \
        line[-2:] == '?"')]
    text = "\n".join(lines_filtered)
    if not text:
        sys.exit("Error: URL returned no article text.")

    # Remove stop words & create frequency table
    word_tokens = tokenize(text)
    frequency_table = {}
    for word in word_tokens:
        if word not in stop_words:
            word = ps.stem(word)
            if word not in frequency_table:
                frequency_table[word] = 1
            else:
                frequency_table[word] += 1 
    if not frequency_table:
        sys.exit("Error: Article does not contain enough unique content to create a summary.")

    # Rank info content of each sentence
    text = re.sub(r'[“”]', '"', text) # quotes mess with sent_tokenize()
    sentences = sent_tokenize(text)
    sentence_scores = []
    order_num = 0 # remember order of sentences in text
    for sentence in sentences:
        # sentence = clean_sentence(sentence)
        # title_words_set = set()
        # title_words_bonus = 0
        info_score = 0
        sentence_len = 0 # count nonstop words towards length
        sentence_tokens = tokenize(sentence)
        for word in sentence_tokens:
            word = ps.stem(word)
            if word in frequency_table: # only look at non-stopwords
                # if word in title and word not in title_words_set: 
                #     title_words_bonus += (1/len(title))
                #     title_words_set.add(word)
                sentence_len += 1
                info_score += frequency_table[word]
        
        if sentence_len: # only count sentences that actually have non stopwords        
            # info_score = boost(info_score, order_num, len(sentences)) # adjust score by where the sentence appeared in text
            # if (title_words_bonus):
            #     info_score *= (1+title_words_bonus)
            info_score = info_score # adjust score by length of sentence?
            sentence_scores.append((sentence, info_score, order_num))
            order_num += 1
    sentence_scores.sort(key=itemgetter(1), reverse=True) # sort by score

    # Return highest ranking sentences
    summary_tuples = sentence_scores[0:int(summary_len)]
    summary_tuples.sort(key=itemgetter(2)) # sort by appearance in original text
    os.system('clear')
    print("Summary:\n")
    for tuple_ in summary_tuples:
        print(tuple_[0]+"\n")

if __name__ == "__main__":
    main()
