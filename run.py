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


def main():
    w = 10#30
    h = 10#16
    m = 10#99

    # create your game board
    game = Game(w, h, m, tile_size = 32)
    game.out = open("data/test.csv", "w")

    # draw if you want
    if game.draw_board:
        t = game.tile_size
        screen = pygame.display.set_mode((w * t, h * t))

    # create your players
    agent = Agent(game)

    # load your saved neural net from a file
    try:
        f = open("data/nn.obj", "r")
        agent.nn = pickle.load(f)
        print "Loading human."
        f.close()
    except:
        print "Couldn't load human. Creating one."
        
    # get things started
    game.running = True
    #print "[H]UMAN or [R]OBOT?"
    step = 0
    while game.running:
        step += 1
        # this loop is for the game itself
        go = True
        while not go:

            # wait to see if we should change players
            event = pygame.event.wait()
            if event.type == KEYDOWN:
                if event.key == K_h:
                    #print "human"
                    player.switch()
                    go = True
                if event.key == K_r:
                    #print "robot"
                    player.switch()
                    go = True

        # check which player plays next
        
        WIN = game.wins
        s = str(step) + "," + str(game.cleared) + "," + str(game.left_click_count) + "\n"
        game.out.write(s)
        game.reset()

        try:
            f = open("data/nn.obj", "w")
            pickle.dump(human.nn, f)
            #print "Saving your human."
            f.close()
        except:pass
            #print "Couldn't save your human."

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
        try:
            win, lose = game.wins, game.loses
            win_pct = (win*100.0)/(win+lose)
            #print "W: ", win
            #print "L: ", lose
            #print "%: ", win_pct
        
        except: pass
        #print "[H]UMAN or [R]OBOT?"
    
if __name__ == '__main__':
    main()
