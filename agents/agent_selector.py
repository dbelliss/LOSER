# https://chatbotslife.com/building-a-basic-pysc2-agent-b109cde1477c
from pysc2.agents import base_agent
from pysc2.lib import actions
from pysc2.lib import features
from pprint import pprint
import smart_agent
import simple_agent
import time


class AgentSelector(base_agent.BaseAgent):
    def __init__(self):
        super().__init__()
        # prints out fields for self
        pprint(dir(self))
        self.agents = [simple_agent.SimpleAgent(), smart_agent.SmartAgent()]
        self.stepsPerAgent = 100
        self.curAgentIndex = 0
        self.curStep = 0
        self.timesSwitched = 0

    def step(self, time_step):
        super().step(time_step)

        self.curStep += 1
        if self.curStep == self.stepsPerAgent:
            self.curStep = 0
            self.curAgentIndex = (self.curAgentIndex + 1) % len(self.agents)
            self.agents[self.curAgentIndex].ResetBeliefState()
            self.timesSwitched += 1

        return self.agents[self.curAgentIndex].step(time_step)
