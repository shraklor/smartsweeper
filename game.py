#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       game.py
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

TORUS = False
OPEN_FIRST = False# false to be able to lose on first click
LOAD_NN = True
SAVE_NN = True
SAVE_CSV = False
ASCII_OUTPUT = False
LEARN = True
DRAW = True
RECORD = False # this is really resource intensive
HUMAN = False
CHUNK = 500
SAVE_CHUNK = 1
SAVE_INT = 1
OUTPUT_TEXT = "win_pct,sq_err,pct_cor,cleared,cor_digs,inc_digs,cor_flags,inc_flags\n"
DIFF = 0
DIFF_MINDS = False
AGENTS = 1

import math, os, sys, platform, pickle, random
if DRAW:
    import pygame
    from pygame.locals import *
from neural_network import *
from agent import *
try:
    from numpy import *
    import numpy.random as nrand
except:
    print "You need numpy! Ahh!"
    exit(-1)
    
    
########################################################################
# MINESWEEPER
########################################################################

class Game:
    def __init__(self, width, height, mines, draw = True, tile_size = 32, torus = False):
        self.width = width
        self.height = height
        self.mines = mines
        self.wins = 0
        self.loses = 0
        self.torus = torus
        self.guess = {}

        self.draw_board = draw
        if self.draw_board:
            pygame.init()
            self.surface = pygame.Surface((width * tile_size, height * tile_size))
            self.clock = pygame.time.Clock()
            self.tile_size = tile_size
            self.tile_dict = {}
            names = "_012345678fime"
            for name in names:
                size = (self.tile_size, self.tile_size)
                self.tile_dict[name] = pygame.transform.scale(self.loadImg(name), size)

        self.reset()

    def reset(self):
        self.goggles = 1
        self.FINISHED = False
        self.did_change = True
        self.left_clicks = 0
        self.cleared = 0
        self.correct_digs = 0
        self.incorrect_digs = 0
        self.correct_flags = 0
        self.incorrect_flags = 0
        self.towel_thrown = 0
        self.first_click = True
        self.done = False
        self.result = -1
        for i in range(self.width):
            for j in range(self.height):
                self.guess[(i,j)] = .5

        self.mine_array = {}
        for h in range(self.height):
            for w in range(self.width):
                self.mine_array[(w, h)] = 0

        self.pos_li = []
        while len(self.pos_li) != self.mines:
            rand_x = random.randint(0, self.width)
            rand_y = random.randint(0, self.height)
            pos = (rand_x, rand_y)

            if pos not in self.pos_li:
                self.pos_li.append(pos)

        for pos in self.pos_li:
            self.mine_array[pos] = 1

        self.board = {}
        for h in range(self.height):
            for w in range(self.width):
                self.upTile((w, h), "_")

    def throwTowel(self):
        self.towel_thrown = 1

    def loadImg(self, name):
        return pygame.image.load(os.path.join("images", name + ".png"))

    def upTile(self, pos, symbol):
        self.did_change = True
        self.board[pos] = symbol

        #draw stuff if drawing turned on
        if self.draw_board:
            x, y = pos
            p = (x * self.tile_size, y * self.tile_size)
            self.surface.blit(self.tile_dict[symbol], p)

    def resize(self, w, h, m):
        self.width = w
        self.height = h
        self.mines = m

    def printBoard(self):
        s = ""
        for h in range(self.height):
            for w in range(self.width):
                try:
                    s += self.board[(w, h)]
                except:
                    s += "X"
            s += "\n"
        print s

    def mark(self, pos):
        # place a flag down or pull one up
        if self.board[pos] == "_":
            self.upTile(pos, "f")
            return True

        elif self.board[pos] == "f":
            self.upTile(pos, "_")
            return False

    def dig(self, pos):
        cleared = 0
        if not self.done and self.board[pos] != "f":
            self.left_clicks += 1
            "surely dig and clear can be merged"
            "things get funky with recursion"
            # clear a space and see if you win
            cleared = self.clear(pos)
            if self.isWon():
                self.wins += 1
                self.result = 1
                self.done = True
            if cleared > 0:
                self.correct_digs += 1
            elif cleared == 0:
                self.incorrect_digs += 1
            return cleared

    def clear(self, pos, auto = False):
        cleared = 0
        x = pos[0]
        y = pos[1]

        # if the space has a mine and it's not your first move
        if (self.mine_array[pos] == 1 and
            (not self.first_click or not OPEN_FIRST)):

            # go through every space on the board
            for h in range(self.height):
                for w in range(self.width):

                    # if the space is empty and flagged
                    if (self.mine_array[(w, h)] == 0 and
                        self.board[(w, h)] == "f"):

                        # mark it as incorrectly flagged
                        self.upTile((w, h), "i")
                        self.incorrect_flags += 1

                    # if the space has a mine and is flagged
                    elif (self.mine_array[(w, h)] == 1 and
                          self.board[(w, h)] == "f"):

                        # mark it as incorrectly flagged
                        self.correct_flags += 1

                    # if the space has a mine and is not flagged
                    elif (self.mine_array[(w, h)] == 1 and
                          self.board[(w, h)] == "_"):

                        # mark it as having a mine
                        self.upTile((w, h), "m")

            # mark your position as exploded
            self.upTile(pos, "e") #

            # end the game
            self.loses += 1
            self.done = True

        # if it's your first click
        if self.first_click and OPEN_FIRST:
            self.first_click = False
            if self.torus:
                w = self.width
                h = self.height
                area = [((x-1)%w, (y-1)%h), (x, (y-1)%h), ((x+1)%w, (y-1)%h),
                        ((x-1)%w, y)      , (x, y)      , ((x+1)%w, y)      ,
                        ((x-1)%w, (y+1)%h), (x, (y+1)%h), ((x+1)%w, (y+1)%h)]
            else:
                area = [(x-1, y-1), (x, y-1), (x+1, y-1),
                        (x-1, y),   (x, y),   (x+1, y),
                        (x-1, y+1), (x, y+1), (x+1, y+1)]
            count = 0
            for s in area:
                try:
                    count += self.mine_array[s]
                    self.mine_array[s] = 0
                except:
                    pass

            rh = random.randint(0, self.height - 1)
            rw = random.randint(0, self.width - 1)
            for h in range(self.height):
                for w in range(self.width):
                    p = ((w + rw) % self.width, (h + rh) % self.height)
                    if self.mine_array[p] == 0 and p not in area:
                        if count > 0:
                            self.mine_array[p] = 1
                            count -= 1
                        else:
                            break


        # if the space is empty
        if self.mine_array[pos] == 0:

            # get your neighbors
            if self.torus:
                w = self.width
                h = self.height
                area = [((x-1)%w, (y-1)%h), (x, (y-1)%h), ((x+1)%w, (y-1)%h),
                        ((x-1)%w, y)      , (x, y)      , ((x+1)%w, y)      ,
                        ((x-1)%w, (y+1)%h), (x, (y+1)%h), ((x+1)%w, (y+1)%h)]
            else:
                area = [(x-1, y-1), (x, y-1), (x+1, y-1),
                        (x-1, y),   (x, y),   (x+1, y),
                        (x-1, y+1), (x, y+1), (x+1, y+1)]
                        
            # if the space is unknown
            if self.board[pos] == "_":
                cleared += 1

                # check all neighbors for mines
                mines = 0
                for s in area:
                    try:
                        mines += self.mine_array[s]
                    except:
                        pass # invalid position


                # set your image to the number of adj. mines
                self.upTile(pos, str(mines))

            # if the space is numbered
            if self.board[pos] in "012345678":

                # check all neighbors for flags
                flags = 0
                for s in area:
                    try:
                        if self.board[s] == "f":
                            flags += 1
                    except:
                        pass # invalid position

                # if the number of flags is your number
                if ((flags == int(self.board[pos]) and not auto) or
                    int(self.board[pos]) == 0):

                    # clear all of the unknown spaces around you
                    for s in area:
                        try:
                            if self.board[s] == "_":
                                cleared += self.clear(s, True)
                        except:
                            pass # invalid position


        return cleared

    def isWon(self):
        cleared = 0
        covered = 0
        for w in range(self.width):
            for h in range(self.height):
                if (self.board[(w,h)] != "_" and
                    self.board[(w,h)] != "f" and
                    self.mine_array[(w,h)] == 0):
                        cleared += 1
                if (self.board[(w,h)] == "_" or
                    self.board[(w,h)] == "f" and
                    self.mine_array[(w,h)] == 1):
                        covered += 1
        self.cleared = cleared
        if (cleared == ((self.width * self.height) - self.mines) and
            covered == self.mines):
            self.FINISHED = True
            return True
        self.FINISHED = False
        return False

    def getErrors(self):
        sq_err = 0
        correct = 0
        for x in range(self.width):
            for y in range(self.height):
                err = abs(self.mine_array[(x,y)] - self.guess[(x,y)])
                sq_err += err ** 2
                if err < .5: correct += 1
        sq_err /= float(self.width * self.height)
        correct /= float(self.width * self.height)
        return sq_err, correct


