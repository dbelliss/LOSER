#!/usr/bin/python3
from random import randint

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
from loser_agent import LoserAgent
from saferoach_agent import SafeRoachAgent
from zerglingBanelingRush_agent import SpawnPoolRavagerAgent

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

class Fitness(LoserAgent):
    def __init__(self):
        super().__init__()
        print(bcolors.OKGREEN + "###Fitness Constructor" + bcolors.ENDC)
        self.idle_workers = self.get_idle_workers()

    def __repr__(self):
        return f"idle workers: {self.idle_workers}"

class AgentSelector(LoserAgent):
    def __init__(self, is_logging = False):
        super().__init__()

        # For debugging
        self.is_logging = is_logging
        if self.is_logging:

            # Make logs directory if it doesn't exist
            if not os.path.exists("./logs"):
                os.mkdir("./logs")
            self.log_file_name = "./logs/" + "AgentSelector_" + strftime("%Y-%m-%d %H:%M:%S", localtime()) + ".log"
            self.log_file = open(self.log_file_name, "w+")  # Create log file based on the time

        print(bcolors.OKGREEN + "###AgentSelector Constructor" + bcolors.ENDC)

        # List of build orders
        self.agents = [SafeRoachAgent(is_logging), SpawnPoolRavagerAgent(is_logging)]

        # List of strategies
        self.strategies = []

        # Properties
        self.stepsPerAgent = 100
        self.curAgentIndex = 0
        self.strategiesIndex = 0
        self.curStep = 0
        self.timesSwitched = 0

        # Choose RandomAgent
        self.curAgentIndex = randint(0,1)
        print(bcolors.OKGREEN + "###RandomIndex: {}".format(self.curAgentIndex) + bcolors.ENDC)

        # TODO
        # Call constructor for current agent
        # self.agents[self.curAgentIndex].__init__()

    async def on_step(self, iteration):
        # TODO
        # Get Fitness on every step
        # fitness = Fitness()
        # self.log(fitness.__repr__)

        # TODO
        # Call the current agent on_step
        # await self.agents[self.curAgentIndex].on_step(iteration)
        self.log("agent selector on step")
        pass

def main():
    # Start game with AgentSelector as the Bot, and begin logging
    sc2.run_game(sc2.maps.get("Abyssal Reef LE"), [
        Bot(Race.Zerg, AgentSelector(True)),
        Computer(Race.Protoss, Difficulty.Medium)
    ], realtime=False)

if __name__ == '__main__':
    main()

    # pysc2 old agent selector
    # def step(self, time_step):
    #     super().step(time_step)
    #
    #     self.curStep += 1
    #     if self.curStep == self.stepsPerAgent:
    #         self.curStep = 0
    #         self.curAgentIndex = (self.curAgentIndex + 1) % len(self.agents)
    #         self.agents[self.curAgentIndex].ResetBeliefState()
    #         self.timesSwitched += 1
    #
    #     return self.agents[self.curAgentIndex].step(time_step)
