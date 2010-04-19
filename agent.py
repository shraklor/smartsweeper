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

# FLOATING POINT NUMBERS BETWEEN 0 and 1
VISITS = 0
TRAIN_RULES = .9
THRESH = .01
INITIAL = 1
ALPHA = .5
BETA = .1
OPEN_MIND = 1
HUG_EDGE = .9999
BRN2GRN = 0
GREED = 0
EXPLORE = 1
TO_DIG = .6 # low numbers make digging difficult
TO_FLAG = .9 # low numbers make flagging easy
TO_UNFLAG = .5 # low numbers make unflagging easy
WEIGHT = .005
ALLOW_REPEATS = 0 #percentage of repeats allowed
WHOLE_BOARD = 0 # pct of time the whole board is scanned

# FLOATS LARGER THAN 1
SPEED_AMT = 1.01 # increased threshold change
CHANGE = 1.001 # normal threshold change

# INTEGERS
NUM_POS = 1
MAX_MOVES = 42000
MOVES_LEARNED = 1000
SPEED_MOVES = 12000
INPUT_GRID = 5
OUTPUT_GRID = 3

# BOOLEAN
SHARE_MAP = True
RESET_MOVES = False # do you want your move list to empty after each game?
CHEAT = False

################################################################################
# Intelligent Agent
################################################################################

