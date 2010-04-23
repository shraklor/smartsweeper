# FLOATING POINT NUMBERS BETWEEN 0 and 1
VISITS = 0
TRAIN_RULES = 0
THRESH = .2
INITIAL = 1
ALPHA = .5
BETA = .1
OPEN_MIND = 1
HUG_EDGE = .9
BRN2GRN = 0
GREED = 0
EXPLORE = 1
TO_DIG = 1 # low numbers make digging difficult
TO_FLAG = 1 # low numbers make flagging easy
TO_UNFLAG = 1 # low numbers make unflagging easy
WEIGHT = .009
ALLOW_REPEATS = 0 #percentage of repeats allowed
WHOLE_BOARD = 0 # pct of time the whole board is scanned

# FLOATS LARGER THAN 1
SPEED_AMT = 1.02 # increased threshold change
CHANGE = 1.006 # normal threshold change

# INTEGERS
NUM_POS = 1
MAX_MOVES = 42000
MOVES_LEARNED = 2000
MOVES_REMEMBERED = 10000
SPEED_MOVES = 10000
INPUT_GRID = 5
OUTPUT_GRID = 3

# BOOLEAN
SHARE_MAP = True
RESET_MOVES = False # do you want your move list to empty after each game?
CHEAT = False

# GAME CONSTANTS
NUM_GAMES = 10000
TORUS = False
OPEN_FIRST = True# false to be able to lose on first click
LOAD_NN = False
LOAD_ML = False
SAVE_NN = False
SAVE_ML = False
SAVE_CSV = True
ASCII_OUTPUT = False
LEARN = False
DRAW = False
RECORD = False # this is really resource intensive
HUMAN = False
CHUNK = 10000
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
try:
    from numpy import *
    import numpy.random as nrand
except:
    print "You need numpy! Ahh!"
    exit(-1)

################################################################################
# Useful Vector Functions
################################################################################
def sigmoid(x):
    return 1.0 / (1 + math.exp(-x))
sigmoid = vectorize(sigmoid, otypes=[float])

def sigPrime(x):
    # in terms of the output of the sigmoid function
    # otherwise would be sig(x) - sig^2(x)
    return x - x ** 2
sigPrime = vectorize(sigPrime, otypes=[float])

def oneMinus(x):
    return 1 - x
oneMinus = vectorize(oneMinus, otypes=[float])

def sub(x,y):
    return x - y
sub = vectorize(sub, otypes=[float])

################################################################################
# Neural Network
################################################################################
class NeuralNet:
    def __init__(self, i, h, o):
        self.w_ih = mat(nrand.uniform(-.05, .05,(i,h)))
        self.w_ho = mat(nrand.uniform(-.05, .05,(h,o)))
        self.m_ih = mat(zeros((i,h)))
        self.m_ho = mat(zeros((h,o)))

    def getOut(self, i):
        self.h = sigmoid(mat(i) * self.w_ih)
        return sigmoid(self.h * self.w_ho).tolist()[0]

    def train(self, i, t, a = .1, b = .01):

        # get output of our neural network
        out = mat(self.getOut(i))

        # calc deltas
        d_o = mat(asarray(out) * asarray(oneMinus(out)) *
                  asarray(sub(mat(t), out)))
        d_h = mat(asarray(self.h) * asarray(oneMinus(self.h)) *
                  asarray(d_o * self.w_ho.T))

        # update weights
        c_ih = mat(i).T * d_h
        self.w_ih = add(add(self.w_ih, a * c_ih), b * self.m_ih)
        self.m_ih = c_ih
        c_ho = self.h.T * d_o
        self.w_ho = add(add(self.w_ho, a * c_ho), b * self.m_ho)
        self.m_ho = c_ho

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
# Intelligent Agent
################################################################################

