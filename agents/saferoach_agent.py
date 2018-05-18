# https://chatbotslife.com/building-a-basic-pysc2-agent-b109cde1477c
import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer

from pprint import pprint
from time import gmtime, strftime, localtime
import os

from loser_agent import *

import time

class SafeRoachAgent(LoserAgent):
    base_top_left = None
    overlord_built = False
    larva_selected = False
    drone_selected = False
    spawning_pool_built = False
    spawning_pool_selected = False
    spawning_pool_rallied = False
    army_selected = False
    army_rallied = False

    def __init__(self, is_logging = False):
        super().__init__()

        # For debugging
        self.is_logging = is_logging
        if self.is_logging:

            # Make logs directory if it doesn't exist
            if not os.path.exists("./logs"):
                os.mkdir("./logs")
            self.log_file_name = "./logs/" + strftime("%Y-%m-%d %H:%M:%S", localtime()) + ".log"
            self.log_file = open(self.log_file_name, "w+")  # Create log file based on the time


        # Constants
        self.researched = 2  # If an upgrade has been research
        self.is_researching = 1  # If an upgrade is being researched
        self.not_researched = 0  # If an upgrade is not being researched and has not been researched

        # Number of ground unit types
        self.num_drones = None
        self.num_queens = None  # number of queens
        self.num_zergling = None  # number of zergling
        self.num_banelings = None  # number of banelings
        self.num_roaches = None  # number of roaches
        self.num_hydralisks = None  # number of hydralisks
        self.num_swarm_hosts = None  # number of swarm hosts
        self.num_ravagers = None  # number of ravagers
        self.num_lurkers = None  # number of lurkers
        self.num_infestors = None  # number of infestors
        self.num_ultralisks = None  # number of ultralisks
        self.num_changelings = None  # number of changelings

        # Number of flying unit types
        self.num_overlords = None  # number of overlords
        self.num_overseers = None  # number of overseers
        self.num_mutalisks = None  # number of mutalisks
        self.num_corruptors = None  # number of corruptors
        self.num_brood_lords = None # number of brood lords
        self.num_vipers = None  # number of vipers

        # Number of BUILT units, different from number of unit types
        self.creeptumors_built = 0 # number of built creep tumors
        self.drones_built = 0 # number of built drones
        self.overlords_built = 0 # number of overlords built
        self.hatcheries_built = 0 # number of hatcheries built

        self.base_build_order_complete = False

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

        # standard upgrades
        # TODO

    async def on_step(self, iteration):
        self.log("Step: %s Idle Workers: %s Overlord: %s" % (str(iteration), str(self.get_idle_workers), str(self.units(OVERLORD).amount)))

        if iteration == 0:
            await self.chat_send("help me im trapped inside a terrible bot")

        # code from zerg_rush example, literally just last resort sends all units to attack if hatchery is destroyed
        if not self.units(HATCHERY).ready.exists:
            for unit in self.workers | self.units(ZERGLING) | self.units(QUEEN):
                await self.do(unit.attack(self.enemy_start_locations[0]))
            return
        else:
            hatchery = self.units(HATCHERY).ready.random

        # ideas: spread creep to block expansions, spread to increase zergling defense, patrol with zerglings, spread
        # with overseer, changelings for vision (most bots/humans don't attack? follow the unit it finds)

        larvae = self.units(LARVA)

        target = self.known_enemy_structures.random_or(self.enemy_start_locations[0]).position


        for idle_worker in self.workers.idle:
            mf = self.state.mineral_field.closest_to(idle_worker)
            await self.do(idle_worker.gather(mf))

        if self.supply_left < 2 and self.base_build_order_complete is True:
            if self.can_afford(OVERLORD) and larvae.exists:
                await self.do(larvae.random.train(OVERLORD))

        if self.base_build_order_complete is True and self.can_afford(HATCHERY):
            self.hatcheries_built += 1
            location = await self.get_next_expansion()
            await self.build(HATCHERY, near=location)


        for queen in self.units(QUEEN).idle:
            abilities = await self.get_available_abilities(queen)
            if AbilityId.BUILD_CREEPTUMOR_QUEEN in abilities and self.creeptumors_built is 0:
                self.creeptumors_built += 1
                await self.do(queen(BUILD_CREEPTUMOR_QUEEN, near=hatchery))
            if AbilityId.EFFECT_INJECTLARVA in abilities:
                await self.do(queen(EFFECT_INJECTLARVA, hatchery))

        # queen sets down one tumor, then tumor self-spreads

        for tumor in self.units(CREEPTUMOR).idle:
            abilities = await self.get_available_abilities(tumor)
            if AbilityId.BUILD_CREEPTUMOR_TUMOR in abilities:
                self.creeptumors_built += 1
                await self.do(tumor(BUILD_CREEPTUMOR_TUMOR, near=tumor))

        # strict build order begins here
        if self.drones_built is 0 and larvae.exists and self.can_afford(DRONE):
            self.drones_built += 1
            await self.do(larvae.random.train(DRONE))

        if self.overlords_built is 0 and larvae.exists and self.can_afford(OVERLORD):
            self.overlords_built += 1
            await self.do(larvae.random.train(OVERLORD))

        if self.drones_built is 1 and larvae.exists and self.can_afford(DRONE):
            self.drones_built += 1
            await self.do(larvae.random.train(DRONE))

        if self.drones_built is 2 and larvae.exists and self.can_afford(DRONE):
            self.drones_built += 1
            await self.do(larvae.random.train(DRONE))

        if self.drones_built is 3 and larvae.exists and self.can_afford(DRONE):
            self.drones_built += 1
            await self.do(larvae.random.train(DRONE))

        if self.drones_built is 4 and larvae.exists and self.can_afford(DRONE):
            self.drones_built += 1
            await self.do(larvae.random.train(DRONE))

        if self.hatcheries_built is 0 and self.can_afford(HATCHERY):
            self.hatcheries_built += 1
            location = await self.get_next_expansion()
            await self.build(HATCHERY, near=location)

        if self.drones_built is 5 and larvae.exists and self.can_afford(DRONE):
            await self.do(larvae.closest_to(self.units(HATCHERY).ready.first).train(DRONE))

        # checks if base build order requirements are done, allows for expansion of hatcheries at-will
        if self.drones_built is 6 and self.hatcheries_built is 1:
            self.base_build_order_complete = True


def main():
    # Start game as SafeRoach as the Bot, and begin logging
    sc2.run_game(sc2.maps.get("Abyssal Reef LE"), [
        Bot(Race.Zerg, SafeRoachAgent(True)),
        Computer(Race.Protoss, Difficulty.VeryHard)
    ], realtime=False)

if __name__ == '__main__':
    main()
