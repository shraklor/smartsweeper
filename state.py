#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       state.py
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

################################################################################
# THIS ONE IS NOT USED ANY LONGER
################################################################################

import random, pygame, os, math
from numpy import *
import numpy.random as nrand
################################################################################
# State-action-reward thing
################################################################################
class State:
    def __init__(self, array, rewards = [100,-100,0,0,0,0,0]):
        self.actions = "LRJNESW"
        self.rewards = rewards
        self.getSym(array)
        self.action_index = 0

    def printArray(self, array):
        for i in range(3):
            for j in range(3):
                print(array[i][j]),
            print()

    def printSym(self):
        for sym in self.sym:
            self.printArray(sym)
            print

    def getSym(self, a):
        # creates a list of 3x3 arrays symmetrical to the one passed
        # and changes directions to match

        rot0 = [[a[0][0],a[0][1],a[0][2]],
                [a[1][0],a[1][1],a[1][2]],
                [a[2][0],a[2][1],a[2][2]]]

        rot1 = [[a[2][0],a[1][0],a[0][0]],
                [a[2][1],a[1][1],a[0][1]],
                [a[2][2],a[1][2],a[0][2]]]

        rot2 = [[a[2][2],a[2][1],a[2][0]],
                [a[1][2],a[1][1],a[1][0]],
                [a[0][2],a[0][1],a[0][0]]]

        rot3 = [[a[0][2],a[1][2],a[2][2]],
                [a[0][1],a[1][1],a[2][1]],
                [a[0][0],a[1][0],a[2][0]]]

        flip0 = [[a[0][2],a[0][1],a[0][0]],
                 [a[1][2],a[1][1],a[1][0]],
                 [a[2][2],a[2][1],a[2][0]]]

        flip1 = [[a[0][0],a[1][0],a[2][0]],
                 [a[0][1],a[1][1],a[2][1]],
                 [a[0][2],a[1][2],a[2][2]]]

        flip2 = [[a[2][0],a[2][1],a[2][2]],
                 [a[1][0],a[1][1],a[1][2]],
                 [a[0][0],a[0][1],a[0][2]]]

        flip3 = [[a[2][2],a[1][2],a[0][2]],
                 [a[2][1],a[1][1],a[0][1]],
                 [a[2][0],a[1][0],a[0][0]]]

        self.sym = [rot0, rot1, rot2, rot3,
                    flip0, flip1, flip2, flip3]

        self.moves = ["NESW", "WNES", "SWNE", "ESWN",
                      "NWSE", "WSEN", "SENW", "ENWS"]

    def isMatch(self, array):
        # run through each symmetry
        for i in range(8):
            # if we find a match
            if array == self.sym[i]:
                # change the actions accordingly
                self.actions = self.actions[:3] + self.moves[i]
                # and return yes
                return True
        # otherwise, return no
        return False

    def getAction(self):
        #print self.actions # a string of moves
        #print self.rewards # a list of rewards

        self.action_index = 0
        reward = -9999999999999
        #print "$", reward, self.rewards[0]
        # check all actions
        for i in range(len(self.rewards)):
            r = self.rewards[i]

            # keep group of rewards
            # find maximum reward
            if r > reward:
                reward = r
                self.action_index = i
            #print "$", reward, r


        self.action_index = random.randint(0,len(self.rewards) - 1)
        r = self.rewards[self.action_index]
        a = self.actions[self.action_index]
        #print a
        return r, a

################################################################################
# example
################################################################################

a = [["_","N","_"],
     ["W","_","E"],
     ["_","S","_"]]
state = State(a)
print state.actions

b = [["_","S","_"],
     ["W","_","E"],
     ["_","N","_"]]

c = [["_","S","_"],
     ["N","_","W"],
     ["_","E","_"]]

d = [["_","S","_"],
     ["E","_","W"],
     ["_","N","_"]]
print state.isMatch(b)
print state.actions

print state.isMatch(c)
print state.actions

print state.isMatch(d)
print state.actions

state.printSym()