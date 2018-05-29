#!/usr/bin/python3
# https://chatbotslife.com/building-a-basic-pysc2-agent-b109cde1477c
# Debug imports
from pprint import pprint
from time import gmtime, strftime, localtime
import sys
import os
# python-sc2 imports
import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer

# agent imports
from loser_agent import *
from saferoach_agent import SafeRoachAgent
from zerglingBanelingRush_agent import SpawnPoolRavagerAgent
from NeuralNetwork import NeuralNetwork
from strategies import Strategies
import time


# Coloring for terminal output
# https://stackoverflow.com/questions/287871/print-in-terminal-with-colors
class bcolors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
UNDERLINE = '\033[4m'


class AgentSelector(LoserAgent):
    def __init__(self, is_logging = False, is_printing_to_console = False, isMainAgent = False):
        super().__init__(is_logging, is_printing_to_console, isMainAgent, "AgentSelector_")
        print(bcolors.OKGREEN + "###AgentSelector Constructor" + bcolors.ENDC)

        # List of build orders
        self.agents = [LoserAgent(), LoserAgent()]
        self.nAgents = len(self.agents)

        # Choose RandomBuild
        self.chooseRandomBuild()

        # Number of strategies
        self.strategies = Strategies
        self.nStrategies = len(Strategies)

        # Choose RandomStrategy
        self.chooseRandomStrategy()

        # Properties
        self.stepsPerAgent = 100
        self.curAgentIndex = 0
        self.strategiesIndex = 0
        self.curStep = 0
        self.timesSwitched = 0

        self.prevInputs = [0]
        self.prevAgent = 0
        self.prevStrategy = 0
        self.lastFitness = 0

        # number of calculated inputs such as army size, mineral rate, etc. prevInput list must be same length as this value
        self.nInputs = 1

        # inputs = nData inputs + nAgents (for last agent selected) + nStrategies (for last strategy selected)
        # outputs = nAgents
        self.agentNN = NeuralNetwork(self.nInputs + self.nAgents + self.nStrategies, self.nAgents, 1, 1, 100)

        # inputs = nData inputs + 2 * nAgents (for last and current agent selected) + nStrategies (for last strategy selected)
        # outputs = nStrategies
        self.strategyNN = NeuralNetwork(self.nInputs + 2 * self.nAgents + self.nStrategies, self.nStrategies, 1, 1, 100)

    def fitness(self):
        #self.idle_workers = self.mainAgent.workers.idle.amount
        return (self.lastFitness + .5) % 1

    def chooseRandomBuild(self):
        self.curAgentIndex = 0
        print(bcolors.OKGREEN + "###RandomBuildIndex: {}".format(self.agents[self.curAgentIndex]) + bcolors.ENDC)

    def chooseRandomStrategy(self):
        self.strategiesIndex = 0
        print(bcolors.OKGREEN + "###RandomStrategyIndex: {}".format(self.strategiesIndex) + bcolors.ENDC)

    async def on_step(self, iteration):
        self.log("Step: %s Idle Workers: %s Overlord: %s Workers: %s" % (str(iteration), str(self.mainAgent.workers.idle.amount), str(self.mainAgent.units(OVERLORD).amount), str(self.mainAgent.workers.amount)))

        # Run fitness on a certain number of steps
        if (iteration % self.stepsPerAgent == 0):
            print(bcolors.OKGREEN + "###Fitness function: {}".format(iteration) + bcolors.ENDC)
            self.learn()
            self.selectNewAgentsAndStrategies()

        # TODO
        # Call the current agent on_step
        await self.agents[self.curAgentIndex].on_step(iteration)


    def learn(self):
        curFitness = self.fitness()

        #bogus correct choice and fitness equations for now
        correctChoice = 1 if curFitness > self.lastFitness else 0
        self.lastFitness = curFitness

        #create list for all the inputs to the neural network
        prevAgent = [0] * self.nAgents
        prevStrategy = [0] * self.nStrategies
        curAgent = [1 - correctChoice] * self.nAgents
        curStrategy = [1 - correctChoice] * self.nStrategies

        #this is for the predicted agent that was used as input for the strategy NN. Must be 1 hot like it was during prediction
        predAgent = [0] * self.nAgents

        #set the 1 hot encoding for prev agents and certainty that the current choice was correct
        #these are part of the X's that are used to teach the NN
        prevAgent[self.prevAgent] = 1
        prevStrategy[self.prevStrategy] = 1
        predAgent[self.curAgentIndex] = 1

        #set certainty that the choice was correct
        #these are the y's
        curAgent[self.curAgentIndex] = correctChoice
        curStrategy[self.strategiesIndex] = correctChoice

        #appends all the input lists together, also puts them into lists of lists for the NN 
        # ie [1, 2, 3] + [4, 5] => [[1, 2, 3, 4 ,5]]
        agentInputList = [self.prevInputs + prevAgent + prevStrategy]
        agentOutputList = [curAgent]
        strategyInputList = [self.prevInputs + predAgent + prevAgent + prevStrategy]
        strategyOutputList = [curStrategy]
        self.log("Training agentNN with inputs: {0} and outputs {1}".format(str(agentInputList), str(agentOutputList)))
        self.log("Training strategyNN with inputs: {0} and outputs {1}".format(str(strategyInputList), str(strategyOutputList)))
        self.agentNN.train(agentInputList, agentOutputList)
        self.strategyNN.train(strategyInputList, strategyOutputList)


    def selectNewAgentsAndStrategies(self):

        #define other inputs to NN
        curInputs = [0]

        #create list for all the inputs to the neural network
        curAgent = [0] * self.nAgents
        curStrategy = [0] * self.nStrategies

        #set previous choices as 1 hot
        curAgent[self.curAgentIndex] = 1
        curStrategy[self.strategiesIndex] = 1

        #appends all the input lists together, also puts them into lists of lists for the NN 
        # ie [1, 2, 3] + [4, 5] => [[1, 2, 3, 4 ,5]]
        agentInputList = [curInputs + curAgent + curStrategy]
        self.log("Predicting agentNN with inputs: {0}".format(str(agentInputList)))
        
        nextAgent = self.agentNN.predict(agentInputList)[0].tolist() #extract first row from returned numpy array
        nextAgentIndex = nextAgent.index(max(nextAgent))
        nextAgent = [nextAgent[i] if i == nextAgentIndex else 0 for i in range(len(nextAgent))]

        strategyInputList = [curInputs + nextAgent + curAgent + curStrategy]
        self.log("Predicting strategyNN with inputs: {0}".format(str(strategyInputList)))
        nextStrategy = self.strategyNN.predict(strategyInputList)[0].tolist() #extract first row from returned numpy array

        self.prevAgent = self.curAgentIndex
        self.prevStrategy = self.strategiesIndex
        self.prevInputs = curInputs
        self.curAgentIndex = nextAgentIndex
        self.strategiesIndex = nextStrategy.index(max(nextStrategy))

def main():
    # Start game with AgentSelector as the Bot, and begin logging
    sc2.run_game(sc2.maps.get("Abyssal Reef LE"), [
        Bot(Race.Zerg, AgentSelector(True, True, True)),
        Computer(Race.Protoss, Difficulty.Medium)
    ], realtime=False)

if __name__ == '__main__':
    main()
