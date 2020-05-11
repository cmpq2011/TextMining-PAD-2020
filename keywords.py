# -*- coding: utf-8 -*-
"""
PAD Project - Text Mining

@author: Carlos Quendera 49946
@author: David Pais 50220
"""

# Part II a) - Automatic Extraction of Explicit and Implicit Keywords

import re, os, time, json
from nltk import FreqDist
from nltk.util import everygrams

start_time = time.time()

CORPUS_FOLDER_PATH = "corpus2mw/"  # and that we need to change the measure on the extractor file and here to load the file we extracted of that measure
COHESION_MEASURE = "glue" # just here to don't forget to talk in the report about running the other file with the measure we want before running keywords

def read_corpus():

    print("Reading corpus...\n")
    
    regex = re.compile("[\w'’-]+|[;:!?<>&\(\)\[\]\"\.,=/\\\^\$\*\+\|\{\}\%\'\’\-\...\“\”\—\–\§\¿?¡!]|[\S'’-]+") 
    
    docs_size = dict()
    n_grams_freq_corpus_doc = dict()
    n_grams_doc = dict() # to which document a n_gram belongs
    docs_text = dict() # to use for intra-document frequency
    docs_re = dict()
  
    
    for file_name, i in zip(sorted(os.listdir(CORPUS_FOLDER_PATH), key = len), range(len(os.listdir(CORPUS_FOLDER_PATH)))):          
        with open(CORPUS_FOLDER_PATH + file_name, "r", encoding="utf8") as f:
            text = f.read()
            
            # remove doc identification strings
            text_without_doc = re.sub('<doc(.*?)>|<br(.*?)>' , " ", text)
            
            # find the regex defined in text
            text_list = re.findall(regex, text_without_doc)
             
            n_grams = list(everygrams(text_list, min_len=2, max_len=6))
            n_grams_doc.update({doc_n_gram : i for doc_n_gram in n_grams})
            
            n_grams_freq_corpus_doc[i] = FreqDist(n_grams)
            
            docs_size[i] = len(text_list)
                
            docs_text[i] = text_list
            
            docs_re[i] = dict()


    return docs_size, n_grams_freq_corpus_doc, n_grams_doc, docs_text, docs_re


def read_extractor():
    
    with open("{}-{}-mwu.txt".format(CORPUS_FOLDER_PATH[:-1], COHESION_MEASURE), "r", encoding="utf-8") as file: 
        extracted_re = json.load(file)
        
    return extracted_re

def find_docs_re(n_grams_doc, extracted_re, n_grams_freq_corpus_doc, docs_re):
    
    for corpus_re in extracted_re:
        
        n_doc = n_grams_doc[corpus_re]

        re_freq = n_grams_freq_corpus_doc[n_doc][corpus_re]
        
        # from which doc each corpus re is and each re frequency inside that doc
        docs_re[n_doc].update({corpus_re: re_freq})
    
    return docs_re
    
# Main method

docs_size, n_grams_freq_corpus_doc, n_grams_doc, docs_text, docs_re = read_corpus()

extracted_re = read_extractor()

extracted_re = list([tuple(re.split(' ')) for re in extracted_re])     

docs_re = find_docs_re(n_grams_doc, extracted_re, n_grams_freq_corpus_doc, docs_re)

print("Corpus read in %s seconds\n" % (time.time() - start_time))

