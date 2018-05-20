# https://chatbotslife.com/building-a-basic-pysc2-agent-b109cde1477c
import asyncio
import random

import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer

from pprint import pprint
from time import gmtime, strftime, localtime
import os

# For debugging purposes only
import sys

# Get strategy enums
from strategies import Strategies

class LoserAgent(sc2.BotAI):
    base_top_left = None
    overlord_built = False
    larva_selected = False
    drone_selected = False
    spawning_pool_built = False
    spawning_pool_selected = False
    spawning_pool_rallied = False
    army_selected = False
    army_rallied = False

    def __init__(self, is_logging = False, is_printing_to_console = False):
        super().__init__()

        # For debugging
        self.is_logging = is_logging  # Setting this to true to write information to log files in the agents/logs directory
        self.is_printing_to_console = is_printing_to_console  # Setting this to true causes all logs to be printed to the console

        # Make logs directory if it doesn't exist
        if not os.path.exists("./logs"):
            os.mkdir("./logs")
        self.log_file_name = "./logs/" + strftime("%Y-%m-%d %H:%M:%S", localtime()) + ".log"
        self.log_file = open(self.log_file_name, "w+")  # Create log file based on the time

        # Constants
        self.researched = 2  # If an upgrade has been research
        self.is_researching = 1  # If an upgrade is being researched
        self.not_researched = 0  # If an upgrade is not being researched and has not been researched

        # non-standard upgrades purchased
        self.can_burrow = None # true if Burrow has been purchased
        self.zergling_speed = None # True if Metabolic Boost has been purchased
        self.zergling_attack_boost = None  # True if Adrenal glands has been purchased
        self.baneling_speed = None # True if Centrifugal Hooks has been purchased
        self.roach_speed = None  # True if Glial Reconstruction has been purchased
        self.roach_tunnel = None  # True if Tunneling Claws reconstruction has been purchased
        self.overlord_speed = None  # True if Pneumatized Carapace has been purchsed
        self.hydralisk_range = None  # True if Grooved Spines has been purchased
        self.infestor_parasite = None  # True if Neural parasite has been purchased
        self.infestor_energy = None  # True if Pathogen Glands has been purchased
        self.ultralisk_defense = None  # True if Chitinous Plating has been purchased

        self.strike_force = None  # Units actively being used for things, gets set to null on strategy change

        self.prev_strategy = None  # Previous strategy so you now when the strategy changes
        self.did_strategy_change = False  # True if strategy just changed in this iteration
        # standard upgrades
        # TODO

    '''
    Base on_step function
    Will only do something if it is given a strategy_num
    '''
    async def on_step(self, iteration, strategy_num = 2):
        self.log("Step: %s Idle Workers: %s Overlord: %s" % (str(iteration), str(self.get_idle_workers), str(self.units(OVERLORD).amount)))
        self.log("Step: " + str(iteration))

        if strategy_num == -1:
            self.log("No given strategy")
        else:
            # Make sure given strategy num is valid
            if Strategies.has_value(strategy_num):
                # Valid strategy num, convert int into enum value
                strategy = Strategies(strategy_num)
                self.log("Strategy is " + str(strategy))

                # Mark strategy as changed or not
                if strategy != self.prev_strategy:
                    self.did_strategy_change = True
                    self.strike_force = None
                else:
                    self.did_strategy_change = False

                self.prev_strategy = strategy  # Prepare for next iteration

                # Call the proper strategy function
                await self.perform_strategy(iteration, strategy)
            else:
                # Not valid strategy num
                self.log_error("Unknown strategy " + str(strategy_num))

    '''
    Calls the correct strategy function given the strategy enum value
    Strategy functions can be override in base classes
    '''
    async def perform_strategy(self, iteration, strategy):
        self.clean_strike_force()  # Clear dead units from strike force
        # Attack
        if strategy == Strategies.HEAVY_ATTACK:
            await self.heavy_attack(iteration)
        elif strategy == Strategies.MEDIUM_ATTACK:
            await self.medium_attack(iteration)
        elif strategy == Strategies.LIGHT_ATTACK:
            await self.light_attack(iteration)

        # Scouting
        elif strategy == Strategies.HEAVY_SCOUTING:
            await self.heavy_scouting(iteration)
        elif strategy == Strategies.MEDIUM_SCOUTING:
            await self.medium_scouting(iteration)
        elif strategy == Strategies.LIGHT_SCOUTING:
            await self.light_scouting(iteration)

        # Defense
        elif strategy == Strategies.HEAVY_DEFENSE:
            await self.heavy_defense(iteration)
        elif strategy == Strategies.MEDIUM_DEFENSE:
            await self.medium_defense(iteration)
        elif strategy == Strategies.LIGHT_DEFENSE:
            await self.light_defense(iteration)

        # Harass
        elif strategy == Strategies.HEAVY_HARASS:
            await self.heavy_harass(iteration)
        elif strategy == Strategies.MEDIUM_HARASS:
            await self.medium_harass(iteration)
        elif strategy == Strategies.LIGHT_HARASS:
            await self.light_harass(iteration)

        # Unknown
        else:
            self.log("Unknown strategy was given: " + str(strategy))

    '''
    Send all combat units (including the queen) to a known enemy position
    Do NOT recall ever
    '''
    async def heavy_attack(self, iteration):
        await self.attack_with_percentage_of_army(1)

    '''
    Send all combat units (including the queen) to a known enemy position
    Recall after a certain amount of units die 
    Must keep track of units being used because order of units in self.units constantly changes
    '''
    async def medium_attack(self, iteration):
        await self.attack_with_percentage_of_army(.6)
    '''
    Attack a known enemy position, but if you get attacked, retreat back to base
    '''

    async def light_attack(self, iteration):
        await self.attack_with_percentage_of_army(.3)


    async def attack_with_percentage_of_army(self, percentage):
        army = self.army

        if len(army) == 0:
            # No army to use, don't bother trying to attack
            return

        desired_strike_force_size = int(percentage * army.amount)
        self.log(f"{desired_strike_force_size} is desired size")
        # Strategy just changed, need to take a strike_force
        if self.strike_force is None:
            self.strike_force = army.take(desired_strike_force_size)

        # If strike force should include more members (If a unit was built)
        # Do not add more units if the entire army is already in strike force
        if len(self.strike_force) < desired_strike_force_size and len(army) > len(self.strike_force):
            self.strike_force += (army - self.strike_force).take(desired_strike_force_size - len(self.strike_force))

        self.log(f"Size of striek force is {len(self.strike_force)}")

        # By now we must have at least 1 offensive unit
        target = self.select_target()
        unselected_army = army - self.strike_force

        # All strike force members attack
        for unit in self.strike_force:
            self.log(unit.tag)
            await self.do(unit.attack(target))

        # # Remaining offensive units just wait at their position
        # for unit in unselected_army:
        #     await self.do(unit.hold_position())

    '''
    Send all military units out to different areas
    Die for knowledge
    '''
    async def heavy_scouting(self, iteration):
        pass

    '''
    Send a good amount of military units out
    '''
    async def medium_scouting(self, iteration):
        pass

    '''
    Send a couple of things out for scouting and pull back if damage is taken
    '''
    async def light_scouting(self, iteration):
        pass

    '''
    Complete recall back to main base
    Build lots of static defenses
    Build lots of lurkers 
    '''
    async def heavy_defense(self, iteration):
        pass

    '''
    Recall and distribute between main base and explansions
    Build some defensive structures and units
    '''
    async def medium_defense(self, iteration):
        pass

    '''
    Distribute forces between main base and expansions
    Build a few defensive structures and units
    '''
    async def light_defense(self, iteration):
        pass

    '''
    Build swarms hosts and harass with them
    Build mutalisks and harass with them
    If harass units are attacked, move to the next base
    '''
    async def heavy_harass(self, iteration):
        pass

    '''
    TODO
    '''
    async def medium_harass(self, iteration):
        pass

    '''
    If attacked pull back for a set time
    Only use harass units if you have them
    '''
    async def light_harass(self, iteration):
        pass

    '''
    Removes dead untis from strike force
    '''
    def clean_strike_force(self):
        if self.strike_force is None:
            # No defined strike force yet
            return
        for unit in self.strike_force:
            if self.units.find_by_tag(unit.tag) is None:
                self.strike_force.remove(unit)
    '''
    Utilities
    '''
    @property
    def army(self):
        return self.units - self.units(DRONE) - self.units(OVERLORD) - self.units(LARVA) - self.units(EGG)- self.buildings

    @property
    def buildings(self):
        return self.units(HATCHERY) + self.units(LAIR) + self.units(HIVE) + self.units(EXTRACTOR) + self.units(SPAWNINGPOOL) \
               + self.units(ROACHWARREN) + self.units(CREEPTUMOR) + self.units(EVOLUTIONCHAMBER) + self.units(HYDRALISKDEN) \
               + self.units(SPIRE) + self.units(GREATERSPIRE) + self.units(ULTRALISKCAVERN) + self.units(INFESTATIONPIT) \
               + self.units(NYDUSNETWORK) + self.units(BANELINGNEST) + self.units(SPINECRAWLER) + self.units(SPORECRAWLER)

    '''
    From Dentosal's proxyrax build
    Targets a random known enemy unit
    If no known units, targets a random known building
    If no known buildings and units, go towards te first possible enemy start position
    '''
    def select_target(self):
        target = self.known_enemy_structures
        if target.exists:
            return target.random.position

        target = self.known_enemy_units
        if target.exists:
            return target.random.position


        # TODO: Explore other starting positions
        return self.enemy_start_locations[0].position

    @property
    def get_minerals(self):
        """Get the current amount of minerals"""
        return self.minerals

    @property
    def get_vespene(self):
        """Get the current amount of vespene"""
        return self.vespene

    @property
    def get_remaining_supply(self):
        """Get remaining supply"""
        return self.supply_left

    @property
    def get_workers(self):
        """Get the current amount of drones"""
        return self.workers.amount

    @property
    def get_idle_workers(self):
        return self.workers.idle.amount

    @property
    def get_larva_num(self):
        """Get the current amount of larva"""
        return self.units(LARVA).amount

    '''
    Prints to console if self.is_printing_to_console
    Writes to log file if self.is_logging
    '''
    def log(self, data):
        """Log the data to the logfile if this agent is set to log information and logfile is below 1 megabyte"""
        if self.is_logging and os.path.getsize(self.log_file_name) < 1000000:
            self.log_file.write(f"{data}\n")
        if self.is_printing_to_console:
            print(data)

    def log_error(self, data):
        data = f"ERROR: {data}"
        self.log_file.write(f"{data}\n")
        print(data)


def main():
    # Start game with LoserAgent as the Bot, and begin logging
    sc2.run_game(sc2.maps.get("Abyssal Reef LE"), [
        Bot(Race.Zerg, LoserAgent(True, True)),
        Computer(Race.Protoss, Difficulty.Medium)
    ], realtime=False)

if __name__ == '__main__':
    main()
