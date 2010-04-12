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
from state import *
from neural_network import *

ALPHA = .1
BETA = .01
MAX_MOVES = 10000
MOVES_LEARNED = 420
THRESH = .012
INITIAL = .022
INPUT_GRID = 5
OUTPUT_GRID = 3
CHANGE = 1.007
WEIGHT = .3

################################################################################
# Intelligent Agent
################################################################################

class Agent:
    def __init__(self, game):
        self.game = game
        self.clearMoves()
        self.name2num_dict = {}
        names = "_012345678f"
        self.in_size = len(names)
        for i in range(len(names)):
            nodes = [0] * len(names)
            nodes[i] = 1
            self.name2num_dict[names[i]] = nodes
        a = (INPUT_GRID**2)*len(names)
        b = OUTPUT_GRID**2
        self.nn = NeuralNet(a,int((3*a+2*b)/5),b)
        self.human = 0
        self.cheat = False
        self.memory = []

    def switch(self):
        self.human = 1 - self.human

    def clearMoves(self):
        self.num_moves = 0
        self.closed = []
        self.thresh = INITIAL# * random.uniform(.001, 10)
        x = random.randint(0,self.game.width)
        y = random.randint(0,self.game.height)
        self.old_pos = (x,y)
        self.pos = (x,y)
        self.old_action = "L"
        self.action = "L"
        self.move_list = []
        #self.guess = {}
        self.visited = {}
        for i in range(self.game.width):
            for j in range(self.game.height):
                #self.guess[(i,j)] = .5
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

    def threshClick(self):
        x,y = self.pos
        # get the guess for the space you're on
        out = self.game.guess[self.pos]

        name = self.game.board[self.pos]
        self.thresh *= CHANGE
        m = self.num_moves
        if m == MAX_MOVES:
            print "max moves exceeded"
        if m < MAX_MOVES:
            if out <= self.thresh and name != "f":
                #print "dig"
                self.close(self.pos)
                cleared = self.game.dig(self.pos) # how many spaces we cleared
                #self.visited[(x,y)] += 5
                if name not in "012345678":
                    self.thresh = THRESH
            elif (out <= self.thresh and name == "f"):
                #print "unflag"
                #self.open(self.pos)
                self.game.mark(self.pos)
                self.thresh = THRESH
            elif (out >= (1 - self.thresh) and name != "f"):
                #print "flag"
                self.close(self.pos)
                self.game.mark(self.pos)
                #self.visited[self.pos] += 5
                self.thresh = THRESH

        # if you've gone so many moves without ending the game, do it
        elif name == "f":
            self.game.mark(self.pos)
            self.game.throwTowel()
        else:
            self.game.dig(self.pos)
            self.game.throwTowel()

        if name == "0":
            self.visited[(x,y)] += 10

    def simMove(self):
        ############################################################
        # MOVEMENT
        ############################################################
        x,y = self.pos
        # if you're on green, move to brown (most of the time)
        von_neumann = [(x,y+1),(x,y-1),(x+1,y),(x-1,y)]
        possible = []
        if random.random() < 0.7:
            for pos in self.area:
                if self.pos == pos:
                    continue
                try:
                    a = self.game.board[self.pos]
                    grn = "_f"
                    brn = "012345678"
                    if (a in grn) and (self.game.board[pos] in brn):
                        possible.append(pos)
                    #if ((a in brn) and
                    #    (self.game.board[pos] in grn) and
                    #    (pos in von_neumann)):
                    #    possible.append(pos)
                except: pass

        # if this isn't possible, anywhere is fine
        if len(possible) == 0:
            possible = self.area

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
        if random.random() < 0.7:
            random.shuffle(self.best_guesses)
            self.pos = self.best_guesses[0]

        # and go to it
        else:
            self.pos = s[0]
        self.visited[self.pos] += 1

    def act(self):
        if not self.game.FINISHED:
            self.old_pos = self.pos
            x,y = self.pos

            # figure out where your are and what's around you
            self.area = self.getArea(x,y,OUTPUT_GRID)
            self.area2 = self.getArea(x,y,INPUT_GRID)

            # GET INPUT FROM AREA AROUND YOU
            input = []
            for pos in self.area2:
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
            for i in range(len(self.area)):
                pos = self.area[i]
                try:
                    num = self.game.mine_array[pos]
                    target.append(num)
                except:
                    target.append(.5)


            ################################################################
            # get output from neural net
            ################################################################
            output = self.nn.getOut(input)

            # uncomment this to play perfectly (cheat)
            # for learning examples quicker
            if self.cheat:
                print "cheating"
                output = target

            # update your guesses for whether or not a square has a mine
            for i in range(OUTPUT_GRID**2):
                try:
                    output[i] = self.game.guess[self.area[i]] * (1-WEIGHT) + output[i] * WEIGHT
                    self.game.guess[self.area[i]] = output[i]
                except:
                    pass # this just means we're looking out of bounds

            ################################################################
            # Q STUFF
            ################################################################
            out_array = []
            count = 0
            for a in range(OUTPUT_GRID):
                out_array.append([])
                for b in range(OUTPUT_GRID):
                    try:
                        if output[count] < .5: o = 0
                        elif self.game.board[self.pos] == "f": o = -1
                        else: o = 1
                        out_array[a].append(o)
                        count += 1
                    except:
                        out_array[a].append(0)
            found = False
            for s in self.memory:
                found = s.isMatch(out_array)
                if found:
                    state = s
                    break
            if not found:
                state = State(out_array)
                self.memory.append(state)

            action_i = state.getActionIndex()
            action = state.actions[action_i]

            ################################################################
            # EVENT LOOP - if you're drawing the board, check for events
            ################################################################
            if self.human:
                found = False
                while not found:
                    event = pygame.event.wait()
                    # if the keyboard is used
                    if event.type == KEYDOWN:
                        if event.key == K_ESCAPE:
                            self.game.running = False
                            found = True
                            pygame.quit ()

                    if event.type == MOUSEMOTION:
                        self.old_pos = self.pos
                        self.pos = self.mouse2Grid(event.pos)
                        x, y = self.pos
                        a, b = self.old_pos
                        if self.old_pos != self.pos:
                            if x > a:
                                state.reward("E")
                                state.punish("W")
                            if x < a:
                                state.reward("W")
                                state.punish("E")
                            if y > a:
                                state.reward("S")
                                state.punish("N")
                            if y < a:
                                state.reward("N")
                                state.punish("S")
                            found = True

                    if event.type == QUIT:
                        self.game.running = False
                        found = True
                        pygame.quit ()

                    # if something is clicked
                    elif event.type == MOUSEBUTTONDOWN:
                        if event.button == 1:
                            cleared = self.game.dig(self.pos)
                            found = True
                            state.reward("L")
                            state.punish("R")
                        if event.button == 3:
                            self.game.mark(self.pos)
                            found = True
                            state.reward("R")
                            state.punish("L")

            ################################################################
            # BOT SPECIFIC STUFF
            ################################################################
            if not self.human:
                self.threshClick()
                self.getCertainty()
                self.simMove()
                '''
                x, y = self.pos

                if action == "L":
                    self.game.dig(self.pos)
                elif action == "R":
                    self.game.mark(self.pos)
                elif action == "N":
                    y -= 1
                elif action == "E":
                    x += 1
                elif action == "S":
                    y += 1
                elif action == "W":
                    x -= 1
                elif action == "J":
                    x = random.randint(0, self.game.width - 1)
                    y = random.randint(0, self.game.height - 1)

                if x < 0: x = 0
                if x > self.game.width: x = self.game.width
                if y < 0: y = 0
                if y > self.game.height: y = self.game.height
                self.pos = x, y
                '''
            ################################################################
            # Remember what you've done.
            ################################################################
            self.move_list.append([self.pos, input, target])#, state, action_i])
            if self.num_moves > MOVES_LEARNED:
                r = random.randint(0, len(self.move_list))
                self.move_list = self.move_list[:r] + self.move_list[r+1:]
            self.num_moves += 1
            if self.num_moves == MOVES_LEARNED:
                print "truncating move list"
            if self.num_moves == MAX_MOVES / 10:
                print "10%"
            if self.num_moves == MAX_MOVES / 4:
                print "1/4"
            if self.num_moves == MAX_MOVES / 2:
                print "half way"

    def getCertainty(self):
        ############################################################
        # how certain are you that you've chosen correctly
        ############################################################
        self.best_guesses = [self.pos]
        best = self.pos
        lowest_errors = [1]
        lowest = 1
        global_certainty = 0
        local_certainty = 0
        for i in range(self.game.width):
            for j in range(self.game.height):
                g = self.game.guess[(i,j)]
                err = min(g, 1-g) ** 2
                global_certainty += 1 - err
                if (i,j) in self.area:
                    local_certainty += 1 - err
                if (i,j) in self.closed:
                    continue
                if err < max(lowest_errors):
                    lowest_errors.append(err)
                    self.best_guesses.append((i,j))
                    if len(self.best_guesses) > 10:
                        self.best_guesses = self.best_guesses[1:]
                        lowest_errors = lowest_errors[1:]
                    if err < lowest:
                        best = (i,j)
                        lowest = err

        global_certainty /= float(self.game.width * self.game.height)
        local_certainty /= float(self.game.width * self.game.height)

    def QLearn(self, move, reward, threshold = .05, decay = .7):
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

    def open(self, pos):
        if pos in self.closed:
            self.closed.remove(pos)

    def close(self, pos):
        if pos not in self.closed:
            self.closed.append(pos)

    def learn(self):
        for i in range(15):
            move = self.move_list[-1]
            self.nn.train(move[1], move[2], ALPHA * 3, BETA * 3)
        # go through each move and back propogate rewards
        for i in range(len(self.move_list)):
            move = self.move_list[i]
            a = 1#random.uniform(.001, 2)
            b = 1#random.uniform(.0001, 1)
            self.nn.train(move[1], move[2], ALPHA * a, BETA * b)
            #q-learn

    def reward(self, i, amt):
        self.state.rewards[i] += amt

    def punish(self, i, amt):
        self.reward(i, -amt)

    def setPos(self, pos):
        self.pos = pos

    def getNumMineGuess(self):
        sum = 0
        for guess in self.game.guess.values():
            if guess > .5:
                sum += 1
        return sum
