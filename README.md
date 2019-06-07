# Article-Summarizer
Command line interface to summarize text. Enter desired summary length and article URL to retrieve a short summary.

The summarizer uses the [SumBasic algorithm](http://citeseerx.ist.psu.edu/viewdoc/download;jsessionid=32ECB53B997E9161F32D56FAB237B117?doi=10.1.1.529.6099&rep=rep1&type=pdf), a word frequency-based approach. SumBasic consists of the following steps:

1. Compute the probability of each word: p(w<sub>i</sub>) = n<sub>i</sub>/N where n<sub>i</sub> is word frequency and N is total number of words.

2. For each sentence in text assign a score equal to the average probability of words in the sentence: (p(w<sub>1</sub>) + ... + p(w<sub>n</sub>))/n where words w<sub>1</sub>, ..., w<sub>n</sub> are all unique words in a sentence.

3. Pick the highest scoring sentence that contains the most frequent word.

4. Re-calculate weights for each word w<sub>i</sub> that appeared in the sentence chosen in step 3: p<sub>new</sub>(w<sub>i</sub>) = p<sub>old</sub>(w<sub>i</sub>) * p<sub>old</sub>(w<sub>i</sub>).

5. Restart from step 2 if more sentences are needed for desired summary length.

SumBasic works on the finding that high frequency words are very likely to be found in human-produced summaries, so it ensures that step 3 picks the sentence with the most frequent word. Step 4 adjusts the summary depending on what has already appeared in it by decreasing the weights (probabilities) for words that were already chosen. This aims to mimic the fact that most summaries aim to reduce redundancy of information. What's most important to include in a summary depends on what has already been chosen to include. By demoting certain words, it thereby promotes other words that initially had lower weights, helping them have a higher likelihood of inclusion in subsequent sentences.

![example](https://github.com/khanmoha/Article-Summarizer/blob/master/pictures/screenshot.PNG?raw=true)
