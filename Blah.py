from __future__  import division
import nltk
import A
from collections import defaultdict
import itertools
import math as math
from nltk.align import Alignment, AlignedSent
import sys


from collections import defaultdict
from nltk.align  import AlignedSent
from nltk.corpus import comtrans
from nltk.align.ibm1 import IBMModel1
class BerkeleyAligner():
    def __init__(self, align_sents, num_iter):
        self.t, self.q = self.train(align_sents, num_iter)


    # TODO: Computes the alignments for align_sent, using this model's parameters. Return
    #       an AlignedSent object, with the sentence pair and the alignments computed.
    def align(self, align_sent):
        alignment = []

        l = len(align_sent.words)
        m = len(align_sent.mots)

        for j, en_word in enumerate(align_sent.words):
            
            # Initialize the maximum probability with Null token
            max_align_prob = (self.t[en_word][None]*self.q[(0,j+1,l,m)], None)
            for i, g_word in enumerate(align_sent.mots):
                # Find out the maximum probability
                max_align_prob = max(max_align_prob,
                    (self.t[en_word][g_word]*self.q[(i+1,j+1,l,m)], i))

            # If the maximum probability is not Null token,
            # then append it to the alignment. 
            if max_align_prob[1] is not None:
                alignment.append((j, max_align_prob[1]))

        return AlignedSent(align_sent.words, align_sent.mots, alignment)

        
    # TODO: Implement the EM algorithm. num_iters is the number of iterations. Returns the 
    # translation and distortion parameters as a tuple.
    def getCounts(self, aligned_sents, num_iter, e_to_g):
        print 'training'
        # ibm1 = IBMModel1(aligned_sents, 10)
        # t = ibm1.probabilities

        german_vocab = set()
        english_vocab = set()
        if e_to_g == True:
            for alignSent in aligned_sents:
                english_vocab.update(alignSent.mots)
                german_vocab.update(alignSent.words)
            german_vocab.add(None)
        else: 
            for alignSent in aligned_sents:
                english_vocab.update(alignSent.words)
                german_vocab.update(alignSent.mots)
            german_vocab.add(None)

        t = defaultdict(lambda: defaultdict(lambda: 0.0))
        if e_to_g == True:
            for word in german_vocab:
                possibles = []
                for sent in aligned_sents:
                    if word in sent.words:
                        possibles += sent.mots
                possibles = set(possibles)
                length = len(possibles)
                for possible in possibles:
                    t[possible][word] = 1/float(length)
        else:
            for word in german_vocab:
                possibles = []
                for sent in aligned_sents:
                    if word in sent.mots:
                        possibles += sent.words
                possibles = set(possibles)
                length = len(possibles)
                for possible in possibles:
                    t[possible][word] = 1/float(length)

        q = defaultdict(float)

        for alignSent in aligned_sents:
            english = alignSent.mots if e_to_g else alignSent.words
            german = [None] + alignSent.words if e_to_g else [None] + alignSent.mots
            m = len(german) - 1
            l = len(english)
            initial_value = 1 / (m + 1)
            for i in range(0, m+1):
                for j in range(1, l+1):
                    q[(i,j,l,m)] = initial_value

        print 'collecting counts'
        for i in range(0, num_iter):
            c = defaultdict(float)
            total_e = defaultdict(float)

            for alignSent in aligned_sents:
                english = alignSent.mots if e_to_g else alignSent.words
                german = [None] + alignSent.words if e_to_g else [None] + alignSent.mots
                m = len(german) - 1
                l = len(english)

                #normalize
                for j in range(1, l+1):
                    en_word = english[j-1]
                    total_e[en_word] = 0
                    for i in range(0, m+1):
                        total_e[en_word] += t[en_word][german[i]] * q[(i,j,l,m)]

                #calculate counts
                for j in range(1, l+1):
                    en_word = english[j-1]
                    for i in range(0, m+1):
                        g_word = german[i]
                        delta = t[en_word][g_word] * q[(i,j,l,m)] / total_e[en_word]
                        c[(en_word,g_word)] += delta
                        c[g_word] += delta
                        c[(i,j,l,m)] += delta
                        c[(j,l,m)] += delta
        return c
    def train(self, aligned_sents, num_iter):
        german_vocab = set()
        english_vocab = set()
        for alignSent in aligned_sents:
            english_vocab.update(alignSent.words)
            german_vocab.update(alignSent.mots)
        german_vocab.add(None)

        c = self.getCounts(aligned_sents, num_iter, False) 
        c1 = self.getCounts(aligned_sents, num_iter, True) 

        for k in range(0, num_iter):

            t = defaultdict(lambda: defaultdict(lambda: 0.0))
            q = defaultdict(float)

            # calculate t and q
            print 'calculating t and q'
            for f,e in itertools.product(german_vocab, english_vocab):
                t[e][f] = (c[(e,f)] + c1[(f,e)])/ (c[f] + c1[e])

            for alignSent in aligned_sents:
                english = alignSent.words
                german = [None] + alignSent.mots
                m = len(german) - 1
                l = len(english)
                for i in range(0, m+1):
                    for j in range(1, l+1):
                        q[(i,j,l,m)] = (c[(i,j,l,m)] +  c1[(j,i,m,l)]) / (c[(j,l,m)] + c1[(i,m,l)] )

        return t, q


def main(aligned_sents):
    ba = BerkeleyAligner(aligned_sents, 10)
    #A.save_model_output(aligned_sents, ba, "ba.txt")
    avg_aer = A.compute_avg_aer(aligned_sents, ba, 50)

    print ('Berkeley Aligner')
    print ('---------------------------')
    print('Average AER: {0:.3f}\n'.format(avg_aer))