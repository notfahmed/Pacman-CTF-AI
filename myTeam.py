from captureAgents import CaptureAgent
import random
import time
import util
from game import Directions, Actions
import game
from util import nearestPoint
import numpy as np

#################
# Team creation #
#################
isRed = True


def createTeam(firstIndex, secondIndex, isRed_,
               first='OffensiveReflexAgent', second='DefensiveReflexAgent'):
    """
    This function should return a list of two agents that will form the
    team, initialized using firstIndex and secondIndex as their agent
    index numbers.
    """
    global isRed
    isRed = isRed_

    return [eval(first)(firstIndex), eval(second)(secondIndex)]


##########
# Agents #
##########

class DefensiveReflexAgent(CaptureAgent):
    """
    A reflex agent that keeps its side Pacman-free. Again,
    this is to give you an idea of what a defensive agent
    could be like.  It is not the best or only way to make
    such an agent.
    """

    def registerInitialState(self, gameState):
        CaptureAgent.registerInitialState(self, gameState)
        self.start = gameState.getAgentPosition(self.index)

    def evaluate(self, gameState, action):
        """
        Computes a linear combination of features and feature weights
        """
        weights = self.getWeights()
        features = self.getFeatures(gameState, action)

        evaluation = 0
        for k in weights.keys():
            evaluation += weights[k] * features[k]

        return evaluation

    def getFeatures(self, gameState, action):
        """
        Returns a counter of features for the state
        """
        features = util.Counter()
        successor = gameState.generateSuccessor(self.index, action)
        enemies = self.getOpponents(successor)

        enemyPosition = []
        for i in enemies:
            enemyPosition.append(successor.getAgentPosition(i))

        invaders = 0
        if not isRed:
            for i in enemyPosition:
                if not successor.isRed(i):
                    invaders += 1
        else:
            for i in enemyPosition:
                if successor.isRed(i):
                    invaders += 1
        features['invaders'] = invaders

        currentPosition = successor.getAgentPosition(self.index)
        if isRed:
            if not gameState.isRed(currentPosition):
                myPacman = 1
            else:
                myPacman = 0
        elif gameState.isRed(currentPosition):
            myPacman = 1
        else:
            myPacman = 0
        features['myPacman'] = myPacman

        myFoodCount = 0
        for i in self.getFood(successor):
            myFoodCount += sum(i)
        features['myFoodCount'] = myFoodCount

        minDistanceFromEnemy = float('inf')
        for k in enemies:
            currentDistance = self.distancer.getDistance(successor.getAgentPosition(k), currentPosition)
            if minDistanceFromEnemy > currentDistance:
                minDistanceFromEnemy = currentDistance
                if not minDistanceFromEnemy:
                    minDistanceFromEnemy = -float('inf')
                    break

        if successor.getAgentState(self.index).scaredTimer != 0:
            if minDistanceFromEnemy == 1:
                minDistanceFromEnemy = float('inf')

        features['minDistanceFromEnemy'] = minDistanceFromEnemy

        features['minDistanceFromEnemyPacman'] = 10000
        if not isRed:
            for i in enemyPosition:
                if not successor.isRed(i):
                    distanceFromEnemyPacman = self.distancer.getDistance(i, currentPosition)
                    if features['minDistanceFromEnemyPacman'] > distanceFromEnemyPacman:
                        features['minDistanceFromEnemyPacman'] = distanceFromEnemyPacman
        else:
            for i in enemyPosition:
                if successor.isRed(i):
                    distanceFromEnemyPacman = self.distancer.getDistance(i, currentPosition)
                    if features['minDistanceFromEnemyPacman'] > distanceFromEnemyPacman:
                        features['minDistanceFromEnemyPacman'] = distanceFromEnemyPacman

        if features['minDistanceFromEnemyPacman'] == 10000:
            features['minDistanceFromEnemyPacman'] = 0

        features['successorScore'] = self.getScore(successor)
        return features

    def getWeights(self):
        """
        Normally, weights do not depend on the gamestate.  They can be either
        a counter or a dictionary.
        """
        return {'invaders': -10000, 'myFoodCount': 2, "myPacman": -10000, 'minDistanceFromEnemy': -10,
                'minDistanceFromEnemyPacman': -1000, 'successorScore': 100}

    def chooseAction(self, gameState):
        """
        Picks among the actions with the highest Q(s,a).
        """
        actions = gameState.getLegalActions(self.index)

        # You can profile your evaluation time by uncommenting these lines
        # start = time.time()
        values = [self.evaluate(gameState, a) for a in actions]
        maxValue = max(values)
        bestActions = [a for a, v in zip(actions, values) if v == maxValue]
        foodLeft = len(self.getFood(gameState).asList())

        if foodLeft <= 2:
            bestDist = 9999
            for action in actions:
                successor = self.getSuccessor(gameState, action)
                pos2 = successor.getAgentPosition(self.index)
                dist = self.getMazeDistance(self.start, pos2)
                if dist < bestDist:
                    bestAction = action
                    bestDist = dist
            return bestAction
        return random.choice(bestActions)

    def getSuccessor(self, gameState, action):
        """
        Finds the next successor which is a grid position (location tuple).
        """
        successor = gameState.generateSuccessor(self.index, action)
        pos = successor.getAgentState(self.index).getPosition()
        if pos != nearestPoint(pos):
            # Only half a grid position was covered
            return successor.generateSuccessor(self.index, action)
        else:
            return successor


