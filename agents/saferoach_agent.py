# https://chatbotslife.com/building-a-basic-pysc2-agent-b109cde1477c
import sc2
from sc2 import Race, Difficulty
from sc2.constants import *
from sc2.player import Bot, Computer

from math import pi

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
        self.num_brood_lords = None  # number of brood lords
        self.num_vipers = None  # number of vipers

        # Number of BUILT units, different from number of unit types
        self.creeptumors_built = 0  # number of built creep tumors
        self.creeptumors_built_queen = 0  # number of seed creep tumors built by queens
        self.drones_built = 0  # number of built drones
        self.overlords_built = 0  # number of overlords built
        self.hatcheries_built = 0  # number of hatcheries built
        self.rebuild_viable_tumor = 0  # number of viable tumors rebuilt

        # checks for true/false
        self.base_build_order_complete = False  # checks if base build order is complete
        self.viable_tumor = True  # checks if there's a tumor that can spawn other tumors

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
        self.built_gas1 = False
        self.moved_workers_to_gas1 = False # whether workers are assigned to the first vespene geyser
        self.built_sp = False # whether a spawning pool was built

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
        # add checker for buildings, if any are missing (spawning pool, warren, etc, (re)build them)

        larvae = self.units(LARVA)

        target = self.known_enemy_structures.random_or(self.enemy_start_locations[0]).position

        for idle_worker in self.workers.idle:
            mf = self.state.mineral_field.closest_to(idle_worker)
            await self.do(idle_worker.gather(mf))

        for extractor in self.units(EXTRACTOR):
            if extractor.assigned_harvesters < extractor.ideal_harvesters:
                print("finding extractor worker")
                await self.do(self.workers.random.gather(extractor))

        if self.supply_left < 4 and self.base_build_order_complete is True:
            if self.can_afford(OVERLORD) and larvae.exists:
                await self.do(larvae.random.train(OVERLORD))

        if self.base_build_order_complete is True and self.minerals > 600 and not self.already_pending(HATCHERY):
            self.hatcheries_built += 1
            location = await self.get_next_expansion()
            await self.build(HATCHERY, near=location)

        for queen in self.units(QUEEN).idle:
            abilities = await self.get_available_abilities(queen)
            # makes 4 starting tumors by default
            if AbilityId.BUILD_CREEPTUMOR_QUEEN in abilities and self.creeptumors_built_queen < 4:
                # while True:
                #     print("trying to build creep tumor")
                    # err2 = await self.build(CREEPTUMOR, near=self.units(HATCHERY).first, max_distance=20, unit=queen)
                    # if not err2:
                    #     print("First tumor built")
                    #     self.creeptumors_built += 1
                    #     break

                for d in range(1, 10):
                    print("searching for a spot for tumor")
                    pos = queen.position.to2.towards(self.game_info.map_center, d)
                    if self.can_place(CREEPTUMOR, pos):
                        err = await self.do(queen(BUILD_CREEPTUMOR_QUEEN, pos))
                        if not err:
                            print("First tumors built")
                            self.creeptumors_built_queen += 1
                            break

            # recreates tumors when the number of tumors drops too low
            elif AbilityId.BUILD_CREEPTUMOR_QUEEN in abilities and self.viable_tumor is False and \
                    self.creeptumors_built_queen >= 4 and self.rebuild_viable_tumor < 4 and\
                    not self.already_pending(CREEPTUMOR):
                print("going into backup because only", self.units(CREEPTUMOR).ready.amount, "tumors are left ready")
                for d in range(1, 10):
                    print("searching for a spot for tumor backup")
                    pos = queen.position.to2.towards(self.game_info.map_center, d)
                    # if await self.can_place(CREEPTUMOR, pos):
                    if self.can_place(CREEPTUMOR, pos):
                        err = await self.do(queen(BUILD_CREEPTUMOR_QUEEN, pos))
                        if not err:
                            print("Backup tumors built")
                            self.creeptumors_built_queen += 1
                            self.rebuild_viable_tumor += 1
                            break

            elif AbilityId.EFFECT_INJECTLARVA in abilities:
                injection_target = self.units(HATCHERY).ready.closest_to(queen.position)
                await self.do(queen(EFFECT_INJECTLARVA, injection_target))

        # sets viable_tumor to false so that if one is found, it's set to true for the next iteration through the above
        self.viable_tumor = False

        # queen sets down one tumor, then tumor self-spreads
        for tumor in self.units(CREEPTUMORBURROWED).ready:
            abilities = await self.get_available_abilities(tumor)
            if AbilityId.BUILD_CREEPTUMOR_TUMOR in abilities:
                self.viable_tumor = True
                for d in range(5, 10):
                    pos = tumor.position.towards_with_random_angle(target, d, max_difference=pi/2)
                    if self.can_place(CREEPTUMOR, pos):
                        err = await self.do(tumor(BUILD_CREEPTUMOR_TUMOR, pos))
                        if err:
                            print("didn't build tumor2")
                        else:
                            self.creeptumors_built += 1
                        # print("built tumor2")

        # resets viable_tumor here so that if four have been built but they all die, more gets rebuilt
        if self.rebuild_viable_tumor >= 4:
            self.rebuild_viable_tumor = 0

        # strict build order begins here
        if self.base_build_order_complete is False:
            if self.drones_built == 0 and larvae.exists and self.can_afford(DRONE):
                self.drones_built += 1
                print("1")
                await self.do(larvae.random.train(DRONE))

            if self.overlords_built == 0 and larvae.exists and self.can_afford(OVERLORD):
                self.overlords_built += 1
                print("2")
                await self.do(larvae.random.train(OVERLORD))

            if self.drones_built == 1 and self.overlords_built == 1 and self.already_pending(OVERLORD) and larvae.exists:
                if self.can_afford(DRONE):
                    self.drones_built += 1
                    print("BUILD 3")
                    await self.do(larvae.random.train(DRONE))

            if self.units(OVERLORD).amount == 2 and self.overlords_built == 1 and self.drones_built >= 2:

                if self.drones_built == 2 and larvae.exists and self.can_afford(DRONE):
                    self.drones_built += 1
                    print("4")
                    await self.do(larvae.random.train(DRONE))

                if self.drones_built == 3 and larvae.exists and self.can_afford(DRONE):
                    self.drones_built += 1
                    print("5")
                    await self.do(larvae.random.train(DRONE))

                if self.drones_built == 4 and larvae.exists and self.can_afford(DRONE):
                    self.drones_built += 1
                    print("6")
                    await self.do(larvae.random.train(DRONE))

                if self.hatcheries_built == 0 and self.can_afford(HATCHERY) and not self.already_pending(HATCHERY):
                    print("entered, hatcheries build: %s" % (str(self.hatcheries_built)))
                    self.hatcheries_built += 1
                    location = await self.get_next_expansion()
                    print("7")
                    await self.build(HATCHERY, near=location)

                # experimental non-working pre-move worker for hatchery code, likely not worth pursuing

                # if self.hatcheries_built == 0 and self.minerals > 200 and not self.already_pending(HATCHERY):
                #     print("entered, hatcheries built: %s" % (str(self.hatcheries_built)))
                #     location = await self.get_next_expansion()
                #     print("7")
                #     await self.do(self.workers.random.move(location))
                #
                # if self.hatcheries_built == 0 and self.can_afford(HATCHERY) and not self.already_pending(HATCHERY):
                #     print("entered, hatcheries built2: %s" % (str(self.hatcheries_built)))
                #     self.hatcheries_built += 1
                #     await self.select_build_worker(location).build(HATCHERY)

                if self.drones_built == 5 and self.hatcheries_built == 1 and larvae.exists and self.can_afford(DRONE):
                    self.drones_built += 1
                    print("8")
                    await self.do(larvae.closest_to(self.units(HATCHERY).ready.first).train(DRONE))

                if self.drones_built == 6 and self.hatcheries_built == 1 and larvae.exists and self.can_afford(DRONE):
                    self.drones_built += 1
                    print("9")
                    await self.do(larvae.closest_to(self.units(HATCHERY).ready.first).train(DRONE))

                if self.drones_built == 7 and self.can_afford(EXTRACTOR) and self.built_gas1 is False:
                    print("Entered gas build")
                    drone = self.workers.closest_to(self.units(HATCHERY).ready.first)
                    target = self.state.vespene_geyser.closest_to(self.units(HATCHERY).ready.first)
                    err = await self.do(drone.build(EXTRACTOR, target))
                    if not err:
                        self.built_gas1 = True

                # if self.units(EXTRACTOR).ready.exists and not self.moved_workers_to_gas1:
                #     self.moved_workers_to_gas1 = True
                #     extractor1 = self.units(EXTRACTOR).first
                #     for num in range(0,3):
                #         print("Moved workers to gas")
                #         await self.do(self.workers.closest_to(extractor1).gather(extractor1))

                if self.drones_built == 7 and self.can_afford(SPAWNINGPOOL) and self.built_gas1 is True and self.built_sp is False:
                    for d in range(4, 15):
                        print("searching for a spot for sp")
                        extractor1 = self.units(EXTRACTOR).first  # builds closer to extractor, toward center
                        pos = extractor1.position.to2.towards(self.game_info.map_center, d)
                        if await self.can_place(SPAWNINGPOOL, pos):
                            drone = self.workers.closest_to(self.units(HATCHERY).ready.first)
                            err = await self.do(drone.build(SPAWNINGPOOL, pos))
                            if not err:
                                self.built_sp = True
                                break

                if self.drones_built == 7 and self.built_sp is True and self.can_afford(DRONE) and larvae.exists:
                    self.drones_built += 1
                    print("10")
                    await self.do(larvae.closest_to(self.units(HATCHERY).ready.first).train(DRONE))

                if self.drones_built == 8 and self.built_sp is True and self.can_afford(DRONE) and larvae.exists:
                    self.drones_built += 1
                    print("11")
                    await self.do(larvae.closest_to(self.units(HATCHERY).ready.first).train(DRONE))

                if self.drones_built == 9 and self.built_sp is True and self.can_afford(DRONE) and larvae.exists:
                    self.drones_built += 1
                    print("12")
                    await self.do(larvae.closest_to(self.units(HATCHERY).ready.first).train(DRONE))

                if larvae.exists and self.can_afford(OVERLORD) and self.drones_built == 10:
                    self.overlords_built += 1
                    print("13")
                    await self.do(larvae.closest_to(self.units(HATCHERY).ready.first).train(OVERLORD))

            # 2nd hatchery should be finished now, simultaneously builds queens when 1st expansion is done at both hatcheries
            if self.units(SPAWNINGPOOL).ready.exists:
                if self.drones_built == 10 and self.units(HATCHERY).ready.amount == 2 and self.minerals >= 300 and self.num_queens_built == 0:
                    noqueue = 0
                    for hatchery in self.units(HATCHERY):
                        if noqueue == 2:
                            break
                        if hatchery.noqueue:
                            print("built queen")
                            self.num_queens_built += 1
                            noqueue += 1
                            await self.do(hatchery.train(QUEEN))

        # checks if base build order requirements are done, allows for expansion of hatcheries at-will
        if self.drones_built == 7 and self.moved_workers_to_gas1 is True and self.built_sp is True and self.base_build_order_complete is False:
            self.base_build_order_complete = True
            print("DONE WITH BASE BUILD ORDER")


def main():
    # Start game as SafeRoach as the Bot, and begin logging
    sc2.run_game(sc2.maps.get("Abyssal Reef LE"), [
        Bot(Race.Zerg, SafeRoachAgent(True)),
        Computer(Race.Protoss, Difficulty.VeryHard)
    ], realtime=False)


if __name__ == '__main__':
    main()
