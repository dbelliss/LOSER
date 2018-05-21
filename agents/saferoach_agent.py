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

    def __init__(self, is_logging = False, isMainAgent = False):
        super().__init__(is_logging, "", isMainAgent)



        # Constants
        self.mainAgent.researched = 2  # If an upgrade has been research
        self.mainAgent.is_researching = 1  # If an upgrade is being researched
        self.mainAgent.not_researched = 0  # If an upgrade is not being researched and has not been researched

        # Number of ground unit types
        self.mainAgent.num_drones = None
        self.mainAgent.num_queens = None  # number of queens
        self.mainAgent.num_zergling = None  # number of zergling
        self.mainAgent.num_banelings = None  # number of banelings
        self.mainAgent.num_roaches = None  # number of roaches
        self.mainAgent.num_hydralisks = None  # number of hydralisks
        self.mainAgent.num_swarm_hosts = None  # number of swarm hosts
        self.mainAgent.num_ravagers = None  # number of ravagers
        self.mainAgent.num_lurkers = None  # number of lurkers
        self.mainAgent.num_infestors = None  # number of infestors
        self.mainAgent.num_ultralisks = None  # number of ultralisks
        self.mainAgent.num_changelings = None  # number of changelings

        # Number of flying unit types
        self.mainAgent.num_overlords = None  # number of overlords
        self.mainAgent.num_overseers = None  # number of overseers
        self.mainAgent.num_mutalisks = None  # number of mutalisks
        self.mainAgent.num_corruptors = None  # number of corruptors
        self.mainAgent.num_brood_lords = None  # number of brood lords
        self.mainAgent.num_vipers = None  # number of vipers

        # Number of BUILT units, different from number of unit types
        self.mainAgent.creeptumors_built = 0  # number of built creep tumors
        self.mainAgent.drones_built = 0  # number of built drones
        self.mainAgent.overlords_built = 0  # number of overlords built
        self.mainAgent.hatcheries_built = 0  # number of hatcheries built

        self.mainAgent.base_build_order_complete = False  # checks if base build order is complete

        # non-standard upgrades purchased
        self.mainAgent.can_burrow = None # true if Burrow has been purchased
        self.mainAgent.zergling_speed = None # True if Metabolic Boost has been purchased
        self.mainAgent.zergling_attack_boost = None  # True if Adrenal glands has been purchased
        self.mainAgent.baneling_speed = None # True if Centrifugal Hooks has been purchased
        self.mainAgent.roach_speed = None  # True if Glial Reconstruction has been purchased
        self.mainAgent.roach_tunnel = None  # True if Tunneling Claws reconstruction has been purchased
        self.mainAgent.overlord_speed = None  # True if Pneumatized Carapace has been purchsed
        self.mainAgent.hydralisk_range = None  # True if Grooved Spines has been purchased
        self.mainAgent.infestor_parasite = None  # True if Neural parasite has been purchased
        self.mainAgent.infestor_energy = None  # True if Pathogen Glands has been purchased
        self.mainAgent.ultralisk_defense = None  # True if Chitinous Plating has been purchased

        # standard upgrades
        # TODO

    async def on_step(self, iteration):
        self.mainAgent.log("Step: %s Idle Workers: %s Overlord: %s" % (str(iteration), str(self.mainAgent.get_idle_workers), str(self.mainAgent.units(OVERLORD).amount)))

        if iteration == 0:
            await self.mainAgent.chat_send("help me im trapped inside a terrible bot")

        # code from zerg_rush example, literally just last resort sends all units to attack if hatchery is destroyed
        if not self.mainAgent.units(HATCHERY).ready.exists:
            for unit in self.mainAgent.workers | self.mainAgent.units(ZERGLING) | self.mainAgent.units(QUEEN):
                await self.mainAgent.do(unit.attack(self.mainAgent.enemy_start_locations[0]))
            return
        else:
            hatchery = self.mainAgent.units(HATCHERY).ready.random

        # ideas: spread creep to block expansions, spread to increase zergling defense, patrol with zerglings, spread
        # with overseer, changelings for vision (most bots/humans don't attack? follow the unit it finds)

        larvae = self.mainAgent.units(LARVA)

        target = self.mainAgent.known_enemy_structures.random_or(self.mainAgent.enemy_start_locations[0]).position

        for idle_worker in self.mainAgent.workers.idle:
            mf = self.mainAgent.state.mineral_field.closest_to(idle_worker)
            await self.mainAgent.do(idle_worker.gather(mf))

        if self.mainAgent.supply_left < 2 and self.mainAgent.base_build_order_complete is True:
            if self.mainAgent.can_afford(OVERLORD) and larvae.exists:
                await self.mainAgent.do(larvae.random.train(OVERLORD))

        if self.mainAgent.base_build_order_complete is True and self.mainAgent.can_afford(HATCHERY):
            self.mainAgent.hatcheries_built += 1
            location = await self.mainAgent.get_next_expansion()
            await self.mainAgent.build(HATCHERY, near=location)

        for queen in self.mainAgent.units(QUEEN).idle:
            abilities = await self.mainAgent.get_available_abilities(queen)
            if AbilityId.BUILD_CREEPTUMOR_QUEEN in abilities and self.mainAgent.creeptumors_built is 0:
                self.mainAgent.creeptumors_built += 1
                await self.mainAgent.do(queen(BUILD_CREEPTUMOR_QUEEN, near=hatchery))
            if AbilityId.EFFECT_INJECTLARVA in abilities:
                await self.mainAgent.do(queen(EFFECT_INJECTLARVA, hatchery))

        # queen sets down one tumor, then tumor self-spreads

        for tumor in self.mainAgent.units(CREEPTUMOR).idle:
            abilities = await self.mainAgent.get_available_abilities(tumor)
            if AbilityId.BUILD_CREEPTUMOR_TUMOR in abilities:
                self.mainAgent.creeptumors_built += 1
                await self.mainAgent.do(tumor(BUILD_CREEPTUMOR_TUMOR, near=tumor))

        # strict build order begins here
        if self.mainAgent.base_build_order_complete is False:
            if self.mainAgent.drones_built == 0 and larvae.exists and self.mainAgent.can_afford(DRONE):
                self.mainAgent.drones_built += 1
                print("1")
                await self.mainAgent.do(larvae.random.train(DRONE))

            if self.mainAgent.overlords_built == 0 and larvae.exists and self.mainAgent.can_afford(OVERLORD):
                self.mainAgent.overlords_built += 1
                print("2")
                await self.mainAgent.do(larvae.random.train(OVERLORD))

            if self.mainAgent.drones_built == 1 and self.mainAgent.overlords_built == 1 and self.mainAgent.already_pending(OVERLORD) and larvae.exists:
                if self.mainAgent.can_afford(DRONE):
                    self.mainAgent.drones_built += 1
                    print("BUILD 3")
                    await self.mainAgent.do(larvae.random.train(DRONE))

            if self.mainAgent.units(OVERLORD).amount == 2 and self.mainAgent.overlords_built is 1 and self.mainAgent.drones_built > 2:

                if self.mainAgent.drones_built == 2 and larvae.exists and self.mainAgent.can_afford(DRONE):
                    self.mainAgent.drones_built += 1
                    print("4")
                    await self.mainAgent.do(larvae.random.train(DRONE))

                if self.mainAgent.drones_built == 3 and larvae.exists and self.mainAgent.can_afford(DRONE):
                    self.mainAgent.drones_built += 1
                    print("5")
                    await self.mainAgent.do(larvae.random.train(DRONE))

                if self.mainAgent.drones_built == 4 and larvae.exists and self.mainAgent.can_afford(DRONE):
                    self.mainAgent.drones_built += 1
                    print("6")
                    await self.mainAgent.do(larvae.random.train(DRONE))

                print("hatcheries built: %s" % (str(self.mainAgent.hatcheries_built)))

                if self.mainAgent.hatcheries_built == 0 and self.mainAgent.can_afford(HATCHERY) and not self.mainAgent.already_pending(HATCHERY):
                    print("entered, hatcheries build: %s" % (str(self.mainAgent.hatcheries_built)))
                    self.mainAgent.hatcheries_built += 1
                    location = await self.mainAgent.get_next_expansion()
                    print("7")
                    await self.mainAgent.build(HATCHERY, near=location)

                if self.mainAgent.drones_built == 5 and self.mainAgent.hatcheries_built is 1 and larvae.exists and self.mainAgent.can_afford(DRONE):

                    print("8")
                    await self.mainAgent.do(larvae.closest_to(self.mainAgent.units(HATCHERY).ready.first).train(DRONE))

        # checks if base build order requirements are done, allows for expansion of hatcheries at-will
        if self.mainAgent.drones_built == 6 and self.mainAgent.hatcheries_built is 1:
            self.mainAgent.base_build_order_complete = True
            print("DONE WITH BASE BUILD ORDER")


def main():
    # Start game as SafeRoach as the Bot, and begin logging
    sc2.run_game(sc2.maps.get("Abyssal Reef LE"), [
        Bot(Race.Zerg, SafeRoachAgent(True, True)),
        Computer(Race.Protoss, Difficulty.VeryHard)
    ], realtime=True)

if __name__ == '__main__':
    main()