################################################################################
# example
################################################################################

def randomGame():
    game = Game(4,4,3)
    while 1:
        game.reset()
        while not game.done:
            c = random.randint(0,1)
            x = random.randint(0, game.width - 1)
            y = random.randint(0, game.height - 1)
            if c == 0:
                game.dig((x,y))
            elif c == 1:
                game.mark((x,y))
        w, l = game.wins, game.loses
        print w,"w",l,"l",(w*100.0)/(w+l),"%"
        try: input()
        except: pass

def main():
    if DIFF == 0:
        #print "SMALL - 8x8 w/ 10 mines"
        w = 8
        h = 8
        m = 10
        t = 32
    if DIFF == 1:
        #print "MEDIUM - 16x16 w/ 40 mines"
        w = 16
        h = 16
        m = 40
        t = 32
    if DIFF == 2:
        #print "LARGE - 32x16 w/ 99 mines"
        w = 32
        h = 16
        m = 99
        t = 26
    if DIFF == 3:
        w = 8
        h = 8
        m = 15
        t = 32
    s = ""

    # create your game board
    if DRAW: os.environ['SDL_VIDEO_CENTERED'] = '1'
    game = Game(w, h, m, draw = DRAW, tile_size = t, torus = TORUS)
    count = 0
    frame = 0
    banner = "W:0 - L:0"
    if DRAW:
        pygame.display.set_caption(banner)
        screen = pygame.display.set_mode((w * t, h * t))

    # create your players
    alist = []
    for i in range(AGENTS):
        alist.append(Agent(game))
    #agent.cheat = True
    if HUMAN:
        alist[0].switch()

    ####################################################################
    # load your saved neural net from a file
    ####################################################################
    if LOAD_NN:
        if DIFF_MINDS:
            for i in range(len(alist)):
                try:
                    f = open(os.path.join("data","nn" + str(i) + ".obj"), "r")
                    alist[i].nn = pickle.load(f)
                    print "Loading Agent " + str(i) + "'s neural network."
                    f.close()
                except:
                    try:
                        f = open(os.path.join("data","nn.obj"), "r")
                        alist[i].nn = pickle.load(f)
                        for agent in alist:
                            agent.nn = alist[i].nn
                        print "Loading stock neural network."
                        f.close()
                    except:
                        #print sys.exc_info()
                        print "Couldn't load mind. Creating one."
        else:
            try:
                f = open(os.path.join("data","nn.obj"), "r")
                alist[0].nn = pickle.load(f)
                for agent in alist:
                    agent.nn = alist[0].nn
                print "Loading neural network."
                f.close()
            except:
                #print sys.exc_info()
                print "Couldn't load mind. Creating one."

    ####################################################################
    # create a log file
    ####################################################################
    if SAVE_CSV:
        csv = open(os.path.join("data", str(count) + ".csv"), "w")
        csv.write(OUTPUT_TEXT)

    # get things started
    game.running = True
    while game.running:
        for agent in alist:
            agent.clearMoves()

        ################################################################
        # AN INDIVIDUAL GAME
        ################################################################
        while not game.done:
            for agent in alist:
                agent.act()
            if ASCII_OUTPUT:
                sq_err, correct = game.getErrors()
                clear = "clear"
                if platform.system() == "Windows":
                    clear = "cls"
                os.system(clear)
                print(banner)
                print("Squared Error", sq_err)
                print("Percent Correct", correct)
                game.printBoard()
            
            if game.draw_board:
                game.clock.tick()#60) #to pace the bot
                for event in pygame.event.get() :
                    if event.type == QUIT:
                        game.running = False
                        pygame.quit ()

                    # if the keyboard is used
                    elif event.type == KEYDOWN:
                        if event.key == K_ESCAPE:
                            game.running = False
                            pygame.quit ()
                        if ((event.key == K_r and alist[0].human) or
                            (event.key == K_h and not alist[0].human)):
                            alist[0].switch()
                        if event.key == K_c:
                            alist[0].cheat = bool(1 - int(alist[0].cheat))
                        if event.key == K_g:
                            game.goggles = (game.goggles + 1) % 3


                if game.goggles == 0 or game.goggles == 1:
                    screen.blit(game.surface, (0,0))

                # DRAW AGENT'S GUESS
                # purple = mine, yellow = not mine
                # transparent = certain, opaque = not sure
                if game.goggles == 1 or game.goggles == 2:
                    temp = pygame.Surface((w,h))
                    tran = pygame.Surface((t-1, t-1))
                    for i in range(w):
                        for j in range(h):
                            g = 1 - game.guess[(i,j)]
                            g *= 255
                            tran.fill((160,g,255-g))
                            g = int(min(g, 255-g) * 2)
                            tran.set_alpha(int(g / 1.4))
                            screen.blit(tran, (i * t + 1, j * t + 1))

                ########################################################
                # DRAW EACH AGENT
                ########################################################
                for agent in alist:
                    x, y = agent.pos
                    rx, ry = random.randint(-t/3,t/3), random.randint(-t/3,t/3)
                    X, Y = x * t + t/2.0 + rx, y * t + t/2.0 + ry
                    pygame.draw.circle(screen, (0,0,0), (int(X),int(Y)), 3)

                ########################################################
                # MAKE A MOVIE
                ########################################################
                if RECORD and game.did_change:
                    print "recording"
                    old_board = copy(game.board)
                    pygame.image.save(screen, os.path.join("video", str(frame) + ".png"))
                    frame += 1
                pygame.display.flip()
                game.did_change = False

        ################################################################
        # compare agent's map of minefield to actual
        ################################################################
        sq_err, correct = game.getErrors()

        ################################################################
        # print results to file
        ################################################################
        win, lose = game.wins, game.loses
        try:
            win_pct = (win*100.0)/(win+lose)
        except: win_pct = 0

        s = (str(win_pct) + "," +
             str(sq_err) + "," +
             str(correct) + "," +
             str(game.cleared) + "," +
             str(game.correct_digs) + "," +
             str(game.incorrect_digs) + "," +
             str(game.correct_flags) + "," +
             str(game.incorrect_flags) + "\n")
        if SAVE_CSV: csv.write(s)

        banner = "W: " + str(win) + " - L: " + str(lose)
        if DRAW: pygame.display.set_caption(banner)
        #print "W: ", win, " - L: ", lose
        print s

        ################################################################
        # START NEW FILE AFTER chunk ITTERATIONS
        ################################################################
        count += 1
        if SAVE_CSV and count % CHUNK == 0:
            csv.close()
            csv = open(os.path.join("data", str(count) + ".csv"), "w")
            csv.write(OUTPUT_TEXT)
        elif SAVE_CSV and not game.running:
            csv.close()

        ################################################################
        # LEARN!!!
        ################################################################
        if LEARN:
            if DIFF_MINDS:
                for agent in alist:
                    agent.learn()
            else:
                nn = alist[0].nn
                for agent in alist:
                    agent.nn = nn
                    agent.learn()
                    nn = agent.nn
                for agent in alist:
                    agent.nn = nn
                    agent.memory = alist[0].memory

        ################################################################
        # SAVE NN
        ################################################################
        if SAVE_NN and count % SAVE_INT == 0:
            if DIFF_MINDS:
                for i in range(len(alist)):
                    if i % SAVE_CHUNK == count % SAVE_CHUNK:
                        try:
                            f = open(os.path.join("data","nn" + str(i) + ".obj"), "w")
                            pickle.dump(alist[i].nn, f)
                            print "Saving neural network number " + str(i) + "."
                            f.close()
                        except:
                            #pass
                            print "Couldn't save your neural network."
            else:
                try:
                    f = open(os.path.join("data","nn.obj"), "w")
                    pickle.dump(alist[0].nn, f)
                    print "Saving your neural network."
                    f.close()
                except:
                    #pass
                    print "Couldn't save your neural network."

        ################################################################
        # RESET BOARD
        ################################################################
        game.reset()

if __name__ == '__main__':
    main()
