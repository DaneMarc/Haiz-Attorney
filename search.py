#!/usr/bin/python3
import nltk
import sys
import getopt
import pickle
import re

# from nltk.corpus import wordnet as wn
from string import punctuation
from operator import itemgetter
from math import log10, floor, sqrt


def usage():
    print("usage: " + sys.argv[0] + " -d dictionary-file -p postings-file -q file-of-queries -o output-file-of-results")


def run_search(dict_file, postings_file, query_file, results_file):
    """
    using the given dictionary file and postings file,
    perform searching on the given queries file and output the results to a file
    """
    print('running search on the queries...')

    with open(dict_file, 'rb') as d_file:
        dictionary = pickle.load(d_file)

    N = dictionary['N'] # collection size
    stemmer = nltk.PorterStemmer()
    query = []

    # prepares the queries for evaluation
    with open(query_file, 'r') as q_file:
        line = q_file.readline().strip()
        tokens = re.findall("(?:\".*?\"|\S)+", line)
        for tok in tokens:
            if tok == "AND":
                continue
            elif tok[0] == '"':
                toks = tok[1:-1].split()
                toks = [stemmer.stem(re.sub('(?<=\d)[-./](?=\d)', ' ', t).translate(str.maketrans('', '', punctuation)).lower()) for t in toks]
                query.append(toks)
                for t in toks:
                    query.append(t)
            else:
                query.append(stemmer.stem(re.sub('(?<=\d)[-./](?=\d)', ' ', tok).translate(str.maketrans('', '', punctuation)).lower()))

    with open(postings_file, 'rb') as postings:
        result = []
        bool = False # flag to signal whether query is a boolean query
        scores = {} # tracks scores of docs. Format: { doc_id: [score, no_of_query_terms_matches] }

        for term in query:
            docs = []

            if type(term) != list: # checks if term is a phrase
                if term in dictionary:
                    data = dictionary[term]
                    idf = log10(N / data[0])
                    postings.seek(data[1])
                    docs = pickle.load(postings)
            else:
                bool = True
                arr = []
                for word in term:
                    if word in dictionary:
                        postings.seek(dictionary[word][1])
                        arr.append(pickle.load(postings))
                docs = eval_phrase(arr)
                if len(docs) > 0:
                    idf = log10(N / len(docs))
                
            for doc in docs:
                if doc[0] in scores:
                    scores[doc[0]][0] += doc[1] * idf
                    scores[doc[0]][1] += 1
                else:
                    scores[doc[0]] = [doc[1] * idf, 1]
                    
    # normalizes scores using doc length and multiplies by keyword frequency if boolean query
    if bool:
        for doc, score in scores.items():
            data = dictionary[doc]
            result.append((-doc, (score[0] / data[0]) * score[1], data[1]))
    else:
        for doc, score in scores.items():
            data = dictionary[doc]
            result.append((-doc, score[0] / data[0], data[1]))

    # sorts docs based on score then court importance in desc order then by docID in asc order
    result.sort(key=itemgetter(1,2,0), reverse=True)

    with open(results_file, 'w') as r_file:
        r_file.write(' '.join([str(-res[0]) for res in result]))


# evaluates phrase queries
def eval_phrase(terms):
    if len(terms) == 0:
        return []

    # lists containing data of the latest consecutive term in the phrase
    docs = [doc[0] for doc in terms[0]]
    tfs = [doc[1] for doc in terms[0]]
    pos = [doc[2] for doc in terms[0]]

    for x in range(1, len(terms)):
        curr = terms[x] # the next term to evaluate
        i = j = 0
        llen = len(docs)
        rlen = len(curr)
        iskip = floor(sqrt(llen))
        jskip = floor(sqrt(rlen))
        temp_docs = []
        temp_tfs = []
        temp_pos = []

        while i < llen and j < rlen:
            a = docs[i]
            b = curr[j][0]

            # if both terms have a common doc, attempt to find positions on the doc where they are consecutive
            if a == b:
                temp = get_positions(pos[i], curr[j][2])
                if len(temp) > 0:
                    temp_docs.append(a)
                    temp_tfs.append(tfs[i] + curr[j][1]) # term frequency is cumulative
                    temp_pos.append(temp)
                i += 1
                j += 1
            elif a < b:
                # checks for skips and then skips if the destination does not overshoot
                if i % iskip == 0 and i + iskip < llen and docs[i+iskip] <= b:
                    i += iskip
                else:
                    i += 1
            else:
                if j % jskip == 0 and j + jskip < rlen and curr[j+jskip][0] <= a:
                    j += jskip
                else:
                    j += 1

        # replaces lists with new narrowed down lists
        docs = temp_docs
        tfs = temp_tfs
        pos = temp_pos

    return [(docs[x], tfs[x]) for x in range(0, len(docs))]


# returns doc positions where the right word comes immediately after the left word
def get_positions(left, right):
    i = j = 0
    arr = []
    llen = len(left)
    rlen = len(right)
    iskip = floor(sqrt(llen))
    jskip = floor(sqrt(rlen))

    while i < llen and j < rlen:
        a = left[i]
        b = right[j]

        if a == b:
            j += 1
        elif a < b:
            if b - a == 1:
                arr.append(b)
                i += 1
                j += 1
            else:
                if i % iskip == 0 and i + iskip < llen and left[i+iskip] <= b - 1:
                    i += iskip
                else:
                    i += 1
        else:
            if j % jskip == 0 and j + jskip < rlen and right[j+jskip] <= a + 1:
                j += jskip
            else:
                j += 1

    return arr


# # finds and returns synonyms of a given word
# def expand_query(word):
#     res = []
#     syns = wn.synsets(word)
#     limit = 1

#     if len(syns) > 0:
#         lemmas = syns[0].lemma_names()
#         for i in range(1, len(lemmas)):
#             if limit > 0 and lemmas[i] != word:
#                 res += [stemmer.stem(lem) for lem in lemmas[i].split('_') if lem != word]
#                 limit -= 1
    
#         for syn in syns:
#             entails = syn.entailments()
#             for entail in entails:
#                 res += [stemmer.stem(en) for en in entail.lemma_names()[0].split('_')]

#     return res


dictionary_file = postings_file = query_file = output_file_of_results = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'd:p:q:o:')
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-d':
        dictionary_file  = a
    elif o == '-p':
        postings_file = a
    elif o == '-q':
        query_file = a
    elif o == '-o':
        file_of_output = a
    else:
        assert False, "unhandled option"

if dictionary_file == None or postings_file == None or query_file == None or file_of_output == None :
    usage()
    sys.exit(2)

run_search(dictionary_file, postings_file, query_file, file_of_output)
