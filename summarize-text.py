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
    summary_len = int(summary_len)
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

    # Compute probabilities for each word (dont count stop words)
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

    # Implement SumBasic algorithm
    text = re.sub(r'[“”]', '"', text) # quotes mess with sent_tokenize()
    sentences = sent_tokenize(text)
    summary = []
    sentence_scores = []
    while len(summary) < summary_len:
        # 1. Compute sentence scores (average probability of words)
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
        # 2. Find most probable word
        best = ["", 0]
        for word, prob in word_probs.items():
            if prob > best[1]:
                best = [word, prob]
        # print("best word:", best)
        # 3. Find highest scoring sentence that contains the most probable word
        summ_sent = ("", 0, -1)
        for sent in sentence_scores:
            if sent[1] > summ_sent[1] and sent not in summary:
                if best[0] in [ps.stem(word) for word in tokenize(sent[0])]:
                    summ_sent = sent
        assert(summ_sent[0] != "")
        # print("best sent:", summ_sent[0])
        summary.append(summ_sent)
        # 4. Decrease probabilities for all words in new summary sentence
        for word in tokenize(summ_sent[0]):
            word = ps.stem(word)
            if word in word_probs:
                # print(word)        
                word_probs[word] *= word_probs[word]
        assert(word_probs[best[0]] < best[1])
        sentence_scores = []
    summary.sort(key=itemgetter(2)) # sort by appearance in text

    os.system('clear')
    print("Summary:\n")
    for tuple_ in summary:
        print(tuple_[0]+"\n")

if __name__ == "__main__":
    main()
