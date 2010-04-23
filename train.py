#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       train.py
#       
#       Copyright 2010 Nolan Baker <hendersonhasselbalch@gmail.com>
#       
#       This program is free software; you can redistribute it and/or modify
#       it under the terms of the GNU General Public License as published by
#       the Free Software Foundation; either version 2 of the License, or
#       (at your option) any later version.
#       
#       This program is distributed in the hope that it will be useful,
#       but WITHOUT ANY WARRANTY; without even the implied warranty of
#       MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#       GNU General Public License for more details.
#       
#       You should have received a copy of the GNU General Public License
#       along with this program; if not, write to the Free Software
#       Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#       MA 02110-1301, USA.


RULES_ONLY = False
RUNS = 10
ALPHA = .5
BETA = .1
NN_NAME = "bigA_nn.obj"
ML_NAME = "ml.obj"
import pickle, random, os
from neural_network import *

def main():
    
    dict = {}
    names = "_012345678f"
    for i in range(len(names)):
        nodes = [0] * 11
        nodes[i] = 1
        dict[str(nodes)] = names[i]
    dict[str([0,0,0,0,0,0,0,0,0,0,0])] = "X"
            
    f = open(os.path.join("data",ML_NAME), "r")
    moves = pickle.load(f)
    print len(moves), "moves"
    random.shuffle(moves)
    f.close()
    
    a = 25*11
    b = 9
    nn = NeuralNet(a,a,b)
    
    t = 0
    for i in range(RUNS):
        print "run", i
        m = 0
        for move in moves:
            m += 1
            if m % 1000 == 0:
                print "."
            center = dict[str(move[0][12*11:13*11])]
            if center in "12345678":
                center = int(center)
            else: center = -1
            sum = 0
            nums = [6,7,8,11,12,13,16,17,18]
            for i in nums:
                if dict[str(move[0][i*11:(i+1)*11])] in "_f":
                    sum += 1
            if not RULES_ONLY or center == sum:
                t += 1
                nn.train(move[0], move[1], ALPHA, BETA)
        random.shuffle(moves)
    print t, "examples"
    print "done training"    
    f = open(os.path.join("data", NN_NAME), "w")
    pickle.dump(nn, f)
    print "saved nn as ", NN_NAME
    f.close()

if __name__ == '__main__':
    main()
