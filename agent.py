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
# Intelligent Agent
################################################################################

class Agent:
    def __init__(self, game):
        self.game = game
        self.old_pos = (0,0)
        self.pos = (0,0)
        self.move_list = [] # list of pos, input, action index
        self.nn = NeuralNet([9,4,1])
        self.name2num_dict = {}
        names = "ime_012345678f"
        for i in range(len(names)):
            self.name2num_dict[names[i]] = i - 4
        self.human = 0

    def switch(self):
        self.human = 1 - self.human
            
    def clearMoves(self):
        self.move_list = []

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

        x, y = self.pos
        self.old_pos = self.pos

        area = self.getArea(x,y,int(math.sqrt(self.nn.layers_list[0])))
        input = []
        for pos in area:
            try:
                name = self.game.board[pos]
                print name
                num = self.name2num_dict[name]
                print num
                input.append(num)
            except:
                print 'here'
                input.append(1)

        if self.human:
            action = 0
            output = [0]

            # check for events
            for event in pygame.event.get() :
                if event.type == QUIT:
                    self.game.running = False
                    pygame.quit()
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
                            action = 1
                    if event.button == 3:
                        self.game.mark(self.pos)
                        action = -1

            # if you move
            if self.old_pos != self.pos:
                x_o, y_o = self.old_pos
                x_n, y_n = self.pos

                '''# N = 2, E = 3, S = 4, W = 5
                if x_n > x_o: action = 3
                if x_n < x_o: action = 5
                if y_n > y_o: action = 4
                if y_n < y_o: action = 2
                '''
                action = 0
                
            print output
            
            # remember where you were
            self.move_list.append([self.pos, input, output, action, cleared])

            # train
            for i in range(10):
                self.nn.train(input, output)

        else:
            for event in pygame.event.get() :
                if event.type == QUIT:
                    self.game.running = False
                    pygame.quit()
                if event.type == KEYDOWN and event.key == K_ESCAPE:
                    self.game.running = False
                if event.type == KEYDOWN and event.key == K_h:
                    self.game.done = True
                    self.game.agent_index = 0



            print input
            output = self.nn.getOut(input)
            action = output[0]
            print action

            if action > .7: # left click
                cleared = self.game.dig((x,y)) # how many spaces we cleared
                action = 1

            elif action < -.7: # right click
                self.game.mark((x,y))
                action = -1

            else: action = 0
            move = random.randint(2,6)

            if move == 2:
                y -= 1
                #print "move north"

            elif move == 3:
                x += 1
                #print "move east"

            elif move == 4:
                y += 1
                #print "move south"

            elif move == 5:
                x -= 1
                #print "move west"

        # slide along the wall
        if x < 0: x = 0
        if x > self.game.width - 1: x = self.game.width - 1
        if y < 0: y = 0
        if y > self.game.height - 1: y = self.game.height - 1

        # remember where you were
        self.move_list.append([self.pos, input, output, action, cleared])

        # update yourself
        self.pos = (x, y)
        if self.old_pos == self.pos:
            #print "in same place, ", x, y
            self.nn.train(input, [1])

    def backPropogate(self, move, reward, threshold = .05, decay = .5):
        # while there's reward and states left
        while reward > threshold and move >= 0:
            # reward the state at i
            pos = self.move_list[move][0]
            input = self.move_list[move][1]
            output = self.move_list[move][2]
            action = self.move_list[move][3]
            
            output = [action * reward]
            self.nn.train(input, output)

            # then reduce your reward and move to the previous state
            move -= 1
            reward *= decay

    def learn(self):
        # go through each move and back propogate rewards
        for i in range(len(self.move_list)):
            move = self.move_list[i]

            # if you're not at the end of the list
            if i != len(self.move_list) - 1:
                # if the state doesn't change and you were moving
                if move[1] == self.move_list[i+1][1] and move[3] >= 2:
                    self.backPropogate(i, -1)

            if move[3] == 0: # if you left clicked
                if self.game.mine_array[move[0]]:
                    self.backPropogate(i, -10)
                    #print "explosion"
                elif move[4] >= 1:
                    self.backPropogate(i, 100 * move[4])
                    #print "you cleared ", move[4], " mines"


            # check this method for validity
            if move[3] == 1:
                if self.game.board[move[0]] == "i" : # if a flag is incorrectly placed
                    self.backPropogate(i, -10)
                    #print "incorrect flagging"

                if self.game.board[move[0]] == "f": # if correctly flagged
                    self.backPropogate(i, 1000)
                    #print "successful flag"

    def reward(self, i, amt):
        self.state.rewards[i] += amt

    def punish(self, i, amt):
        self.reward(i, -amt)

    def setPos(self, pos):
        self.pos = pos
