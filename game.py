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

OPEN_FIRST = False # can you lose on first click?

import random, pygame, os, math
from numpy import *
import numpy.random as nrand
class Game:
    def __init__(self, width, height, mines, draw = True, tile_size = 32):
        self.width = width
        self.height = height
        self.mines = mines
        self.wins = 0
        self.loses = 0
        
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

        self.mine_array = {}
        for h in range(self.height):
            for w in range(self.width):
                self.mine_array[(w, h)] = 0

        self.pos_li = []
        while len(self.pos_li) != self.mines:
            rand_x = random.randint(0, self.width - 1)
            rand_y = random.randint(0, self.height - 1)
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
            area = [(x-1, y-1), (x, y-1), (x+1, y-1),
                    (x-1, y),             (x+1, y),
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
            return True
        return False


################################################################################
# example
################################################################################

def main():
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

if __name__ == '__main__':
    main()