class OffensiveReflexAgent(CaptureAgent):
    '''TODO'''
    """
    An offensive agent that will immediately head for the side of the opposing
    team and will never chase agents on its own team side. We use several
    features and weights that we iterated to improve by viewing games and
    results. The agent also has limits on carrying so that it will go back
    to the other side after collecting a number of food.
    """

    opps = None
    path = []
    safety = True
    totalFood = 0
    homexCoord = 0

    def registerInitialState(self, gameState):
        self.start = gameState.getAgentPosition(self.index)
        CaptureAgent.registerInitialState(self, gameState)
        global opps
        global totalFood
        global homexCoord
        global safety

        opps = self.getOpponents(gameState)
        totalFood = len(self.getFood(gameState).asList())
        if gameState.isOnRedTeam(self.index):
            homexCoord = (gameState.data.layout.width // 2) -1
        else:
            homexCoord = gameState.data.layout.width // 2
        safety = True


    def chooseAction(self, gameState):
        #TODO
        # start = time.time()

        '''IDEAS AND DECISION TREE:
        if predetermined path, go route with safety variable,
            if safety on, go full route with no questions asked
            else, attempt with avoid ghost on
        else, determine new goal

        goal:
        if score is > 0, use DefensiveReflexAgent chooseAction
            COMMENT: this possible will not be implemented if coordination fails
        else if score + run > 0, return home safely goal
        else:
            if ghosts threat, determine run weight:
                if run < 15% of food left, continue run
                else, attempt returnHome
            else, continue run'''
        """

                '''
            return 0
            ## TODO:
        def avoid():
            '''This will be the function to avoid ghosts in case safety is off
            decisions will be based on prediction and ghost locations
            params are self, gameState, run(current carrying food), and capsuleWorth'''
            return 0
            ## TODO:
        def getFeatures():
            ## TODO:
            return 0

        def capsuleWeight():
            #TODO:
            return 0"""

        global path
        global safety
        global totalFood
        global opps

        targets = self.getFood(gameState).asList()
        #powerUps = self.getCapsules(gameState)
        score = CaptureAgent.getScore(self, gameState)
        actions = gameState.getLegalActions(self.index)

        run = gameState.getAgentState(self.index).numCarrying
        pathTest = "yes" if self.path else "no"
        print("if path: " , pathTest)
        if self.path and safety:
            print("in safety branch")
            return self.makeMove(gameState, actions)


        elif self.path and not safety:
            print("in not safety branch")
            myPos = gameState.getAgentState(self.index).getPosition()
            for o in opps:
                enemyPos = gameState.getAgentState(o).getPosition()
                #if self.getMazeDistance(myPos, enemyPos) < 3:
                    #return self.avoid(gameState, actions)
                #else:
                    #return self.makeMove(gameState, actions)

        else:
            print("start goal generation")
            if score + run > 0 and gameState.getAgentState(self.index).isPacman:
                self.path = self.returnHome(gameState)
                if self.path == False:
                    print("did not find a path")
                    return random.choice(actions)

            elif len(targets) < run and gameState.getAgentState(self.index).isPacman:
                self.path = self.returnHome(gameState)
                if self.path == False:
                    print("did not find a path")
                    return random.choice(actions)

            else:
                self.path = self.genGoal(gameState, targets)
                safety = self.calculateSafety(gameState)
                if self.path == False:
                    print("did not find a path")
                    return random.choice(actions)

        #after decision tree
        return self.makeMove(gameState, actions)

    def avoid(self, gameState, actions):
        myPos = gameState.getAgentState(self.index).getPosition()
        global opps
        for o in opps:
            enemyPos = gameState.getAgentState(o).getPosition()
            enemyDir = gameState.getAgentState(o).getDirection()
            gPathing = self.aStar(gameState, o, myPos)
            ghostPath = self.generatePath(gPathing[0], gPathing[1], o)
            if ghostPath:
                if len(ghostPath) > 2:
                    continue
                '''else:
                    dir = (ghostPath[0]-enemyPos[0], ghostPath[1]-enemyPos[1])
                    print("dir: ", dir)
                    enemyPreAction = None
                    if dir[0] == 0:
                        if dir[1] > 0:
                            enemyPreAction = gameState.data.'''


        return self.makeMove(gameState, actions)


    def calculateSafety(self, gameState):
        global path
        global opps
        if self.path:
            for o in opps:
                enemyPos = gameState.getAgentState(o).getPosition()
                pathCounter = 1
                for p in self.path:
                    if self.getMazeDistance(enemyPos, p) <= pathCounter:
                        gPathing = self.aStar(gameState, o, p)
                        ghostPath = self.generatePath(gPathing[0], gPathing[1], o)
                        if len(ghostPath) < len(self.path):
                            return False
                    else:
                        pathCounter += 1
            return True

    def makeMove(self, gameState, actions):
        global path
        nextMove = self.path.pop(0)
        bestAction = None
        bestDist = 9999
        for action in actions:
            successor = self.getSuccessor(gameState, self.index, action)
            pos2 = successor.getAgentPosition(self.index)
            dist = self.getMazeDistance(nextMove, pos2)
            if dist < bestDist:
                bestAction = action
                bestDist = dist
        if len(self.path) == 0:
            self.path = None
        return bestAction


    def genGoal(self, gameState, targets):
        if len(targets) > 0:
            myPos = gameState.getAgentState(self.index).getPosition()
            #min dist finder
            minDist = 9999999
            bestT = None
            for t in targets:
                if bestT == None:
                    minDist = self.getMazeDistance(myPos, t)
                    bestT = t
                    continue
                currFDist = self.getMazeDistance(myPos, t)
                if currFDist < minDist:
                    bestT = t
                    minDist = currFDist

            closedList = self.aStar(gameState, self.index, bestT)
            if closedList != False:
                return self.generatePath(closedList[0],closedList[1], self.index)
            return False


    def returnHome(self, gameState):
        '''Decisions will be based on safe routing home
            This will be determined on ghost positions
            First, determine capsule weight and worth:
                if score + run > 0, capsule avoidance off
                if food amount > 50% of food left, find capsules
            if ghosts cannot reach path for pacman, set goal path home with safety on
            else, attempt goal path with safety off'''
        myPos = gameState.getAgentState(self.index).getPosition()
        global homexCoord
        targets = []
        for i in range(1,gameState.data.layout.height-1):
            coord = (homexCoord, i)
            if not gameState.data.layout.isWall(coord):
                targets.append((homexCoord, i))
        minDist = 9999999
        bestT = None
        for t in targets:
            if bestT == None:
                minDist = self.getMazeDistance(myPos, t)
                bestT = t
                continue
            currFDist = self.getMazeDistance(myPos, t)
            if currFDist < minDist:
                bestT = t
                minDist = currFDist

        c = self.aStar(gameState, self.index,bestT)
        if c != False:
            return self.generatePath(c[0], c[1], self.index)
        return False

    def generatePath(self, closedList, end, agentI):
        if closedList != False:
            fullPath = []
            curr = end
            while closedList[curr][0] != None:
                fullPath.insert(0, curr)
                curr = closedList[curr][0].getAgentState(agentI).getPosition()
            return fullPath
        else:
            return False

    def aStar(self, gameState, agentI, target):
        print("start aStar func, target: ", target)
        openList = []
        closedList = {}
        startPos = gameState.getAgentState(agentI).getPosition()
        openList.append([None, gameState, 0 , self.getMazeDistance(startPos, target)])
        while openList:
            #print("current list size: ", len(openList))
            q = openList.pop(0)
            currPos = q[1].getAgentPosition(agentI)
            #print("q position: ", currPos)
            if currPos in closedList.keys():
                if closedList[currPos][2] >= q[3]:
                    #print("updating closedList")
                    closedList[currPos] = [q[0],q[2],q[3]]
            else:
                #print("adding ", currPos, " to closedList")
                closedList[currPos] = [q[0],q[2],q[3]]
            #if found stop insert here
            #print("closedList: ", closedList, "\n\n")
            #print("entering actions loop")
            #print("list of actions: ",q[1].getLegalActions(self.index))
            for a in q[1].getLegalActions(agentI):
                print("action: ",a)

                #conditional to determine if successor gets added to open list
                add = True

                #generation of successor
                #print("start successor gen")
                succ = self.getSuccessor(q[1], agentI, a)
                succPos = succ.getAgentPosition(agentI)
                #print("passed successor gen ", succPos)

                #print("test if goal")
                if succPos == target:
                    print("goal")
                    closedList[succPos] = [q[1], 0, 0]
                    return [closedList, succPos]
                #print("no goal\n")
                #index 3 f cost calculation
                #print("calculating fcost")
                fCost = (q[2]+1) + self.getMazeDistance(succPos, target)
                #print("fCost of ", succPos ,": ",fCost,"\n")

                '''if openlist contains node with lower f cost, skip this node
                if closedList contains node with lower f cost, skip this node
                else, add node to openList'''
                insertIndex = 0
                for o in openList:
                    if o[1].getAgentState(agentI).getPosition() == succPos and o[3] < fCost:
                        #print("openList better cost")
                        add = False
                        break
                    elif o[3] > fCost:
                        break
                    else:
                        insertIndex += 1
                if succPos in closedList:
                    if closedList[succPos][2] < fCost:
                        #print("closedList better cost")
                        add = False
                if add:
                    #print("adding ", a, "to reach ", succ.getAgentPosition(self.index), "at index ", insertIndex)
                    #print("adding ", [q[1], succ, q[2]+1, fCost], " to openList")
                    openList.insert(insertIndex, [q[1], succ, q[2]+1, fCost])
                #end Loop
            #end loop
        print("no path")
        return False


    def getSuccessor(self, gameState, agentI, action):
        """
    Finds the next successor which is a grid position (location tuple).
    """
        successor = gameState.generateSuccessor(agentI, action)
        pos = successor.getAgentState(agentI).getPosition()
        if pos != nearestPoint(pos):
            # Only half a grid position was covered
            return successor.generateSuccessor(agentI, action)
        else:
            return successor
