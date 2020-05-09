# -*- coding: utf-8 -*-
"""
PAD Project - Text Mining

@author: Carlos Quendera 49946
@author: David Pais 50220
"""

# Part I - Extracting relevant words

import re, os, math, time
from random import sample
import numpy as np
from nltk import FreqDist
from nltk.util import everygrams

start_time = time.time()

CORPUS_FOLDER_PATH = "corpus4mw/"
COHESION_MEASURE = "loglike" # change here to use a different cohesion measure


def n_gram_prob(n_gram): # [dictionary entry][element inside the dictionary entry]
    return n_grams_freq[n_gram] / word_count

def glue(n_gram):
    f = cohesion(n_gram, 'glue')
    return n_gram_prob(n_gram) ** 2 / f # formula of glue (scp) of a n-gram with n > 2 (it can also apply to n = 2)
  
def dice(n_gram):
    f = cohesion(n_gram, 'dice')
    return (word_count * n_gram_prob(n_gram) * 2) / f # formula of dice of a n-gram with n > 2 (it can also apply to n = 2)
  
def mi(n_gram):
    f = cohesion(n_gram, 'mi') # n_gram_prob(n_gram) / f will never be 0 since prob and f > 0
    return math.log(n_gram_prob(n_gram) / f) # formula of mi of a n-gram with n > 2 (it can also apply to n = 2)

def phi(n_gram):
    avq, avd = cohesion(n_gram, 'phi') # word count(number of words in corpus) * frequency
    return (( (word_count ** 2 * n_gram_prob(n_gram)) - avq) ** 2) / avd # formula of phi of a n-gram with n > 2 (it can also apply to n = 2)

def log_l(p, k, m): # auxiliar function for logLike cohesion measure
        return k * math.log(p) + (m - k) * math.log(1-p)

def logLike(n_gram):
    left_subgram, right_subgram = cohesion(n_gram, 'loglike')
    kf1 = word_count * n_gram_prob(n_gram)
    kf2 = left_subgram - kf1
    nf1 = right_subgram
    nf2 = word_count - nf1
    pf1 = kf1/nf1 
    pf2 = kf2/nf2
    pf = left_subgram/ word_count

    # formula of logLike of a n-gram with n > 2 (it can also apply to n = 2)
    if( (pf1 > 0 and pf1 < 1) and  (pf2 > 0 and pf2 < 1) and (pf > 0 and pf < 1)): # < 1 because of math.log(1-p) of log_l
       return 2 * ( log_l (pf1, kf1, nf1) + log_l (pf2, kf2, nf2) - log_l (pf, kf1, nf1) - log_l(pf, kf2, nf2))
   
    else:
        return -math.inf # to avoid being bigger than other omega plus 1 values that might be smaller, ln domain goes from [-oo, oo]

def cohesion (n_gram, measure):

    f = 0 # frequency
        
    avq = 0 
    avd = 0
    
    avx = 0
    avy = 0
    
    n_gramSize = len(n_gram)
    
    for i in range(1,  n_gramSize ): # starting in 1 because :1 goes till the start index, so starts in 0. i: starts in the index (1) till the index
        left_subgram = n_gram_prob(n_gram[:i])
        right_subgram = n_gram_prob(n_gram[i:])
        
        if(not (measure == 'dice')):
            
            if(measure == 'phi'):
                left_subgram = left_subgram * word_count
                right_subgram = right_subgram * word_count
                avq += left_subgram * right_subgram 
                avd += (left_subgram * right_subgram) * (word_count - left_subgram) * (word_count - right_subgram)        
            elif(measure == 'loglike'):
                avx += word_count * left_subgram
                avy += word_count * right_subgram            
            else:                    
                f += left_subgram * right_subgram
    
        else:
            f += word_count * ( left_subgram + right_subgram)
 
    if(measure == 'phi'):
        avq = avq / (  n_gramSize  - 1 )
        avd = avd / (  n_gramSize  - 1 )
        
        return avq, avd
    
    if(measure == 'loglike'):
        avx = avx / (  n_gramSize  - 1 )
        avy = avy / (  n_gramSize  - 1 )
        
        return avx,avy

    if(measure == 'glue' or measure == 'dice' or measure == 'mi'):
        f = f / (  n_gramSize  - 1 ) # formula of F 
        
        return f

def cohesion_measures(measureType, n_gram):    
    if (len(n_gram) == 1):
        return n_gram_prob(n_gram)
    elif(measureType == 'glue'):
        return glue(n_gram)
    elif(measureType == 'dice'):
        return dice(n_gram)
    elif(measureType == 'mi'):
        return mi(n_gram)
    elif(measureType == 'phi'):
        return phi(n_gram)
    elif(measureType == 'loglike'):
        return logLike(n_gram)
    else:
        return glue(n_gram) # glue is the default measure

