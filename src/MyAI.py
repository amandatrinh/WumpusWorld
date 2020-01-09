# ======================================================================
# FILE:        MyAI.py
#
# AUTHOR:      Abdullah Younis
#
# DESCRIPTION: This file contains your agent class, which you will
#              implement. You are responsible for implementing the
#              'getAction' function and any helper methods you feel you
#              need.
#
# NOTES:       - If you are having trouble understanding how the shell
#                works, look at the other parts of the code, as well as
#                the documentation.
#
#              - You are only allowed to make changes to this portion of
#                the code. Any changes to other portions of the code will
#                be lost when the tournament runs your code.
# ======================================================================

from Agent import Agent

class MyAI ( Agent ):

    def __init__ ( self ):
        # ======================================================================
        # YOUR CODE BEGINS
        # ======================================================================
        self.visited = set() # set of visited/safe spots
        self.visitedCount = dict() # how many times we've entered each spot
        self.P = set()
        self.B = set()
        self.S = set()
        self.row = 1 # bottom to top indices
        self.col = 1 # left to right indices
        
        self.direction = "right" # begin facing right
        self.lastMove = False # last move taken, will be an agent action
        # can be either up, right, down, or left
        
        self.maxRow = 99999 # boundary
        self.maxCol = 99999 # boundary
        self.Wumpus = "alive"
        self.WumpusLoc = False # unknown location of Wumpus
        self.canShoot = True # haven't used arrow yet
        self.nextMove = False # nextMove unknown
        self.nextMoveList = list() # sort of be a queue or stack
        self.goHome = list() # path we've taken so far
        self.goHomeNow = False
        self.betterpath = list()
        # ======================================================================
        # YOUR CODE ENDS
        # ======================================================================

    def getAction( self, stench, breeze, glitter, bump, scream ):
        # ======================================================================
        # YOUR CODE BEGINS
        # ======================================================================
        
        if self.nextMove != False: # if nextMove known complete it first as always
            # pop first move in nextMoveList
            result = self.nextMoveList.pop(0)
            # if nextMoveList now empty, set nextMove to false
            if not self.nextMoveList:
                self.nextMove = False
            self.lastMove = result
            return result

        # First get percepts & save them
        if bump: #set max boundaries
            if self.direction == "up":
                self.row -= 1
                self.maxRow = self.row
            if self.direction == "right":
                self.col -= 1
                self.maxCol = self.col
        if scream:
            self.Wumpus = "dead"
        if stench:
            self.S.add((self.row,self.col)) # add current spot to stenches
        if breeze:
            self.B.add((self.row,self.col)) # add current spot to breezes

        # add current position to self.visited if not in it yet
        # update visitedCount to visted once so far/right now
        if (self.row,self.col) not in self.visited:
            self.visited.add((self.row,self.col)) # add current spot to safe
            self.visitedCount[(self.row,self.col)] = 1
        elif self.lastMove == Agent.Action.FORWARD and (not bump):
            self.visitedCount[(self.row,self.col)] += 1

        # update goHome backtracking list 
        if (not self.goHome) and (not self.goHomeNow): # if empty list
            self.goHome.append((self.row,self.col))
        elif not self.goHomeNow and (self.lastMove == Agent.Action.FORWARD):
            if self.goHome[-1] != (self.row,self.col):
                self.goHome.append((self.row,self.col))

        # best case scenario, pick up gold right away
        if glitter:
            self.goHomeNow = True
            self.betterpath = self.goHome.copy()
            self.__calcOptimalPath(list(),(-1,-1),self.betterpath[-1],0,len(self.betterpath))
            self.goHome = self.betterpath.copy()
            self.goHome.pop() # remove current location
            return Agent.Action.GRAB;
        if self.visitedCount[(self.row,self.col)] == 6:
            self.goHomeNow = True
            self.betterpath = self.goHome.copy()
            self.__calcOptimalPath(list(),(-1,-1),self.betterpath[-1],0,len(self.betterpath))
            self.goHome = self.betterpath.copy()
            self.goHome.pop() # remove current location
        # ELSE everything else...
        # at origin, if breeze, climb out right away
        if (self.row,self.col) == (1,1) and breeze:
            return Agent.Action.CLIMB
        if (self.row,self.col) == (1,1) and stench and self.canShoot:
            self.canShoot = False
            return Agent.Action.SHOOT
        if (self.row,self.col) == (1,1) and stench and (self.Wumpus == "alive"):
            self.B.add((self.row+1,self.col))
            stench = False
        if ((self.row,self.col) == (3,1) and stench 
            and (self.Wumpus == "alive") and self.WumpusLoc == (2,1)
            and self.canShoot == False):
            stench = False
        if ((self.row,self.col) == (2,2) and stench
            and (self.Wumpus == "alive") and self.WumpusLoc == (2,1)
            and self.canShoot == False):
            stench = False

        if self.goHomeNow: # figure out how to get home!
            # take all paths back to (1,1) and climb out
            # might have to calculate nextMove here
            if (self.row,self.col) == (1,1):
                return Agent.Action.CLIMB
            else:
                # if goHome list is now empty (we must be at (1,1)
                if not self.goHome:
                    return Agent.Action.CLIMB
                self.nextMove = self.goHome.pop() # will return a tuple
                # calculate nextMoveList
                # returns a list of moves needed to be taken
                self.nextMoveList = self.__calcNextMove(self.nextMove)

        if self.nextMove != False: # nextMove known
            # pop first move in nextMoveList
            result = self.nextMoveList.pop(0)
            self.row,self.col = self.nextMove
            # if nextMoveList now empty, set nextMove to false
            if not self.nextMoveList:
                self.nextMove = False
            self.lastMove = result
            return result


        # let's figure out the percepts in the current spot
        
        if stench and (self.Wumpus == "alive"):
            # check to see if you found the Wumpus location
            self.__locateWumpus()
            if self.WumpusLoc and self.canShoot:
                # found Wumpus, generate nextMoveList
                # will include shoot at the end
                self.nextMoveList = self.__calcShoot()
                self.nextMove = True
                self.canShoot = False # going to use up the arrow
                result = self.nextMoveList.pop(0)
                if not self.nextMoveList:
                    self.nextMove = False
                self.lastMove = result
                return result
            else:
                # no available move so back track by 1
                self.nextMove = self.goHome.pop()
                if self.nextMove == (self.row,self.col):
                    self.nextMove = self.goHome.pop()
                self.nextMoveList = self.__calcNextMove(self.nextMove)
                result = self.nextMoveList.pop(0)
                self.row,self.col = self.nextMove
                if not self.nextMoveList:
                    self.nextMove = False
                self.lastMove = result
                return result
        if breeze:
            # check for any pits that exists for sure
            # go back and explore another new path?
            self.nextMove = self.goHome.pop()
            if self.nextMove == (self.row,self.col):
                self.nextMove = self.goHome.pop()
            self.nextMoveList = self.__calcNextMove(self.nextMove)
            result = self.nextMoveList.pop(0)
            self.row,self.col = self.nextMove
            if not self.nextMoveList:
                self.nextMove = False
            self.lastMove = result
            return result
        if not (stench or breeze) or ((not breeze) and self.Wumpus == "dead"):
            # go to next available spot if possible
            # if new/unexplored spot, go to that one first
            upPos = (self.row+1,self.col)
            downPos = (self.row-1,self.col)
            leftPos = (self.row,self.col-1)
            rightPos = (self.row,self.col+1)
            temp = [upPos,downPos,leftPos,rightPos]
            if (upPos in self.B) or (upPos in self.P):
                temp.remove(upPos)
            if (downPos in self.B) or (downPos in self.P):
                temp.remove(downPos)
            if (leftPos in self.B) or (leftPos in self.P):
                temp.remove(leftPos)
            if (rightPos in self.B) or (rightPos in self.P):
                temp.remove(rightPos)
            # now remove all possible moves that are out of range
            if (upPos[0] > self.maxRow) and (upPos in temp):
                temp.remove(upPos)
            if (downPos[0] < 1) and (downPos in temp):
                temp.remove(downPos)
            if (leftPos[1] < 1) and (leftPos in temp):
                temp.remove(leftPos)
            if (rightPos[1] > self.maxCol) and (rightPos in temp):
                temp.remove(rightPos)
            # now remove all the places we've been to before
            if (upPos in self.visited) and (upPos in temp):
                temp.remove(upPos)
            if (downPos in self.visited) and (downPos in temp):
                temp.remove(downPos)
            if (leftPos in self.visited) and (leftPos in temp):
                temp.remove(leftPos)
            if (rightPos in self.visited) and (rightPos in temp):
                temp.remove(rightPos)
            # if not empty, new spots we've never been to, then take it
            if temp:
                self.nextMove = temp.pop()
                self.nextMoveList = self.__calcNextMove(self.nextMove)
                result = self.nextMoveList.pop(0)
                self.row,self.col = self.nextMove
                if not self.nextMoveList:
                    self.nextMove = False
                self.lastMove = result
                return result
            if not temp:
                # no available move so back track by 1
                if self.lastMove == Agent.Action.FORWARD:
                    self.goHome.pop()
                if not self.goHome:
                    # must be at (1,1)
                    return Agent.Action.CLIMB
                self.nextMove = self.goHome.pop()
                if self.nextMove == (self.row,self.col):
                    self.nextMove = self.goHome.pop()
                self.nextMoveList = self.__calcNextMove(self.nextMove)
                result = self.nextMoveList.pop(0)
                self.row,self.col = self.nextMove
                if not self.nextMoveList:
                    self.nextMove = False
                self.lastMove = result
                return result
        
        # CODE HERE
        return Agent.Action.CLIMB
        # YOUR CODE ENDS
        # ======================================================================
    
    # ======================================================================
    # YOUR CODE BEGINS
    # ======================================================================

    def __calcNextMove(self, nextPosTuple):
        # will return a list of Agent.Action
        # that helps us move to nextPos
        # note we append the moves
        result = []
        nextRow, nextCol = nextPosTuple
        if (self.row > nextRow) and (self.col == nextCol):
            # we have to move down
            if self.direction == "up":
                result = [Agent.Action.TURN_RIGHT,Agent.Action.TURN_RIGHT,Agent.Action.FORWARD]
            elif self.direction == "down":
                result.append(Agent.Action.FORWARD)
            elif self.direction == "left":
                result = [Agent.Action.TURN_LEFT,Agent.Action.FORWARD]
            elif self.direction == "right":
                result = [Agent.Action.TURN_RIGHT,Agent.Action.FORWARD]
            self.direction = "down"
        elif (self.row < nextRow) and (self.col == nextCol):
            # we have to move up
            if self.direction == "up":
                result.append(Agent.Action.FORWARD)
            elif self.direction == "down":
                result = [Agent.Action.TURN_RIGHT,Agent.Action.TURN_RIGHT,Agent.Action.FORWARD]
            elif self.direction == "left":
                result = [Agent.Action.TURN_RIGHT,Agent.Action.FORWARD]
            elif self.direction == "right":
                result = [Agent.Action.TURN_LEFT,Agent.Action.FORWARD]
            self.direction = "up"
        elif (self.row == nextRow) and (self.col > nextCol):
            # we have to move left
            if self.direction == "up":
                result = [Agent.Action.TURN_LEFT,Agent.Action.FORWARD]
            elif self.direction == "down":
                result = [Agent.Action.TURN_RIGHT,Agent.Action.FORWARD]
            elif self.direction == "left":
                result.append(Agent.Action.FORWARD)
            elif self.direction == "right":
                result = [Agent.Action.TURN_RIGHT,Agent.Action.TURN_RIGHT,Agent.Action.FORWARD]
            self.direction = "left"
        elif (self.row == nextRow) and (self.col < nextCol):
            # we have to move right
            if self.direction == "up":
                result = [Agent.Action.TURN_RIGHT,Agent.Action.FORWARD]
            elif self.direction == "down":
                result = [Agent.Action.TURN_LEFT,Agent.Action.FORWARD]
            elif self.direction == "left":
                result = [Agent.Action.TURN_RIGHT,Agent.Action.TURN_RIGHT,Agent.Action.FORWARD]
            elif self.direction == "right":
                result.append(Agent.Action.FORWARD)
            self.direction = "right"
        return result


    def __locateWumpus(self):
        # stench was perceived at the current location
        # check if we can find the Wumpus for sure

        # Wumpus on top
        if (((self.row + 1, self.col - 1) in self.S) and
           ((self.row + 1, self.col + 1) in self.S)):
            self.WumpusLoc = (self.row + 1, self.col)
        if (((self.row + 1, self.col - 1) in self.S) and
           ((self.row - 1, self.col - 1) not in self.S) and
           ((self.row - 1, self.col - 1) in self.visited)):
            self.WumpusLoc = (self.row + 1, self.col)
        if (((self.row + 1, self.col + 1) in self.S) and
           ((self.row - 1, self.col + 1) not in self.S) and
           ((self.row - 1, self.col + 1) in self.visited)):
            self.WumpusLoc = (self.row + 1, self.col)
        if ((self.row - 1 == 0) and (self.col - 2 == 0) and
           ((self.row + 1, self.col - 1) in self.S)):
            self.WumpusLoc = (self.row + 1, self.col)
        if ((self.row - 1 == 0) and (self.col + 1 == self.maxCol) and
           ((self.row + 1, self.col + 1) in self.S)):
            self.WumpusLoc = (self.row + 1, self.col)
        # Wumpus on bottom
        if (((self.row - 1, self.col - 1) in self.S) and
           ((self.row - 1, self.col + 1) in self.S)):
            self.WumpusLoc = (self.row - 1, self.col)
        if (((self.row - 1, self.col - 1) in self.S) and
           ((self.row + 1, self.col - 1) not in self.S) and
           ((self.row + 1, self.col - 1) in self.visited)):
            self.WumpusLoc = (self.row - 1, self.col)
        if (((self.row - 1, self.col + 1) in self.S) and
           ((self.row + 1, self.col + 1) not in self.S) and
           ((self.row + 1, self.col + 1) in self.visited)):
            self.WumpusLoc = (self.row - 1, self.col)
        if ((self.row == self.maxRow) and (self.col - 2 == 0) and
           ((self.row - 1, self.col - 1) in self.S)):
            self.WumpusLoc = (self.row - 1, self.col)
        if ((self.row == self.maxRow) and (self.col + 1 == self.maxCol) and
           ((self.row - 1, self.col + 1) in self.S)):
            self.WumpusLoc = (self.row - 1, self.col)
        # Wumpus on left
        if (((self.row + 1, self.col - 1) in self.S) and
           ((self.row - 1, self.col - 1) in self.S)):
            self.WumpusLoc = (self.row, self.col - 1)
        if (((self.row + 1, self.col - 1) in self.S) and
           ((self.row + 1, self.col + 1) not in self.S) and
           ((self.row + 1, self.col + 1) in self.visited)):
            self.WumpusLoc = (self.row, self.col - 1)
        if (((self.row - 1, self.col - 1) in self.S) and
           ((self.row - 1, self.col + 1) not in self.S) and
           ((self.row - 1, self.col + 1) in self.visited)):
            self.WumpusLoc = (self.row, self.col - 1)
        if ((self.row + 1 == self.maxRow) and (self.col == self.maxCol) and
           ((self.row + 1, self.col - 1) in self.S)):
            self.WumpusLoc = (self.row, self.col - 1)
        if ((self.row - 2 == 0) and (self.col == self.maxCol) and
           ((self.row - 1, self.col - 1) in self.S)):
            self.WumpusLoc = (self.row, self.col - 1)
        # Wumpus on right
        if (((self.row + 1, self.col + 1) in self.S) and
           ((self.row - 1, self.col + 1) in self.S)):
            self.WumpusLoc = (self.row, self.col + 1)
        if (((self.row + 1, self.col + 1) in self.S) and
           ((self.row + 1, self.col - 1) not in self.S) and
           ((self.row + 1, self.col - 1) in self.visited)):
            self.WumpusLoc = (self.row, self.col + 1)
        if (((self.row - 1, self.col + 1) in self.S) and
           ((self.row - 1, self.col - 1) not in self.S) and
           ((self.row - 1, self.col - 1) in self.visited)):
            self.WumpusLoc = (self.row, self.col + 1)
        if ((self.row - 2 == 0) and (self.col - 1 == 0) and
           ((self.row - 1, self.col + 1) in self.S)):
            self.WumpusLoc = (self.row, self.col + 1)
        if ((self.row + 1 == self.maxRow) and (self.col - 1 == 0) and
           ((self.row + 1, self.col + 1) in self.S)):
            self.WumpusLoc = (self.row, self.col + 1)
        # Does not return anything


    def __calcShoot(self):
        # returns a list of moves to shoot Wumpus
        # try to call __calcNextMove and replace walking forward w/ shoot
        result = list()
        result = self.__calcNextMove(self.WumpusLoc)
        result.pop() # remove FORWARD
        result.append(Agent.Action.SHOOT)
        return result


    def __calcOptimalPath(self, currpath, lastmove, currmove, counter, length):
        # calculates the optimal path back home if any
        # returns a list of optimal path if any
        result = currpath.copy()
        result.insert(0,currmove)
        steps = counter + 1
        if steps >= length:
            return result # too long of a path
        upPos = (self.row+1,self.col)
        downPos = (self.row-1,self.col)
        leftPos = (self.row,self.col-1)
        rightPos = (self.row,self.col+1)
        temp = [upPos,downPos,leftPos,rightPos]
        if (upPos not in self.visited) or (upPos in result):
            temp.remove(upPos)
        if (downPos not in self.visited) or (downPos in result):
            temp.remove(downPos)
        if (leftPos not in self.visited) or (leftPos in result):
            temp.remove(leftPos)
        if (rightPos not in self.visited) or (rightPos in result):
            temp.remove(rightPos)
        if lastmove in temp:
            temp.remove(lastmove)
        if len(temp) == 0:
            return result # deadend
        else:
            for nextmove in temp:
                if nextmove == (1,1):
                    result.insert(0,(1,1))
                    if len(result) < len(self.betterpath):
                        self.betterpath = result.copy()
                    return result
                else:
                    nextcurrpath = result.copy()
                    self.__calcOptimalPath(nextcurrpath,currmove,nextmove,counter+1,len(self.betterpath))
            return self.betterpath

    # ======================================================================
    # YOUR CODE ENDS
    # ======================================================================
