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

import pygame, os, pickle, random, sys
from pygame.locals import *
from game import *
from neural_network import *
from agent import *

LOAD_NN = True
SAVE_NN = True
DRAW = True
RECORD = False # this is really resource intensive
HUMAN = False
CHUNK = 1000
OUTPUT_TEXT = "win_pct,sq_err,pct_cor,cleared,cor_digs,inc_digs,cor_flags,inc_flags\n"

def main():
    w = 30
    h = 16
    m = 99

    # create your game board
    game = Game(w, h, m, draw = DRAW, tile_size = 32)
    count = 0
    frame = 0
    
    # draw if you want
    if game.draw_board:
        t = game.tile_size
        screen = pygame.display.set_mode((w * t, h * t))

    # create your players
    agent = Agent(game)
    #agent.cheat = True
    if HUMAN:
        agent.switch()

    ####################################################################
    # load your saved neural net from a file
    ####################################################################
    if LOAD_NN:
        try:
            f = open(os.path.join("data","nn.obj"), "r")
            agent.nn = pickle.load(f)
            print "Loading neural network."
            f.close()
        except:
            #print sys.exc_info()
            print "Couldn't load mind. Creating one."

    ####################################################################
    # create a log file
    ####################################################################
    csv = open(os.path.join("data", str(count) + ".csv"), "w")
    csv.write(OUTPUT_TEXT)
       
    # get things started
    game.running = True
    while game.running:

        agent.clearMoves()

        ################################################################
        # AN INDIVIDUAL GAME
        ################################################################
        while not game.done:
            agent.act()
            if game.draw_board:
                game.clock.tick()#60) #to pace the bot
                screen.blit(game.surface, (0,0))
                x, y = agent.pos
                X, Y = x * t + t/2.0, y * t + t/2.0
                pygame.draw.circle(screen, (0,0,0), (int(X),int(Y)), 5)
                if RECORD:
                    pygame.image.save(screen, os.path.join("video", str(frame) + ".png"))
                    frame += 1
                pygame.display.flip()

        ################################################################
        # compare agent's map of minefield to actual
        ################################################################
        sq_err = 0
        correct = 0
        for x in range(game.width):
            for y in range(game.height):
                err = abs(game.mine_array[(x,y)] - agent.guess[(x,y)])
                sq_err += err ** 2
                if err < .5: correct += 1
        sq_err /= float(game.width * game.height)
        correct /= float(game.width * game.height)

        ################################################################
        # print results to file
        ################################################################
        try:
            win, lose = game.wins, game.loses
            win_pct = (win*100.0)/(win+lose)
            print "W: ", win, " - L: ", lose
            print s
        except: win_pct = 0
        
        s = (str(win_pct) + "," +
             str(sq_err) + "," +
             str(correct) + "," +
             str(game.cleared) + "," +
             str(game.correct_digs) + "," +
             str(game.incorrect_digs) + "," +
             str(game.correct_flags) + "," +
             str(game.incorrect_flags) + "\n")
        csv.write(s)
        
        ################################################################
        # START NEW FILE AFTER chunk ITTERATIONS
        ################################################################
        count += 1
        if count % CHUNK == 0:
            csv.close()
            #agent = Agent(game)
            #count = 0
            csv = open(os.path.join("data", str(count) + ".csv"), "w")
            csv.write(OUTPUT_TEXT)
        elif not game.running:
            csv.close()

        ################################################################
        # LEARN!!!
        ################################################################
        agent.learn()
        agent.clearMoves()
        
        ################################################################
        # SAVE NN
        ################################################################
        if SAVE_NN:
            try:
                f = open(os.path.join("data","nn.obj"), "w")
                pickle.dump(agent.nn, f)
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
