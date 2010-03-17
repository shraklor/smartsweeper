#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       run.py
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

import pygame, os, pickle, random
from pygame.locals import *
from game import *
from neural_network import *
from agent import *

LOAD_PREV = True
DRAW = False
HUMAN = False
CHUNK = 500

def main():
    w = 30
    h = 16
    m = 99

    # create your game board
    game = Game(w, h, m, draw = DRAW, tile_size = 32)
    count = 0
        
    # draw if you want
    if game.draw_board:
        t = game.tile_size
        screen = pygame.display.set_mode((w * t, h * t))

    # create your players
    agent = Agent(game)
    if HUMAN:
        agent.switch()

    # load your saved neural net from a file
    if LOAD_PREV:
        try:
            f = open("data/saved_state.obj", "r")
            agent.nn, count = pickle.load(f)
            print "Loading neural network."
            f.close()
        except:
            print "Couldn't load mind. Creating one."

    csv = open("data/" + str(count) + ".csv", "w")
    csv.write("count,cleared,cor_digs,inc_digs,cor_flags,inc_flags\n")
       
    # get things started
    game.running = True
    while game.running:
        if LOAD_PREV and count % CHUNK == 0:
            try:
                f = open("data/nn.obj", "w")
                pickle.dump((agent.nn, count), f)
                print "Saving your human."
                f.close()
            except:
                #pass
                print "Couldn't save your brain."

        agent.clearMoves()
        while not game.done:
            agent.act()
            if game.draw_board:
                game.clock.tick(30)
                screen.blit(game.surface, (0,0))
                x, y = agent.pos
                X, Y = x * t + t/2.0, y * t + t/2.0
                pygame.draw.circle(screen, (0,0,0), (int(X),int(Y)), 5)
                pygame.display.flip()

        agent.learn()
        s = (str(count) + "," +
             str(game.cleared) + "," +
             str(game.correct_digs) + "," +
             str(game.incorrect_digs) + "," +
             str(game.correct_flags) + "," +
             str(game.incorrect_flags) + "\n")
        csv.write(s)
        count += 1
        if count % CHUNK == 0:
            csv.close()
            csv = open("data/" + str(count) + ".csv", "w")
            csv.write("count,cleared,cor_digs,inc_digs,cor_flags,inc_flags\n")
        
        try:
            win, lose = game.wins, game.loses
            win_pct = (win*100.0)/(win+lose)
            #print "W: ", win, " - L: ", lose
            
        except: pass
        
        if game.correct_flags + game.incorrect_flags > 0:
            print(s + " @" + str(count))

        game.reset()
    
if __name__ == '__main__':
    main()
