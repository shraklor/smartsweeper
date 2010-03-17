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
        self.clearMoves()
        self.nn = NeuralNet([9,30,9])
        self.name2num_dict = {}
        names = "ime_012345678f"
        for i in range(len(names)):
            self.name2num_dict[names[i]] = i - 4
        self.human = 0
        
    def switch(self):
        self.human = 1 - self.human
            
    def clearMoves(self):
        self.move_list = []
        self.guess = {}
        self.visited = {}
        for i in range(self.game.width):
            for j in range(self.game.height):
                self.guess[(i,j)] = 0
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

        x, y = self.pos
        self.old_pos = self.pos

        # figure out where your are and what's around you
        area = self.getArea(x,y,3)
        area2 = self.getArea(x,y,5)
        
        input = []
        for pos in area:
            try:
                name = self.game.board[pos]
                num = self.name2num_dict[name]
                input.append(num)
            except:
                input.append(1)

        target = []
        for i in range(len(area)):
            pos = area[i]
            try:
                num = self.game.mine_array[pos]
                target.append(num)
            except: 
                target.append(.5)


        ################################################################
        # HUMAN
        ################################################################
        if self.human:

            if self.game.draw_board:
                self.pos = self.mouse2Grid(pygame.mouse.get_pos())
            x, y = self.pos
            
            # check for events
            if self.game.draw_board:
                for event in pygame.event.get() :
                    if event.type == QUIT:
                        self.game.running = False
                        pygame.quit()
                    if event.type == KEYDOWN and event.key == K_ESCAPE:
                        self.game.running = False
                    if event.type == KEYDOWN and event.key == K_r:
                        self.switch()

                    # if something is clicked
                    if event.type == MOUSEBUTTONDOWN:
                        if event.button == 1:
                            cleared = self.game.dig(self.pos)
                        if event.button == 3:
                            self.game.mark(self.pos)

        ################################################################
        # BOT
        ################################################################
        else:
            if self.game.draw_board:
                for event in pygame.event.get():
                    if event.type == QUIT:
                        self.game.running = False
                        pygame.quit()
                    if event.type == KEYDOWN and event.key == K_ESCAPE:
                        self.game.running = False
                    if event.type == KEYDOWN and event.key == K_h:
                        self.switch()

            output = self.nn.getOut(input)
            
            # update your guesses for whether or not a square has a mine
            for i in range(9):
                try:
                    self.guess[area[i]] = (self.guess[area[i]] + output[i]) / 2.0
                except:
                    pass # this just means we're looking out of bounds

            # get the guess for the space you're on
            out = self.guess[(x,y)]
            name = self.game.board[self.pos]

            thr = .3
            if (out < thr and name == "f"):
                self.game.mark((x,y))
            elif (out > thr and name != "f"):
                self.game.mark((x,y))
                self.visited[(x,y)] += 1
            elif out < thr and name != "f":
                cleared = self.game.dig((x,y)) # how many spaces we cleared
                self.visited[(x,y)] += 5

            if self.game.board[(x,y)] == "0":
                self.visited[(x,y)] += 10
            #x = random.randint(0, self.game.width - 1)
            #y = random.randint(0, self.game.height - 1)

            # find the spot you've visited least
            min = 9999999999
            s = [(x,y)]
            for pos in area:
                try:
                    v = self.visited[pos]
                    if v < min:
                        min = v
                        s = [pos]
                    elif v == min:
                        s.append(pos)                    
                except:
                    pass
            random.shuffle(s)
                    
            # and go to it
            self.pos = s[0]
            self.visited[self.pos] += 1

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
        for i in range(len(self.move_list)):
            for j in range(3):
                self.backPropogate(i, .3, .01, .4)

        
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