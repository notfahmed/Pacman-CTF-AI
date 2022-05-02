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

    def registerInitialState(self, gameState):
        self.start = gameState.getAgentPosition(self.index)
        CaptureAgent.registerInitialState(self, gameState)
        CaptureAgent.getOpponents(self, gameState)

    def chooseAction(self, gameState):
        #TODO
        targets = CaptureAgent.getFood(self, gameState)
        powerUps = CaptureAgent.getCapsules(self, gameState)
        score = CaptureAgent.getScore(self, gameState)
        actions = gameState.getLegalActions(self.index)

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
            else, continue run

            else, continue search'''
        def returnHome():
            '''Decisions will be based on safe routing home
                This will be determined on ghost positions
                First, determine capsule weight and worth:
                    if score + run > 0, capsule avoidance off
                    if food amount > 50% of food left, find capsules
                if ghosts cannot reach path for pacman, set goal path home with safety on
                else, attempt goal path with safety off

                '''
            ## TODO:
        def avoid():
            '''This will be the function to avoid ghosts in case safety is off
            decisions will be based on prediction and ghost locations
            params are self, gameState, run(current carrying food), and capsuleWorth'''
            ## TODO:
        def getFeatures():
            ## TODO:
            return 0




        return random.choice(actions)





    def evaluationFunction(self, gameState):
        #to do
        return 0
