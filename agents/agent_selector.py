#!/usr/bin/python3
import random

# Debug imports
from pprint import pprint
import time
import sys
# python-sc2 imports
import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer

# agent imports
from loser_agent import LoserAgent
from saferoach_agent import SafeRoachAgent
from zerglingBanelingRush_agent import SpawnPoolRavagerAgent

class Fitness(LoserAgent):
    def __init__(self, is_logging = True):
        super().__init__()
        self.idle_workers = self.workers.idle.amount

        # For debugging
        self.is_logging = is_logging
        if self.is_logging:

            # Make logs directory if it doesn't exist
            if not os.path.exists("./logs"):
                os.mkdir("./logs")
            self.log_file_name = "./logs/" + strftime("%Y-%m-%d %H:%M:%S", localtime()) + ".log"
            self.log_file = open(self.log_file_name, "w+")  # Create log file based on the time

    def __repr__(self):
        return f"idle workers: {self.idle_workers}"

class AgentSelector(sc2.BotAI):
    def __init__(self):
        super().__init__()
        self.agents = [SafeRoachAgent(LoserAgent()), SpawnPoolRavagerAgent(LoserAgent())]
        # self.agents = [loser_agent.LoserAgent(True)]
        self.stepsPerAgent = 100
        self.curAgentIndex = 0
        self.curStep = 0
        self.timesSwitched = 0

    async def on_step(self, iteration):
        self.log("Step: %s Idle Workers: %s Overlord: %s" % (str(iteration), str(self.get_idle_workers), str(self.units(OVERLORD).amount)))
        self.log(self.fitness.__repr__())

def main():
    # Start game with LoserAgent as the Bot, and begin logging
    sc2.run_game(sc2.maps.get("Abyssal Reef LE"), [
        Bot(Race.Zerg, LoserAgent(True)),
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