def readCorpus():
    # Find a set of word characters ([\w'’-])     + means that has at least one ocurrence or more of words followed or not by '’-
    # | means or (word characters or punctuation)    
    # where the punctuation is [      ] within this set
    # [ ; : ! ? < > & ( )  \[    \]   to interpret these not as metacharacters but as [  ] characters itself  
    # [ ; : ! ? < > & ( )  \[  \]   \" to not interpret " has a close sign
    # [ ; : ! ? < > & ( )  \[  \]  \"  \. , = / \\ (to not interpret \ as an escaoe signal)]
    # Not adding spaces on ' and - when they are attached to words
    # And also not substituting isolated '’- with white spaces 
    print("Reading corpus...\n")
    
    regex = re.compile("[\w'’-]+|[;:!?<>&\(\)\[\]\"\.,=/\\\^\$\*\+\|\{\}]|[\S'’-]+")
    
    text_split_str = ""
    text_split_list = []
    

    # with - execute the operations as pairs
    for file_name in os.listdir(CORPUS_FOLDER_PATH):  
        
        with open(CORPUS_FOLDER_PATH + file_name, "r", encoding="utf8") as f:
            text = f.read()
            
            # remove doc identification strings
            textWithoutDoc = re.sub('<doc(.*?)>' , " ", text)
            
            # find the regex defined in text
            text_list = re.findall(regex, textWithoutDoc)
             
            text_split_str += " ".join(text_list)
            text_split_list.extend(text_list)

    return text_split_list


text_split_list = readCorpus()

print("Corpus read in %s seconds\n" % (time.time() - start_time))

n_grams = list(everygrams(text_split_list, min_len=1, max_len=7)) # invert to iterate from 7-grams to 1-grams

n_grams_freq = FreqDist(n_grams)

n_grams = sorted(set(n_grams), key = len, reverse = True)

word_count = len(text_split_list)  

seq = dict()

getSize = np.frompyfunc(len,1,1)

oneGram_Index = np.argmax(getSize(n_grams) < 2) # for n-gram with n > 2, because the cohesion is not calculated for n = 1

mwu = set()

getEntry = seq.get   
cohesion_gram = cohesion_measures 
add = mwu.add

with open("{}-{}-mwu.txt".format(CORPUS_FOLDER_PATH[:-1], COHESION_MEASURE), "w+", encoding="utf-8") as file: # w+ for both reading and writting file, overwritting the file
    for n_gramIndex in range(0, oneGram_Index):  
        
        n_gram = n_grams[n_gramIndex]
        
        left_gram = n_gram[:len(n_gram) - 1]
        right_gram = n_gram[1:]

        n_gram_freq = n_grams_freq[n_gram]
        n_gram_cohesion = cohesion_gram(COHESION_MEASURE, n_gram)
        
        # since we start from both, we only assign values to n-1 levels, since we don't need the values of the cohesion of sevengrams stored
        left_gram_freq = n_grams_freq[left_gram]
        left_gram_cohesion =  cohesion_gram(COHESION_MEASURE, left_gram) # E.g. United States of America - United States Of
        
        right_gram_freq = n_grams_freq[right_gram]
        right_gram_cohesion = cohesion_gram(COHESION_MEASURE, right_gram) # E.g. United States of America - States of America
        
        # left sub_gram        
        if  getEntry(left_gram):            
                max_cohesion = seq[left_gram][2]    
                if (n_gram_cohesion >  max_cohesion):
                    seq[left_gram][2] = n_gram_cohesion 

        else:
            seq[left_gram] = [left_gram_freq, left_gram_cohesion, n_gram_cohesion]
        
        # right sub_gram
        if  getEntry(right_gram):
                max_cohesion = seq[right_gram][2]
                if(n_gram_cohesion > max_cohesion):
                    seq[right_gram][2] = n_gram_cohesion    
        else:
            seq[right_gram] = [right_gram_freq, right_gram_cohesion, n_gram_cohesion]
        
        # Find Relevant Expressions
        if(len(n_gram) < 7):
            if(n_gram_freq >= 2): # If the n_gram appears at least 2 times in corpus

                if(len(n_gram) == 2):
                    if(n_gram_cohesion > seq[n_gram][2]):  
                        add((n_gram_cohesion, " ".join(n_gram)))
    
                else:           
                    x = max(left_gram_cohesion, right_gram_cohesion)
                    y = seq[n_gram][2]
     
                    if  (n_gram_cohesion > (x + y) / 2 ):
                        add((n_gram_cohesion, " ".join(n_gram)))
        
    file.write(str(mwu))

# sort the relevant expressions found
random_mwu = sample(mwu, 200)

# write the first 200 relevant expressions to calculate precision
with open("{}-{}-200random-mwu.txt".format(CORPUS_FOLDER_PATH[:-1], COHESION_MEASURE), "w", encoding="utf-8") as file:
    for exp in random_mwu:
        file.write(str(exp) + "\n")

print("--- Program ended in %s seconds ---" % (time.time() - start_time))