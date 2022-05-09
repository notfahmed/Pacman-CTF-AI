# Author: Fawaz Ahmed

from captureAgents import CaptureAgent
import random
import util
from util import nearestPoint
from game import Directions

#################
# Team creation #
#################
isRed = True
defPosition = None
offPosition = None


def createTeam(firstIndex, secondIndex, isRed_,
               first='DefensiveReflexAgent', second='OffensiveReflexAgent'):
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
        global defPosition

        features = util.Counter()
        successor = gameState.generateSuccessor(self.index, action)
        enemies = self.getOpponents(successor)
        currentPosition = successor.getAgentPosition(self.index)
        defPosition = currentPosition

        # Get positions of all enemies
        enemyPosition = []
        for i in enemies:
            enemyPosition.append(successor.getAgentPosition(i))

        # Get if there are Pacman in my team's territory
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

        # Make sure my defender does not go into the enemy territory and become a pacman

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

        # Keep track of the food I have to protect
        myFoodCount = 0
        for i in self.getFood(successor):
            myFoodCount += sum(i)
        features['myFoodCount'] = myFoodCount

        # Get as close as possible to the enemy without crossing the midborder
        minDistanceFromEnemy = float('inf')
        for k in enemies:
            currentDistance = self.distancer.getDistance(successor.getAgentPosition(k), currentPosition)
            if minDistanceFromEnemy > currentDistance:
                minDistanceFromEnemy = currentDistance
                if not minDistanceFromEnemy:
                    minDistanceFromEnemy = -float('inf')
                    break

        # If scared then stay 1 block away but keep chasing
        if successor.getAgentState(self.index).scaredTimer != 0:
            if minDistanceFromEnemy == 1:
                minDistanceFromEnemy = float('inf')

        # chase enemy pacman that is in my territory
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

        # print(features['minDistanceFromEnemyPacman'])

        features['successorScore'] = self.getScore(successor)
        return features

    def getWeights(self):
        """
        Normally, weights do not depend on the gamestate.  They can be either
        a counter or a dictionary.
        """
        return {'invaders': -1000, 'myFoodCount': 200, "myPacman": -10000, 'minDistanceFromEnemy': -10,
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

    def registerInitialState(self, gameState):
        self.start = gameState.getAgentPosition(self.index)
        CaptureAgent.registerInitialState(self, gameState)

    def chooseAction(self, gameState):
        """
        Picks among the actions with the highest Q(s,a).
        """
        actions = gameState.getLegalActions(self.index)

        # You can profile your evaluation time by uncommenting these lines
        # start = time.time()
        values = [self.evaluate(gameState, a) for a in actions]
        # print('eval time for agent %d: %.4f' % (self.index, time.time() - start))

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

    def evaluate(self, gameState, action):
        """
        Computes a linear combination of features and feature weights
        """
        weights = self.getWeights(gameState, action)
        features = self.getFeatures(gameState, action)

        evaluation = 0
        for k in weights.keys():
            evaluation += weights[k] * features[k]

        return evaluation

    def getFeatures(self, gameState, action):
        global offPosition
        global stuck

        features = util.Counter()
        successor = self.getSuccessor(gameState, action)
        foodList = self.getFood(successor).asList()
        currentPosition = successor.getAgentPosition(self.index)
        capsules = self.getCapsules(successor)

        offPosition = currentPosition

        if len(foodList) > 0:  # This should always be True,  but better safe than sorry
            myPos = successor.getAgentState(self.index).getPosition()
            minDistance = min([self.getMazeDistance(myPos, food) for food in foodList])
            # if not successor.getAgentState(self.index).isPacman: #this basically means we only look for food if
            # we're on the other side minDistance = 100
            features['minDistanceToFood'] = minDistance

        # Foodleft count
        features['foodLeft'] = len(foodList)

        # Calculate the minimum distance from an enemy
        enemies = self.getOpponents(successor)
        enemyPositions = []
        for enemy in enemies:
            if not successor.getAgentState(enemy).isPacman:
                enemyPositions.append(successor.getAgentPosition(enemy))

        enemyDistances = []
        for enemyPosition in enemyPositions:
            enemyDistances.append(self.distancer.getDistance(currentPosition, enemyPosition))

        minEnemyDistance = 10
        if len(enemyDistances) and min(enemyDistances) < 3 and successor.getAgentState(self.index).isPacman:
            minEnemyDistance = min(enemyDistances)
        features['minEnemyDistance'] = minEnemyDistance

        # keep track of how many pellets I am carrying
        eaten = gameState.getAgentState(self.index).numCarrying
        features['eaten'] = eaten

        # Dont go too far from the middle border
        if gameState.isOnRedTeam(self.index):
            xCoordinate = (gameState.data.layout.width // 2) - 1
        else:
            xCoordinate = gameState.data.layout.width // 2

        minDist = float('inf')
        middleCoordinates = []
        for yCoordinate in range(gameState.data.layout.height):
            try:
                distance = self.distancer.getDistance((xCoordinate, yCoordinate), currentPosition)
                middleCoordinates.append((xCoordinate, yCoordinate))
                if minDist > distance:
                    minDist = distance
            except:
                continue

        if eaten > 0:
            features['middleBorder'] = minDist
        else:
            features['middleBorder'] = 0

        # Get number of invaders. if there are invaders that means there are less defenders (go aggressive)
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

        # This part is basically if an enemy is chasing you, and you are close to a capsule than the middle border
        # Then go to the capsule
        if features['minEnemyDistance'] < 10:
            for capsule in capsules:
                capDistance = self.distancer.getDistance(capsule, currentPosition)
                if capDistance < minDist:
                    features['capsule'] = 1
        else:
            features['capsule'] = 0

        # No dying
        if currentPosition == self.start:
            features['dead'] = 10000000

        # No stopping
        if action == Directions.STOP:
            features['stop'] = 1

        # No reversing
        previousDirection = Directions.REVERSE[gameState.getAgentState(self.index).configuration.direction]
        if action == previousDirection:
            features['reverse'] = 1

        # Don't take same route as defending teammate
        if isRed:
            if not gameState.isRed(currentPosition):
                features['distanceFromFriendly'] = 0
            else:
                if defPosition is not None:
                    features['distanceFromFriendly'] = abs(defPosition[1] - currentPosition[1]) // 2
                else:
                    features['distanceFromFriendly'] = 0
        elif gameState.isRed(currentPosition):
            features['distanceFromFriendly'] = 0
        else:
            if defPosition is not None:
                features['distanceFromFriendly'] = abs(defPosition[1] - currentPosition[1]) // 2
            else:
                features['distanceFromFriendly'] = 0

        # Dont be a ghost
        if isRed:
            if not gameState.isRed(currentPosition):
                isGhost = 0
            else:
                isGhost = 1
        elif gameState.isRed(currentPosition):
            isGhost = 0
        else:
            isGhost = 1
        features['isGhost'] = isGhost

        return features

    def getWeights(self, gameState, action):
        return {'foodLeft': -100, 'minDistanceToFood': -1, 'minEnemyDistance': 100, 'middleBorder': -100,
                'invaders': 20, 'eaten': -10, 'capsule': -1000, 'dead': -1, 'stop': -75, 'reverse': -50,
                'distanceFromFriendly': 1, 'isGhost': -10}
