#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       agent.py
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

import random, pygame, os
from pygame.locals import *
from game import *
from neural_network import *

MAX_MOVES = 15000
THRESH = .044
################################################################################
# Intelligent Agent
################################################################################

class Agent:
    def __init__(self, game):
        self.game = game
        self.old_pos = (0,0)
        self.pos = (0,0)
        self.clearMoves()
        self.name2num_dict = {}
        names = "_012345678f"
        self.in_size = len(names)
        for i in range(len(names)):
            nodes = [0] * len(names)
            nodes[i] = 1
            self.name2num_dict[names[i]] = nodes
        self.nn = NeuralNet(25*len(names),100,9)
        self.human = 0
        self.cheat = False
        self.thresh = THRESH
        self.goggles = 1

    def switch(self):
        self.human = 1 - self.human
            
    def clearMoves(self):
        self.pos = (0,0)
        self.move_list = []
        self.guess = {}
        self.visited = {}
        for i in range(self.game.width):
            for j in range(self.game.height):
                self.guess[(i,j)] = .5
                self.visited[(i,j)] = 0        

    def mouse2Grid(self, pos):
        x, y = pos
        x = int(x / self.game.tile_size)
        y = int(y / self.game.tile_size)
        return (x, y)

    def getArea(self,x,y,n):
        area = []
        for j in range(n):
            b = y + j - int(n / 2)
            for i in range(n):
                a = x + i - int(n / 2)
                area.append((a, b))
        return area

    def boardArea(self):
        area = []
        for j in range(self.game.height):     
            for i in range(self.game.width):
                area.append((i,j))
        return area
   
    def act(self):
        cleared = 0

        self.old_pos = self.pos
        if self.human:
            self.pos = self.mouse2Grid(pygame.mouse.get_pos())
        x, y = self.pos
        
        # figure out where your are and what's around you
        area = self.getArea(x,y,3)
        area2 = self.getArea(x,y,5)


        # GET INPUT FROM AREA AROUND YOU
        input = []
        for pos in area2:
            try:
                name = self.game.board[pos]
                nodes = self.name2num_dict[name]
                input += nodes
            except:
                input += [0] * self.in_size

        # FIGURE OUT WHAT YOUR TARGET OUTPUT SHOULD BE
        # this is not used to determine where to go or what to do
        # it is only used durring the learning phase
        target = []
        for i in range(len(area)):
            pos = area[i]
            try:
                num = self.game.mine_array[pos]
                target.append(num)
            except: 
                target.append(.5)

        ################################################################
        # EVENT LOOP - if you're drawing the board, check for events
        ################################################################
        if self.game.draw_board:
            for event in pygame.event.get() :
                if event.type == QUIT:
                    self.game.running = False
                    return -1

                # if the keyboard is used
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        self.game.running = False
                    if ((event.key == K_r and self.human) or
                        (event.key == K_h and not self.human)):
                        self.switch()
                    if event.key == K_c:
                        self.cheat = bool(1 - int(self.cheat))
                    if event.key == K_g:
                        self.goggles = bool(1 - int(self.goggles))

                # if something is clicked
                elif event.type == MOUSEBUTTONDOWN and self.human:
                    if event.button == 1:
                        cleared = self.game.dig(self.pos)
                    if event.button == 3:
                        self.game.mark(self.pos)

        output = self.nn.getOut(input)

        # uncomment this to play perfectly (cheat)
        # for learning examples quicker
        if self.cheat:
            print "cheating"
            output = target
        
        # update your guesses for whether or not a square has a mine
        for i in range(9):
            try:
                self.guess[area[i]] = self.guess[area[i]] * .9 + output[i] * .1
            except:
                pass # this just means we're looking out of bounds

        ############################################################
        # how certain are you that you've chosen correctly
        ############################################################
        best_guesses = [self.pos]
        best = self.pos
        lowest_errors = [1]
        lowest = 1
        global_certainty = 0
        local_certainty = 0
        for i in range(self.game.width):
            for j in range(self.game.height):
                g = self.guess[(i,j)]
                err = min(g, 1-g) ** 2
                if err < max(lowest_errors):
                    lowest_errors.append(err)
                    best_guesses.append((i,j))
                    if len(best_guesses) > 2:
                        best_guesses = best_guesses[1:]
                        lowest_errors = lowest_errors[1:]
                    if err < lowest:
                        best = (i,j)
                        lowest = err
                global_certainty += 1 - err
                if (i,j) in area:
                    local_certainty += 1 - err
        global_certainty /= float(self.game.width * self.game.height)
        local_certainty /= float(self.game.width * self.game.height)

        ################################################################
        # BOT SPECIFIC STUFF
        ################################################################
        if not self.human:
                    # get the guess for the space you're on
            out = self.guess[self.pos]

            name = self.game.board[self.pos]
            self.thresh *= 1.01
            if len(self.move_list) < MAX_MOVES:
                if (out <= self.thresh and name == "f"):
                    self.game.mark(self.pos)
                    self.thresh = THRESH
                elif (out >= 1 - self.thresh and name != "f"):
                    self.game.mark(self.pos)
                    self.visited[self.pos] += 1
                    self.thresh = THRESH
                elif out <= self.thresh and name != "f":
                    cleared = self.game.dig(self.pos) # how many spaces we cleared
                    self.visited[(x,y)] += 5
                    if name not in "012345678":
                        self.thresh = THRESH

            # if you've gone so many moves without ending the game, do it
            elif name == "f":
                self.game.mark(self.pos)
                self.game.throwTowel()
            else:
                cleared = self.game.dig(self.pos)
                self.game.throwTowel()

            if name == "0":
                self.visited[(x,y)] += 10


            ############################################################
            # MOVEMENT
            ############################################################    

            # if you're on green, move to brown (most of the time)
            von_neumann = [(x,y+1),(x,y-1),(x+1,y),(x-1,y)]
            possible = []
            for pos in area:
                if self.pos == pos:
                    continue
                try:
                    a = self.game.board[self.pos]
                    grn = "_f"
                    brn = "012345678"
                    if (a in grn) and (self.game.board[pos] in brn):
                        possible.append(pos)
                    if ((a in brn) and
                        (self.game.board[pos] in grn) and
                        (pos in von_neumann)):
                        possible.append(pos)
                except: pass
                    
            # if this isn't possible, anywhere is fine
            if len(possible) == 0:
                possible = area
                
            # find the spot you've visited least
            m = 9999999999
            s = []
            for pos in possible:
                if pos == self.pos:
                    continue
                try:
                    v = self.visited[pos]
                    if v < m:
                        m = v
                        s = [pos]
                    elif v == m:
                        s.append(pos)                    
                except:
                    pass
            random.shuffle(s)

            # move to the best guess on the board
            """
            if random.random() > .99:
                print "here"
                random.shuffle(best_guesses)
                self.pos = best_guesses[0]
            """
            # and go to it
            self.pos = s[0]
            self.visited[self.pos] += 1

        ################################################################
        # Remember what you've done.
        ################################################################
        self.move_list.append([self.pos, input, target])

    def backPropogate(self, move, reward, threshold = .05, decay = .7):
        # while there's reward and states left
        while reward > threshold and move >= 0:

            # reward the state at 'move', an int
            pos = self.move_list[move][0]
            input = self.move_list[move][1]
            n = max(max(input), 0)
            target = self.move_list[move][2]
            
            for i in range(n):
                self.nn.train(input, target, reward)

            # then reduce your reward and move to the previous state
            move -= 1
            reward *= decay

    def learn(self):
        # go through each move and back propogate rewards
        for move in self.move_list:
            self.nn.train(move[1], move[2])
        
    def reward(self, i, amt):
        self.state.rewards[i] += amt

    def punish(self, i, amt):
        self.reward(i, -amt)

    def setPos(self, pos):
        self.pos = pos

    def getNumMineGuess(self):
        sum = 0
        for guess in self.guess.values():
            if guess > .5:
                sum += 1
        return sum