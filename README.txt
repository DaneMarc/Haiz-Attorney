== General Notes about this assignment ==

Give an overview of your program, describe the important algorithms/steps 
in your program, and discuss your experiments in general. A few paragraphs 
are usually sufficient.


--- INDEX ---
First, the content of each case is processed by removing any non-latin characters, splitting numbers delimited by '-','.' or '/', removing punctuation, case folding and then is finally tokenized. However, after all this processing some tokens may still contain a mix of numbers and letters so such tokens are split even further leaving only words of sufficient length. Each token is then stemmed.

The frequency and positions of each term is tracked during the processing. The weighted term frequency of each term is calculated and stored in the postings list and then added to a sum variable to calculate the document length once all the document terms have been processed. Tokens that appear in the title have their weighted scores doubled as the title arguably contains important information about the case. This marginally improved the F score of free text queries and did not affect boolean queries at all.

I also kept a record of the court level of each case based on the given court hierarchy. E.g. the most important courts get a score of 3, important courts get 2 and the rest get 1. This is used as another metric to rank relevant documents for search later on as rulings from higher courts are generally more important.

The document length and court level of each case is kept in dictionary.txt and is paired with the integer representation of the document ID. The collection size is also stored in the dictionary under 'N'. The postings lists and dictionary are written out using pickle to keep the data structures intact and for the marginally better performance when searching.

dictionary.txt format:
{ 'term': (df, pointer) }
{ docID: (docLength, courtLvl) }
{ 'N': collectionSize }

postings.txt format:
((docID, wtf, [positions,...]), (docID, wtf, [positions,...]), ...) for each term


--- SEARCH ---
First, the query is split into tokens which are then subject to the same processing used in indexing. If the token is a normal word, it is added to a query list containing all the processed terms. If the token is a phrase, a list containing all the phrase terms is added to the query list as well as all the phrase terms individually. This ensures that even if the strict phrase search does not yield any results, the terms in the phrase will still impact the relevancy of the documents.

Example of query list: [['fertility', 'treatment'], 'damages', 'fertility', 'treatment']

Then, we initialize a score dictionary to keep track of the document scores and the number of query terms the document contains. Then we iterate through each term in the query and get its postings list and calculate its idf. If the term is a list, it signifies that the term is a phrase. It will then be evaluated by going through the postings list of each term in order and checking if there is at least one instance of the terms appearing consecutively in the document. The program then iterates through the whole postings list and calulates and adds the scores for all documents in the list. Once all the terms in the query have been processed, the document scores are normalised by dividing each document's score with its doc length taken from the dictionary. The resulting list in the following format:

[(-normalizedScore, docID, courtLvl), ...] - this sorts by score then court level in desc order and then by docID in asc order

The scores for free text queries and boolean queries are calculated in almost the exact same way except for how the document score is normalized in boolean queries. Along with the standard length normalization, if the query is a boolean query, the score is multiplied by the number of phrase terms found in the document. This somewhat enforces the AND behaviour of a boolean query in this not-so-strict implementation by favouring documents that contain more terms. Implementing the boolean search this way significantly improved the program's F2 score.


--- QUERY EXPANSION ---
Using the results of this program as a base, I experimented with using WordNet to add a variable number of synonyms and entailments to the query. I limited the synonyms to only 1 per phrase term as I did not want to crowd the query too much and possibly stray too far from the original query. Entailments on the other hand were a lot more sparse and also a lot more powerful as these were more contextual in nature and were not limited by semantics so I decided not to limit the amount. After playing around with the thresholds, the results were mostly positive. The improvements were also not limited to free text or boolean queries as both saw some improvement. The main measure I used to test the queries was how close the relevant judgements were from the top rank. After submitting the program with query expansion onto the competition framework, my mean F2 score slightly deproved so I decided not to enable the feature in the end.

