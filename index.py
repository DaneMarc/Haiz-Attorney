#!/usr/bin/python3
import nltk
import sys
import getopt
import pickle
import csv
import re

from string import punctuation, digits
from operator import itemgetter
from math import log10, sqrt

# cases decided in these courts have a court score of 3
APEX = { "SG Court of Appeal", "SG Privy Council", "UK House of Lords", "UK Supreme Court", "High Court of Australia", "CA Supreme Court" }

# court score of 2; all other courts have a score of 1
NOT_SO_APEX = { "SG High Court", "Singapore International Commercial Court", "HK High Court", "HK Court of First Instance", "UK Crown Court", "UK Court of Appeal", "UK High Court", "Federal Court of Australia", "NSW Court of Appeal", "NSW Court of Criminal Appeal", "NSW Supreme Court" }

def usage():
    print("usage: " + sys.argv[0] + " -i directory-of-documents -d dictionary-file -p postings-file")

def build_index(in_file, out_dict, out_postings):
    """
    build index from documents stored in the input directory,
    then output the dictionary file and postings file
    """
    print('indexing...')

    stemmer = nltk.PorterStemmer()
    dictionary = {} # { term: [posting list] }
    final_dict = {} # { term: (doc_freq, pointer) }, { doc_id: (doc_length, court_lvl) }
    n = 0 # collection size
    csv.field_size_limit(1000000)

    with open(in_file, encoding='utf-8') as dataset:
        csv_reader = csv.reader(dataset)
        for row in csv_reader:
            if n != 0:
                if int(row[0]) not in final_dict: # checks if document is a duplicate
                    doc_terms = {} # { term: doc_freq }
                    sum = 0
                    pos = 1 # keeps track of word position in doc
                    tokens = parse(row[2])
                    title = set([stemmer.stem(t) for t in parse(row[1])])

                    for tok in tokens:
                        more = False

                        # strips numbers from words
                        if tok[0].isalpha() and tok[-1].isdecimal():
                            tok = tok.rstrip(digits)
                        elif tok[0].isdecimal() and tok[-1].isalpha():
                            tok = tok.lstrip(digits)

                        # checks if the token still contains both numbers and letters and splits them, keeping the words
                        if tok.isalnum() and not tok.isalpha() and not tok.isdigit():
                            toks = [t for t in re.split('\d+', tok) if len(t) > 1]
                            if len(toks) > 0:
                                more = True
                            else:
                                continue

                        if more == False:
                            tok = stemmer.stem(tok)
                            if tok not in doc_terms:
                                doc_terms[tok] = [0, []]
                            doc_terms[tok][0] += 1
                            doc_terms[tok][1].append(pos)
                            pos += 1
                        else: # comes here if splitting the token results in extra tokens
                            for t in toks:
                                t = stemmer.stem(t)
                                if t not in doc_terms:
                                    doc_terms[t] = [0, []]
                                doc_terms[t][0] += 1
                                doc_terms[t][1].append(pos)
                                pos += 1

                    for term, data in doc_terms.items():
                        weighted = 1 + log10(data[0])
                        if term in title:
                            weighted *= 2
                        sum += weighted ** 2
                        if term not in dictionary:
                            dictionary[term] = []
                        dictionary[term].append((int(row[0]), weighted, tuple(data[1])))

                    # stores document length and court level
                    final_dict[int(row[0])] = (sqrt(sum), court_level(row[4]))
                
                # updates the document's court level if a duplicate has a higher level
                else:
                    court = court_level(row[4])
                    if court > final_dict[int(row[0])][1]:
                        final_dict[int(row[0])] = (final_dict[int(row[0])][0], court)
                
            n += 1

    # Stores collection size
    final_dict['N'] = n - 1

    # Writes out the postings lists
    with open(out_postings, 'ab') as out_p:
        for term, postings in dictionary.items():
            postings = tuple(sorted(postings, key=itemgetter(0)))
            final_dict[term] = (len(postings), out_p.tell())
            pickle.dump(postings, out_p)

    # Writes out the dictionary
    with open(out_dict, 'wb') as out_d:
        pickle.dump(final_dict, out_d)


def parse(text):
    processed = re.sub(r'[^\x00-\x7f]',r'', text) # removes non-latin characters
    processed = re.sub('(?<=\d)[-./](?=\d)', ' ', processed) # splits numbers seperated by hypens, periods or slashes
    processed = processed.translate(str.maketrans('', '', punctuation)).lower() # removes punctuations and case folds
    processed = nltk.word_tokenize(processed) # tokenizes
    return processed


def court_level(court):
    return 3 if court in APEX else 2 if court in NOT_SO_APEX else 1


input_file_dataset = output_file_dictionary = output_file_postings = None

try:
    opts, args = getopt.getopt(sys.argv[1:], 'i:d:p:')
except getopt.GetoptError:
    usage()
    sys.exit(2)

for o, a in opts:
    if o == '-i': # input directory
        input_file_dataset = a
    elif o == '-d': # dictionary file
        output_file_dictionary = a
    elif o == '-p': # postings file
        output_file_postings = a
    else:
        assert False, "unhandled option"

if input_file_dataset == None or output_file_postings == None or output_file_dictionary == None:
    usage()
    sys.exit(2)

build_index(input_file_dataset, output_file_dictionary, output_file_postings)
