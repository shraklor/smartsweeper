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
    w = 30
    h = 16
    m = 99

    # create your game board
    game = Game(w, h, m, tile_size = 32)

    # draw if you want
    if game.draw_board:
        t = game.tile_size
        screen = pygame.display.set_mode((w * t, h * t))

    # create your players
    human = Human(game)

    # load your saved neural net from a file
    try:
        f = open("human.obj", "r")
        human.nn = pickle.load(f)
        print "Loading human."
        f.close()
    except:
        print "Couldn't load human. Creating one."
        human = Human(game)

    bot = Agent(game, human.nn)

    agents = [human, bot]
    game.agent_index = 0

    # get things started
    game.running = True
    print "[H]UMAN or [R]OBOT?"
    while game.running:

        # this loop is for the game itself
        go = True
        while not go:

            # wait to see if we should change players
            event = pygame.event.wait()
            if event.type == KEYDOWN:
                if event.key == K_h:
                    print "human"
                    game.agent_index = 0
                    go = True
                if event.key == K_r:
                    print "robot"
                    game.agent_index = 1
                    go = True

        # check which player plays next
        agent = agents[game.agent_index]

        WIN = game.wins
        game.reset()

        try:
            f = open("human.obj", "w")
            pickle.dump(human.nn, f)
            print "Saving your human."
            f.close()
        except:
            print "Couldn't save your human."

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

        try:
            win, lose = game.wins, game.loses
            win_pct = (win*100.0)/(win+lose)
            print "W: ", win
            print "L: ", lose
            print "%: ", win_pct
            print
            print "[H]UMAN or [R]OBOT?"
        except: pass





if __name__ == '__main__':
    main()