class Agent:
    def __init__(self, game):
        self.game = game
        self.human = 0
        self.clearMoves()
        self.name2num_dict = {}
        names = "_012345678f"
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
        self.rand_moves = []
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
        #if m == SPEED_MOVES:
        #     "speeding up"
        if m > SPEED_MOVES:
            speed = SPEED_AMT
        #if m == MAX_MOVES:
        #    print "giving up"
        if m < MAX_MOVES:
            if out <= self.thresh * TO_DIG and name != "f":
                #print "dig"
                self.close(self.pos)
                cleared = self.game.dig(self.pos) # how many spaces we cleared
                #self.visited[(x,y)] += 5
                #if name not in "012345678" and m > SPEED_MOVES:
                if cleared > 0:
                    #print "cleared", cleared
                    self.resetThresh(speed)
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
                self.resetThresh(speed)
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

    def resetThresh(self, speed):
        self.thresh = THRESH * speed

    def simMove(self):
        m = self.num_moves
        speed = 1
        if m > SPEED_MOVES:
            speed = SPEED_AMT
        if m % 50 == 0: self.thresh *= CHANGE * speed
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

    def randMove(self):
        if len(self.rand_moves) != 0:
            self.pos = self.rand_moves.pop()
        else:
            for i in range(self.game.width):
                for j in range(self.game.height):
                    self.rand_moves.append((i,j))
            random.shuffle(self.rand_moves)
            m = self.num_moves
            speed = 1
            if m > SPEED_MOVES:
                speed = SPEED_AMT
            self.thresh *= CHANGE * speed


    def scanMove(self):
        x, y = self.pos
        x = (x + 1) % self.game.width
        if x == 0:
            y = (y + 1) % self.game.height
            if y == 0:
                m = self.num_moves
                speed = 1
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
                self.nn.train(input, mask, self.alpha * .5, self.beta * .5)


        ################################################################
        # get output from neural net
        ################################################################

        if self.cheat:
            self.nn.train(input, target, self.alpha, self.beta)
        output = self.nn.getOut(input)
        self.output = output


        '''num_mines = sum(output)
        if self.tile_done:
            weight = WEIGHT + .4
        elif num_mines - .5 > center:
            weight = WEIGHT * .5
        else:'''
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
        #print len(self.move_list)
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
                if len(self.move_list) > MOVES_REMEMBERED:
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
        for index in range(min(len(self.move_list),MOVES_LEARNED)):
            move = self.move_list[index]
            self.nn.train(move[0], move[1],self.alpha, self.beta)
        random.shuffle(self.move_list)
        self.alpha *= OPEN_MIND
        self.beta *= OPEN_MIND

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

def main():
    if DIFF == 0:
        #print "SMALL - 8x8 w/ 10 mines"
        w = 8
        h = 8
        m = 10
        t = 64
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
    # load your move list
    ####################################################################
    if LOAD_ML:
        for agent in alist:
            try:
                f = open(os.path.join("data","ml.obj"), "r")
                agent.move_list = pickle.load(f)
                print str(len(agent.move_list)) + " moves loaded."
                f.close()
            except:
                #print sys.exc_info()
                print "Couldn't load moves."

    ####################################################################
    # create a log file
    ####################################################################
    if SAVE_CSV:
        csv = open(os.path.join("data", str(count) + ".csv"), "w")
        csv.write(OUTPUT_TEXT)

    # get things started
    game.running = True
    num_games = 0
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

        s = (str(win) + "," +
             str(lose) + "," +
             str(win_pct) + "," +
             str(sq_err) + "," +
             str(correct) + "," +
             str(game.cleared) + "," +
             str(game.correct_digs) + "," +
             str(game.incorrect_digs) + "," +
             str(game.correct_flags) + "," +
             str(game.incorrect_flags))
        if SAVE_CSV: csv.write(s + "\n")

        banner = "W: " + str(win) + " - L: " + str(lose)
        if DRAW: pygame.display.set_caption(banner)
        #print "W: ", win, " - L: ", lose
        ################################################################
        # CONDOR PRINT OUT
        ################################################################
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
            elif AGENTS != 1:
                nn = alist[0].nn
                for agent in alist:
                    agent.nn = nn
                    agent.learn()
                    nn = agent.nn
                for agent in alist:
                    agent.nn = nn
                    agent.memory = alist[0].memory
            else:
                alist[0].learn()

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
        # SAVE MOVE LIST
        ################################################################
        if SAVE_ML and count % SAVE_INT == 0:
            try:
                f = open(os.path.join("data","ml.obj"), "w")
                pickle.dump(alist[0].move_list, f)
                print "Saved " + str(len(alist[0].move_list)) + " moves."
                f.close()
            except:
                #pass
                print "Couldn't save your moves."

        ################################################################
        # RESET BOARD
        ################################################################
        game.reset()
        num_games += 1
        if num_games == NUM_GAMES:
            game.running = False

if __name__ == '__main__':
    main()
