import string, sys, math, nltk, re, os, urllib.request
from urllib.error import URLError, HTTPError
from operator import itemgetter
from nltk.tokenize import sent_tokenize
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from bs4 import BeautifulSoup

def extract_article(article_url):
    """Extract article text by using Web API from boilerpipe."""
    url = "http://boilerpipe-web.appspot.com/extract?output=text&url="
    url = url + article_url
    # print(url)
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

def read_input():
    """Read article URL and summary length from user."""
    summary_len = input("How many sentences should be in the summary? ")
    while summary_len == "0":
        print("Error: Please enter a nonzero amount.")
        summary_len = input("How many sentences should be in the summary? ")
    summary_len = int(summary_len)
    article_url = input("Enter url for article you wish to summarize:")
    return summary_len, article_url

def clean_text(text):
    """Remove non-article/text sentences and special quotes."""
    text = re.sub(r'[“”]', '"', text) # quotes mess with sent_tokenize()
    # Remove lines that do not end in punctuation e.g. titles, captions, meta-data etc
    lines = text.split("\n")  
    lines_filtered = [line for line in lines if line and (line[-1] == "." or \
        line[-1] == "?" or line[-1] == "!" or line[-2:] == '."' or line[-2:] == '!"' or \
        line[-2:] == '?"')]
    text = "\n".join(lines_filtered)
    if not text:
        sys.exit("Error: URL returned no article text.")
    return text

def compute_word_probs(text, stop_words):
    """Compute word probabilities of all unique words in text."""
    ps = PorterStemmer()
    word_tokens = tokenize(text)
    word_probs = {}
    N = 0 # total number of words
    for word in word_tokens:
        if word not in stop_words:
            word = ps.stem(word)
            if word not in word_probs:
                word_probs[word] = 1
            else:
                word_probs[word] += 1 
            N += 1
    if not word_probs:
        sys.exit("Error: Article does not contain enough unique content to create a summary.")
    for word, freq in word_probs.items():
        word_probs[word] = freq/N
    return word_probs

def compute_sentence_scores(sentences, word_probs):
    """Assign sentence score based on sum of word probabilities. 
    This will skew towards longer sentences."""
    ps = PorterStemmer()
    sentence_scores = []
    order_num = 0 # remember order of sentences in text
    for sentence in sentences:
        info_score = 0
        length = 0
        sentence_tokens = tokenize(sentence)
        for word in sentence_tokens:
            word = ps.stem(word)
            if word in word_probs: # only look at non-stopwords
                info_score += word_probs[word]
                length += 1
        # info_score /= length # compute average probability
        if info_score: # only count sentences that actually have non stopwords        
            sentence_scores.append((sentence, info_score, order_num))
            order_num += 1
    return sentence_scores

def main():
    ps = PorterStemmer() # stems words to their roots
    stop_words = set(stopwords.words('english'))
    # Obtain article text
    summary_len, article_url = read_input()
    text = extract_article(article_url)
    
    # Remove non-article/text lines and special quotes
    text = clean_text(text)

    # Compute probabilities for each word (dont count stop words)
    word_probs = compute_word_probs(text, stop_words)

    # Implement SumBasic algorithm
    sentences = sent_tokenize(text)
    summary = []
    while len(summary) < summary_len:
        # 1. Compute sentence scores (total probability of words)
        sentence_scores = compute_sentence_scores(sentences, word_probs)
        
        # 2. Find most probable word
        best = ["", 0]
        for word, prob in word_probs.items():
            if prob > best[1]:
                best = [word, prob]
        
        # 3. Find highest scoring sentence that contains the most probable word
        summ_sent = ("", 0, -1) # (sentence, info score, order num)
        for sent in sentence_scores:
            if sent[1] > summ_sent[1] and sent not in summary:
                if best[0] in [ps.stem(word) for word in tokenize(sent[0])]:
                    summ_sent = sent
        assert(summ_sent[0] != "")
        summary.append(summ_sent)

        # 4. Decrease probabilities for all words in new summary sentence
        for word in tokenize(summ_sent[0]):
            word = ps.stem(word)
            if word in word_probs:      
                word_probs[word] *= word_probs[word]
        
    summary.sort(key=itemgetter(2)) # sort by appearance in text

    # Output summary
    os.system('clear')
    print("Summary:\n")
    for tuple_ in summary:
        print(tuple_[0]+"\n")

if __name__ == "__main__":
    main()
