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

################################################################################
# Human teacher
################################################################################

class Human:
    def __init__(self, game):
        self.game = game
        self.old_pos = (0,0)
        self.pos = (0,0)
        self.move_list = [] # list of pos, input, action index
        input = 25
        self.nn = NeuralNet([25,12,6])
        self.name2num_dict = {}
        names = "_012345678fime"
        for i in range(len(names)):
            self.name2num_dict[names[i]] = i

    def clearMoves(self):
        self.move_list = []

    def mouse2Grid(self, pos):
        x, y = pos
        x = int(x / self.game.tile_size)
        y = int(y / self.game.tile_size)
        return (x, y)

    def act(self):

        self.old_pos = self.pos
        self.pos = self.mouse2Grid(pygame.mouse.get_pos())
        x, y = self.pos

        area = [(x-1, y-1), (x, y-1), (x+1, y-1),
                (x-1, y  ), (x, y  ), (x+1, y  ),
                (x-1, y+1), (x, y+1), (x+1, y+1)]

        big = [(x-2, y-2), (x-1, y-2), (x  , y-2), (x+1, y-2), (x+2, y-2),
               (x-2, y-1), (x-1, y-1), (x  , y-1), (x+1, y-1), (x+2, y-1),
               (x-2, y  ), (x-1, y  ), (x  , y  ), (x+1, y  ), (x+2, y  ),
               (x-2, y+1), (x-1, y+1), (x  , y+1), (x+1, y+1), (x+2, y+1),
               (x-2, y+2), (x-1, y+2), (x  , y+2), (x+1, y+2), (x+2, y+2)]

        if self.nn.layers_list[0] == 25:
            area = big

        input = []
        for pos in area:
            try:
                name = self.game.board[pos]
                num = self.name2num[name]
                input.append(num)
            except: input.append(0)

        output = [0,0,0,0,0,0]

        # check for events
        for event in pygame.event.get() :
            if event.type == QUIT:
                self.game.running = False
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                self.game.running = False
            if event.type == KEYDOWN and event.key == K_r:
                self.game.done = True
                self.game.agent_index = 1

            # if something is clicked
            if event.type == MOUSEBUTTONDOWN:
                if event.button == 1:
                    cleared = self.game.dig(self.pos)
                    if cleared > 0:
                        output[0] = 1
                if event.button == 3:
                    self.game.mark(self.pos)
                    output[1] = 1

        # if you move
        if self.old_pos != self.pos:
            x_o, y_o = self.old_pos
            x_n, y_n = self.pos

            # N = 2, E = 3, S = 4, W = 5
            if x_n > x_o: output[3] = 1
            if x_n < x_o: output[5] = 1
            if y_n > y_o: output[4] = 1
            if y_n < y_o: output[2] = 1


        # remember where you were
        self.move_list.append([self.pos, input, output])

        # train
        self.nn.train(input, output)

################################################################################
# Agent with a memory
################################################################################
class Agent:
    def __init__(self, game, nn):
        self.game = game
        self.old_pos = (0,0)
        self.pos = (0,0)
        self.move_list = [] # list of pos, input, action index
        self.nn = nn
        self.name2num_dict = {}
        names = "_012345678fime"
        for i in range(len(names)):
            self.name2num_dict[names[i]] = i

    def clearMoves(self):
        self.move_list = []

    def printMove(move):
        pass

    def act(self):
        for event in pygame.event.get() :
            if event.type == QUIT:
                self.game.running = False
            if event.type == KEYDOWN and event.key == K_ESCAPE:
                self.game.running = False
            if event.type == KEYDOWN and event.key == K_h:
                self.game.done = True
                self.game.agent_index = 0

        cleared = 0

        x, y = self.pos
        self.old_pos = self.pos

        area = [(x-1, y-1), (x, y-1), (x+1, y-1),
                (x-1, y  ), (x, y  ), (x+1, y  ),
                (x-1, y+1), (x, y+1), (x+1, y+1)]

        big = [(x-2, y-2), (x-1, y-2), (x  , y-2), (x+1, y-2), (x+2, y-2),
               (x-2, y-1), (x-1, y-1), (x  , y-1), (x+1, y-1), (x+2, y-1),
               (x-2, y  ), (x-1, y  ), (x  , y  ), (x+1, y  ), (x+2, y  ),
               (x-2, y+1), (x-1, y+1), (x  , y+1), (x+1, y+1), (x+2, y+1),
               (x-2, y+2), (x-1, y+2), (x  , y+2), (x+1, y+2), (x+2, y+2)]

        if self.nn.layers_list[0] == 25:
            area = big

        input = []
        for pos in area:
            try:
                name = self.game.board[pos]
                num = self.name2num[name]
                input.append(num)
            except: input.append(0)

        output = self.nn.getOut(input)
        action = self.nn.getActionIndex()

        if action == 0: # left click
            cleared = self.game.dig((x,y)) # how many spaces we cleared

        elif action == 1:# or action == 1: # right click
            self.game.mark((x,y))

        move = random.randint(0,4)

        if action == 2:
            y -= 1
            print "move north"

        elif action == 3:
            x += 1
            print "move east"

        elif action == 4:
            y += 1
            print "move south"

        elif action == 5:
            x -= 1
            print "move west"

        # slide along the wall
        if x < 0: x = 0
        if x > self.game.width - 1: x = self.game.width - 1
        if y < 0: y = 0
        if y > self.game.height - 1: y = self.game.height - 1

        # remember where you were
        self.move_list.append([self.pos, input, action])

        # update yourself
        self.pos = (x, y)
        if self.old_pos == self.pos:
            print "in same place, ", x, y
            #self.nn.train(input, [1,0,0,0,0,0])

    def backPropogate(self, i, reward, threshold, decay = .5):
        # while there's reward and states left
        while reward > threshold and i >= 0:
            # reward the state at i
            input = self.move_list[i][1]
            output = self.move_list[i][2]
            index = self.move_list[i][3]
            output[index] += reward
            self.nn.train(input, output)

            # then reduce your reward and move to the previous state
            i -= 1
            reward *= decay

    def learn(self):
        # go through each move and back propogate rewards
        for i in range(len(self.move_list)):
            move = self.move_list[i]

            # if you're not at the end of the list
            if i != len(self.move_list) - 1:
                # and the state doesn't change
                if move[1] == self.move_list[i+1][1]:
                    self.backPropogate(i, -1, .2)

            if move[3] > 0: # if there was extra clearededge
                self.backPropogate(i, 1, .2)

            if self.game.board[move[0]] == "i": # if a flag is incorrectly placed
                self.backPropogate(i, -1, .2)


    def reward(self, i, amt):
        self.state.rewards[i] += amt

    def punish(self, i, amt):
        self.reward(i, -amt)

    def setPos(self, pos):
        self.pos = pos
