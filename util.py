#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       util.py
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

import math,random,numpy

########################################################################
# Important Functions
########################################################################
def sigmoid(x):
    return math.tanh(x)
    #return 1.0 / (1 + math.exp(-x))

def sigPrime(x):
    # in terms of the output of the sigmoid function
    # otherwise would be sig(x) - sig^2(x)
    return 1 - x ** 2
    #return x - x ** 2

########################################################################
# Matrices
########################################################################

def fillMat(rows, cols, fill):
    M = []
    for i in range(rows):
        M.append([fill]*cols)
    return M

def zeroMat(rows, cols):
    return fillMat(rows, cols, 0)

def oneMat(rows, cols):
    return fillMat(rows, cols, 1)

def randMat(rows, cols):
    M = []
    for i in range(rows):
        row = []
        for j in range(cols):
            row.append(random.random())
        M.append(row)
    return M

def transMat(A):
    M = []
    rows = len(A)
    cols = len(A[0])
    for j in range(cols):
        row = []
        for i in range(rows):
            row.append(A[i][j])
        M.append(row)
    return M

def scaleMat(n, A):
    M = []
    for i in range(len(A)):
        row = []
        for j in range(len(A[0])):
            row.append(n * A[i][j])
        M.append(row)
    return M

def dotMats(A, B):
    M = []
    rows_A = len(A)
    cols_A = len(A[0])
    cols_B = len(B[0])
    for row in range(rows_A):
        M.append([])
        for col in range(cols_B):
            sum = 0
            for i in range(cols_A):
                sum += A[row][i] * B[i][col]
            M[row].append(sum)
    return M

def mulMats(A, B):
    M = []
    for i in range(len(A)):
        M.append([])
        for j in range(len(A[0])):
            value = A[i][j] * B[i][j]
            M[i].append(value)
    return M

def divfMats(A, B):
    # float division
    M = []
    for i in range(len(A)):
        M.append([])
        for j in range(len(A[0])):
            value = A[i][j] / float(B[i][j])
            M[i].append(value)
    return M

def diviMats(A, B):
    # int division
    M = []
    for i in range(len(A)):
        M.append([])
        for j in range(len(A[0])):
            value = int(A[i][j] / float(B[i][j]))
            M[i].append(value)
    return M

def addMats(A, B):
    M = []
    for i in range(len(A)):
        M.append([])
        for j in range(len(A[0])):
            value = A[i][j] + B[i][j]
            M[i].append(value)
    return M

def subMats(A, B):
    M = []
    for i in range(len(A)):
        M.append([])
        for j in range(len(A[0])):
            value = A[i][j] - B[i][j]
            M[i].append(value)
    return M

def funcMat(A, func):
    M = []
    for i in range(len(A)):
        M.append([])
        for j in range(len(A[0])):
            value = func(A[i][j])
            M[i].append(value)
    return M

def sigMat(A): return funcMat(A, sigmoid)
def sigPrimeMat(A): return funcMat(A, sigPrime)

########################################################################
# Vectors
########################################################################

def addVectors(u, v):
    new_vector = []
    for i in range(len(u)):
        new_vector.append(u[i] + v[i])
    return new_vector

def subVectors(u, v):
    new_vector = []
    for i in range(len(u)):
        new_vector.append(u[i] - v[i])
    return new_vector

def scalarMultiply(vector, scalar):
    new_vector = []
    for i in vector:
        new_vector.append(i * scalar)
    return new_vector

def normalize(vector):
    d = 0
    for i in vector:
        d += i ** 2
    d = math.sqrt(d)
    if d != 0:
        return scalarMultiply(vector, 1.0 / d)
    else: return vector

def vectInt(vector):
    for i in vector:
        i = int(i)

def vectAbs(vector):
    """the absolute value vector"""
    new_vector = []
    for i in vector:
        new_vector.append(abs(i))
    return new_vector

def vectSign(vector):
    """returns a vector of 1s, -1s, and 0s"""
    new_vector = []
    for i in vector:
        new_vector.append(cmp(i, 0))
    return new_vector

def avgVectors(vector_list):
    new_vector = [0] * len(vector_list)
    total = 0
    for vector in vector_list:
        new_vector = addVectors(new_vector, vector)
        total += 1
    if total == 0:
        return new_vector
    new_vector = scalarMultiply(new_vector, 1.0 / total)
    return new_vector