class Agent:
    def __init__(self, game):
        self.game = game
        self.human = 0
        self.clearMoves()
        self.name2num_dict = {}
        names = "012345678f_"
        self.in_size = len(names)
        for i in range(len(names)):
            nodes = [0] * 11
            nodes[i] = 1
            self.name2num_dict[names[i]] = nodes
        a = (INPUT_GRID**2)*(11)
        b = OUTPUT_GRID**2
        self.nn = NeuralNet(a,a,b)
        self.cheat = CHEAT
        self.memory = []
        self.alpha = ALPHA
        self.beta = BETA
        self.move_list = []
    def switch(self):
        self.human = 1 - self.human
            
    def clearMoves(self):
        self.num_moves = 0
        self.closed = []
        self.thresh = INITIAL# * random.random()
        if self.human and self.game.draw_board:
            x, y = pygame.mouse.get_pos()
            if self.game.torus:
                x %= self.game.width
                y %= self.game.height
            else:
                if x >= self.game.width: x = self.game.width - 1 
                elif x < 0: x = 0
                if y >= self.game.height: y = self.game.height - 1 
                elif y < 0: y = 0
            s = (x, y)
            
        else: 
            #s = (random.randint(0, self.game.width),
            #     random.randint(0, self.game.height))
            s = (0,0)
        self.old_pos = s
        self.pos = s
        self.old_action = "L"
        self.action = "L"
        if RESET_MOVES:
            self.move_list = []
        if not SHARE_MAP: self.guess = {}
        self.visited = {}
        self.certainty = {}
        for i in range(self.game.width):
            for j in range(self.game.height):
                if not SHARE_MAP: self.guess[(i,j)] = .5
                self.visited[(i,j)] = 0
                self.certainty[(i,j)] = .5

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
                if self.game.torus:
                    a %= self.game.width
                    b %= self.game.height
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
        if SHARE_MAP:
            out = self.game.guess[self.pos]
        else: out = self.guess[self.pos]
        
        
        
        name = self.game.board[self.pos]
        m = self.num_moves
        speed = 1
        if m == SPEED_MOVES:
            print "speeding up"
        if m > SPEED_MOVES:
            speed = SPEED_AMT
        if m == MAX_MOVES:
            print "giving up"
        if m < MAX_MOVES:
            if out <= self.thresh * TO_DIG and name != "f":
                #print "dig"
                self.close(self.pos)
                cleared = self.game.dig(self.pos) # how many spaces we cleared
                #self.visited[(x,y)] += 5
                #if name not in "012345678" and m > SPEED_MOVES:
                if cleared != 0:
                    self.thresh = THRESH * speed
            elif (out * TO_UNFLAG <= self.thresh and name == "f"):
                #print "unflag"
                self.open(self.pos)
                self.game.mark(self.pos)
                #self.thresh = THRESH * speed
                if random.random() < WHOLE_BOARD: self.wholeBoard()
            elif (out >= (1 - self.thresh) * TO_FLAG and name != "f"):
                #print "flag"
                self.close(self.pos)
                self.game.mark(self.pos)
                #self.visited[self.pos] += 5
                self.thresh = THRESH * speed
                if random.random() < WHOLE_BOARD: self.wholeBoard()

        # if you've gone so many moves without ending the game, do it
        elif name == "f":
            self.game.mark(self.pos)
            self.game.throwTowel()
        else:
            self.game.dig(self.pos)
            self.game.throwTowel()
        
        if name == "0":
            pass#self.visited[(x,y)] += 10

    def simMove(self):
        m = self.num_moves
        speed = 1
        if m == SPEED_MOVES:
            print "speeding up"
        if m > SPEED_MOVES:
            speed = SPEED_AMT
        self.thresh *= CHANGE * speed
        ############################################################
        # MOVEMENT
        ############################################################
        x,y = self.pos
        # if you're on green, move to brown (most of the time)
        area = self.getArea(x,y,3)
        von_neumann = [(x,y+1),(x,y-1),(x+1,y),(x-1,y)]
        possible = []
        if random.random() < HUG_EDGE:
            for pos in area:
                if self.pos == pos:
                    continue
                try:
                    a = self.game.board[self.pos]
                    grn = "_f"
                    brn = "012345678"
                    if (a in grn) and (self.game.board[pos] in brn):
                        possible.append(pos)
                    if (random.random < BRN2GRN and (a in brn) and
                        (self.game.board[pos] in grn) and
                        (pos in von_neumann)):
                        possible.append(pos)
                except: pass

        # if this isn't possible, anywhere is fine
        if len(possible) == 0 or random.random < EXPLORE:
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
        if random.random() < GREED:
            random.shuffle(self.best_guesses)
            self.pos = self.best_guesses[0]
        
        # and go to it
        else:
            self.pos = s[0]
        if random.random() < VISITS: self.visited[self.pos] += 1

    def scanMove(self):
        x, y = self.pos
        x = (x + 1) % self.game.width
        if x == 0:
            y = (y + 1) % self.game.height
            if y == 0:
                m = self.num_moves
                speed = 1
                if m == SPEED_MOVES:
                    print "speeding up"
                if m > SPEED_MOVES:
                    speed = SPEED_AMT
                self.thresh *= CHANGE * speed
        self.pos = (x, y)
        
    def wholeBoard(self):
        p = []
        for i in range(self.game.width):
            for j in range(self.game.height):
                p.append((i,j))
        random.shuffle(p)
        for s in p:
            self.getNNOutOf(s)
            
    def getNNOutOf(self, p):
        x,y = p
        
        # figure out where your are and what's around you
        self.area = self.getArea(x,y,OUTPUT_GRID)
        self.area2 = self.getArea(x,y,INPUT_GRID)

        # GET INPUT FROM AREA AROUND YOU
        input = []
        max_in = 0
        for pos in self.area2:
            try:
                name = self.game.board[pos]
                try:
                    if int(name) > max_in:
                        max_in = int(name)
                except:
                    pass
                nodes = self.name2num_dict[name]
                input += nodes
            except:
                input += [0] * len(self.name2num_dict["0"])
        self.input = input
        self.max_in = max_in
        
        # FIGURE OUT WHAT YOUR TARGET OUTPUT SHOULD BE
        # this is not used to determine where to go or what to do
        # it is only used durring the learning phase
        target = []
        mask = [] # rule based learning
        s = 0
        o = 0
        for i in range(len(self.area)):
            pos = self.area[i]
            try:
                name = self.game.board[pos]
                if name in "012345678":
                    mask.append(0)
                else: 
                    mask.append(name)
                    s += 1
                num = self.game.mine_array[pos]
                target.append(num)
            except:
                o += 1
                mask.append(0)
                target.append(.5)
        self.target = target
        
        
        center = 0
        self.tile_done = True
        try:
            center = int(self.game.board[self.area[len(self.area)/2]])
        except:
            center = -1
        if s == center and center != 0:
            self.tile_done = True
            for i in range(len(mask)):
                if str(mask[i]) in "f_":
                    mask[i] = 1
            if random.random() < TRAIN_RULES:
                self.nn.train(input, mask, self.alpha, self.beta)
        if s + o == 9:
            for i in range(len(mask)):
                if str(mask[i]) in "f_":
                    mask[i] = .5
            if random.random() < TRAIN_RULES:
                self.nn.train(input, mask, self.alpha, self.beta)
     

        ################################################################
        # get output from neural net
        ################################################################
        # uncomment this to play perfectly (cheat)
        # for learning examples quicker
        if self.cheat:
            self.nn.train(input, target, self.alpha, self.beta)
        output = self.nn.getOut(input)
        self.output = output
            
        
        num_mines = sum(output)
        if self.tile_done:
            weight = 1 - WEIGHT
        weight = WEIGHT
        
        # update your guesses for whether or not a square has a mine
        for i in range(OUTPUT_GRID**2):
            try:
                if SHARE_MAP:
                    output[i] = self.game.guess[self.area[i]] * (1-weight) + output[i] * weight
                    self.game.guess[self.area[i]] = output[i]
                else:
                    output[i] = self.guess[self.area[i]] * (1-weight) + output[i] * weight
                    self.guess[self.area[i]] = output[i]
            except:
                pass # this just means we're looking out of bounds

    def act(self):
        if not self.game.FINISHED:
            self.old_pos = self.pos
            x,y = self.pos
            self.getNNOutOf(self.pos)
            ################################################################
            # Q STUFF
            ################################################################
            '''
            output = self.output
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
            ahha = False
            for s in self.memory:
                ahha = s.isMatch(out_array)
                if ahha:
                    state = s
                    break
            if not ahha:
                state = State(out_array)
                self.memory.append(state)

            action_i = state.getActionIndex()
            action = state.actions[action_i]
            '''
            
            ################################################################
            # EVENT LOOP - if you're drawing the board, check for events
            ################################################################
            if self.human:
                
                found = False
                if self.game.draw_board:
                    for i in range(5000):
                        event = pygame.event.poll()
                        
                        if event.type == QUIT:
                            self.game.running = False
                            pygame.quit ()
                            break

                        elif event.type == KEYDOWN:
                            if event.key == K_r:
                                self.switch()
                                break
                            if event.key == K_ESCAPE:
                                self.game.running = False
                                pygame.quit ()
                                break
                            if event.key == K_c:
                                if self.cheat: print "not cheating"
                                else: print "cheating"
                                self.cheat = bool(1 - int(self.cheat))
                                break
                            if event.key == K_g:
                                self.game.goggles = (self.game.goggles + 1) % 3
                                break


                        # if something is clicked
                        elif event.type == MOUSEBUTTONDOWN:
                            if event.button == 1:
                                cleared = self.game.dig(self.pos)
                                found = True
                                '''
                                state.reward("L")
                                state.punish("R")
                                '''
                            if event.button == 3:
                                self.game.mark(self.pos)
                                found = True
                                '''
                                state.reward("R")
                                state.punish("L")
                                '''
                                
                        elif event.type == MOUSEMOTION:
                            self.old_pos = self.pos
                            self.pos = self.mouse2Grid(event.pos)
                            x, y = self.pos
                            a, b = self.old_pos
                            if self.old_pos != self.pos:
                                '''
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
                                '''
                                found = True
                        
                        else:
                            self.pos = self.mouse2Grid(pygame.mouse.get_pos())



            ################################################################
            # BOT SPECIFIC STUFF
            ################################################################
            elif not self.human:
                found = False
                if self.game.draw_board:
                    for i in range(10):
                        event = pygame.event.poll()
                        if event.type == KEYDOWN:
                            if event.key == K_h:
                                self.switch()
                            if event.key == K_c:
                                if self.cheat: print "not cheating"
                                else: print "cheating"
                                self.cheat = bool(1 - int(self.cheat))
                                break
                            if event.key == K_g:
                                self.game.goggles = (self.game.goggles + 1) % 3
                                break    
                            if event.key == K_ESCAPE:
                                self.game.running = False
                                pygame.quit ()
                                break
                                
                        if event.type == QUIT:
                            self.game.running = False
                            pygame.quit ()
                            break
                            

                        found = True
                if random.random() < WHOLE_BOARD: self.wholeBoard()
                self.threshClick()
                self.getCertainty()
                self.scanMove()
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
            if found:
                m = [self.input, self.target, self.max_in]
                if (random.random() < ALLOW_REPEATS or 
                    m not in self.move_list):
                    self.move_list.append(m)
                    #print len(self.move_list)
                if len(self.move_list) > MOVES_LEARNED:
                    r = random.randint(0, len(self.move_list))
                    self.move_list = self.move_list[:r] + self.move_list[r+1:]
                    #self.move_list = self.move_list[1:]
                self.num_moves += 1
                
            
            '''if self.num_moves == MOVES_LEARNED:
                print "truncating move list"
            if self.num_moves == MAX_MOVES / 20:
                print "5%"
            if self.num_moves == MAX_MOVES / 4:
                print "1/4"
            if self.num_moves == MAX_MOVES / 2:
                print "half way"'''
                
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
                if SHARE_MAP:
                    g = self.game.guess[(i,j)]
                else:
                    g = self.guess[(i,j)]
                err = min(g, 1-g) ** 2
                global_certainty += 1 - err
                if (i,j) in self.area:
                    local_certainty += 1 - err
                if (i,j) in self.closed and random.random() < .9:
                    continue
                if err < max(lowest_errors):
                    lowest_errors.append(err)
                    self.best_guesses.append((i,j))
                    if len(self.best_guesses) > NUM_POS:
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
        # go through each move and back propogate rewards
        index = 0
        avg_num = 0
        for index in range(len(self.move_list)):
            move = self.move_list[index]
            self.nn.train(move[0], move[1],self.alpha, self.beta)
            avg_num += move[2]
        avg_num /= float(len(self.move_list))
        self.alpha *= OPEN_MIND
        self.beta *= OPEN_MIND
        #print avg_num
        #print self.alpha, self.beta
        
    def reward(self, i, amt):
        self.state.rewards[i] += amt

    def punish(self, i, amt):
        self.reward(i, -amt)

    def setPos(self, pos):
        self.pos = pos

    def getNumMineGuess(self):
        sum = 0
        if SHARE_MAP:
            g = self.game.guess.values()
        else:
            g = self.guess.values()
        for guess in g:
            if guess > .5:
                sum += 1
        return sum
