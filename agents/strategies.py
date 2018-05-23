from enum import Enum

'''
Possible strategies each bot can use
The strategy will be given to an agent's on_step function by the agent_selector
The agent_select will decide on a strategy through a Q table
'''
class Strategies(Enum):
    # Offensive
    HEAVY_ATTACK = 0
    MEDIUM_ATTACK = 1
    LIGHT_ATTACK = 2

    # Scouting
    HEAVY_SCOUTING = 3
    MEDIUM_SCOUTING = 4
    LIGHT_SCOUTING = 5

    # Defensive
    HEAVY_DEFENSE = 6
    MEDIUM_DEFENSE = 7
    LIGHT_DEFENSE = 8

    # Harassing
    HEAVY_HARASS = 9
    MEDIUM_HARASS = 10
    LIGHT_HARASS = 11

    @classmethod
    def has_value(cls, value):
        return any(value == item.value for item in cls)
