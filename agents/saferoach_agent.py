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

import random

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

    def __init__(self, is_logging=False, is_printing_to_console=False, isMainAgent=False, fileName=""):
        super().__init__()

        # For debugging
        self.is_logging = is_logging  # Setting this to true to write information to log files in the agents/logs directory
        self.is_printing_to_console = is_printing_to_console  # Setting this to true causes all logs to be printed to the console

        # Make logs directory if it doesn't exist
        if not os.path.exists("./logs"):
            os.mkdir("./logs")
        self.log_file_name = "./logs/" + fileName + strftime("%Y-%m-%d %H%M%S", localtime()) + ".log"
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
        self.zerglings_built = 0  # number of zerglings built
        self.queens_built = 0  # number of queens built
        self.sporecrawlers_built = 0  # number of spore crawlers built
        self.spinecrawlers_built = 0  # number of spine crawlers built
        self.drone_gapnum = 0  # gap in missing drones
        self.drone_gapnumcounter = 0  # counter for replenishing drones
        self.done_gap_closing = False  # closed gap boolean
        self.roaches_built = 0  # Number of roaches built
        self.hydralisks_built = 0  # Number of hydralisks built
        self.extractors_built = 0  # number of extractors built

        self.queen_gapnum = 0  # gap in missing queens
        self.queen_gapnumcounter = 0  # counter for replenishing queens

        # checks for true/false
        self.base_build_order_complete = False  # checks if base build order is complete
        self.viable_tumor = True  # checks if there's a tumor that can spawn other tumors

        # non-standard upgrades purchased
        self.can_burrow = None  # true if Burrow has been purchased
        self.zergling_speed = None  # True if Metabolic Boost has been purchased
        self.zergling_attack_boost = None  # True if Adrenal glands has been purchased
        self.baneling_speed = None  # True if Centrifugal Hooks has been purchased
        self.roach_speed = None  # True if Glial Reconstruction has been purchased
        self.roach_tunnel = None  # True if Tunneling Claws reconstruction has been purchased
        self.overlord_speed = None  # True if Pneumatized Carapace has been purchsed
        self.hydralisk_range = None  # True if Grooved Spines has been purchased
        self.infestor_parasite = None  # True if Neural parasite has been purchased
        self.infestor_energy = None  # True if Pathogen Glands has been purchased
        self.ultralisk_defense = None  # True if Chitinous Plating has been purchased

        # standard upgrades
        self.built_gas1 = False
        self.moved_workers_to_gas1 = False  # whether workers are assigned to the first vespene geyser
        self.built_sp = False  # whether a spawning pool was built
        self.research_zmb = False  # whether RESEARCH_ZERGLINGMETABOLICBOOST was performed
        self.built_rwarren = False  # whether the roach warren was built
        self.built_lair = False  # True if one Lair has been upgraded
        self.built_gr = False  # True if glial reconstitution has been built
        self.built_hd = False  # True if hydralisk den has been built
        self.built_gs = False  # True if grooved spines are researched
        self.built_ec = False  # True if evolution chamber is built
        self.built_ga1 = False  # True if ground armor 1 built
        self.built_mw1 = False  # True if missile weapon 1 built

        self.OG_hatchery = 0
        # Units actively being used for things, gets set to null on strategy change
        self.strike_force = None

        # Previous strategy so you now when the strategy changes
        self.prev_strategy = None

        # True if strategy just changed in this iteration
        self.did_strategy_change = False

        # Way point for units to move to
        self.waypoint = None

        # Predict enemy will be in the first possible position
        self.predicted_enemy_position_num = -1

        # Position to search for enemy untis
        self.num_enemy_positions = -1

        # Position the bot begins
        self.start_location = None

        # Easier way to access map information, must be loaded in after game loads
        self.map_height = None
        self.map_width = None
        # SafeRoachAgent.mainAgent = self

    async def on_step(self, iteration, strategy_num=2):
        # self.log("Step: %s Overlord: %s" % (str(iteration), str(self.units(OVERLORD).amount)))
        # self.log("Step: " + str(iteration))

        # TEMP: Until strategy is given by Q table
        # strategy_num = (int)(iteration / 75) % 8

        # Build lings, queen, overlords, drones, and meleeattack1
        await self.basic_build(iteration)

        # Perform actions based on given strategy
        if strategy_num == -1:
            # self.log("No given strategy")
            pass
        else:
            await self.mainAgent.perform_strategy(iteration, strategy_num)

    async def basic_build(self, iteration):

        if iteration == 0:
            self.mainAgent.OG_hatchery = self.mainAgent.units(HATCHERY).first.tag
            # print("TAG IS ", self.mainAgent.OG_hatchery)
            await self.mainAgent.chat_send("help me im trapped inside a terrible bot")

        # if iteration % 100 == 0:
            # print("NUMWORKERS ", self.mainAgent.workers.amount)
            # print("NUMROACHES ", self.mainAgent.units(ROACH).amount)
            # print("NUMHYDRAS", self.mainAgent.units(HYDRALISK).amount)
            # print("NUMCRAWLERS", self.mainAgent.units(SPORECRAWLER).amount + self.mainAgent.units(SPINECRAWLER).amount)

        # code from zerg_rush example, literally just last resort sends all units to attack if hatchery is destroyed
        if not self.mainAgent.units(HATCHERY).ready.exists | self.mainAgent.units(LAIR).ready.exists:
            for unit in self.mainAgent.workers | self.mainAgent.units(ZERGLING) | self.mainAgent.units(
                    ROACH) | self.mainAgent.units(QUEEN):
                await self.mainAgent.do(unit.attack(self.mainAgent.enemy_start_locations[0]))
            return
        else:
            hatchpool = self.mainAgent.units.filter(
                lambda x: x.name == "Hatchery" or x.name == "Lair" or x.name == "Hive")
            hatchery = hatchpool.ready.random

        # ideas: spread creep to block expansions, spread to increase zergling defense, patrol with zerglings, spread
        # with overseer, changelings for vision (most bots/humans don't attack? follow the unit it finds)
        # add checker for buildings, if any are missing (spawning pool, warren, etc, (re)build them)

        larvae = self.mainAgent.units(LARVA)

        target = self.mainAgent.known_enemy_structures.random_or(self.mainAgent.enemy_start_locations[0]).position

        await self.mainAgent.distribute_workers()

        # # auto-assigns workers to mineral fields
        #
        # for idle_worker in self.mainAgent.workers.idle:
        #     mf = self.mainAgent.state.mineral_field.closest_to(idle_worker)
        #     await self.mainAgent.do(idle_worker.gather(mf))
        #
        # auto-assigns workers to geysers
        if self.mainAgent.vespene < 500:
            for extractor in self.mainAgent.units(EXTRACTOR):
                if extractor.assigned_harvesters < extractor.ideal_harvesters:
                    # print("finding extractor worker")
                    if self.mainAgent.workers.exists:
                        await self.mainAgent.do(self.mainAgent.workers.random.gather(extractor))

        # actions to take only if build order is complete

        if self.mainAgent.base_build_order_complete is True:

            # add grooved spines, evo chamber, zerg misile weapons, just alter if statement for roaches,
            # biggest mineral consumer

            if self.mainAgent.can_afford(EVOLUTIONCHAMBER) and \
                    self.mainAgent.units(LAIR).ready.exists and not self.mainAgent.already_pending(EVOLUTIONCHAMBER) \
                    and not self.mainAgent.units(EVOLUTIONCHAMBER).ready.exists:
                for d in range(4, 15):
                    if self.mainAgent.can_afford(EVOLUTIONCHAMBER) and not self.mainAgent.already_pending(
                            EVOLUTIONCHAMBER):
                        err = await self.mainAgent.build(EVOLUTIONCHAMBER, near=self.mainAgent.units(LAIR).find_by_tag(
                            self.mainAgent.OG_hatchery).position.to2.towards(self.mainAgent.game_info.map_center, d))
                        if not err:
                            # print("EVOLUTIONCHAMBER BUILT")
                            self.mainAgent.built_ec = True

            # builds glial reconstitution upgrade

            if self.mainAgent.units(
                    ROACHWARREN).ready.exists and self.mainAgent.built_gr is False and self.mainAgent.can_afford(
                    RESEARCH_GLIALREGENERATION) and self.mainAgent.units(LAIR).ready.exists:
                err = await self.mainAgent.do(self.mainAgent.units(ROACHWARREN).random(RESEARCH_GLIALREGENERATION))
                if not err:
                    # print("BUILT GLIALRECONSTITUTION")
                    self.mainAgent.built_gr = True

            # adds a hydralisk den after checking if lair and roach warren exists, then if no hydralisk den exists
            # prefers to build the den toward the center of the map from the lair's position

            if not self.mainAgent.units(HYDRALISKDEN).ready.exists and not self.mainAgent.already_pending(HYDRALISKDEN) \
                    and self.mainAgent.units(LAIR).ready.exists and self.mainAgent.units(
                ROACHWARREN).ready.exists and self.mainAgent.supply_used > 50:
                # print("ATTEMPTING TO BUILD HYDRALISK DEN")
                if self.mainAgent.can_afford(HYDRALISKDEN):
                    for d in range(4, 25):
                        if self.mainAgent.can_afford(HYDRALISKDEN):
                            err = await self.mainAgent.build(HYDRALISKDEN, near=self.mainAgent.units(
                                ROACHWARREN).ready.first.position.to2.towards(self.mainAgent.game_info.map_center, d))
                            if not err:
                                # print("SUCCESSFULLY BUILT HYDRALISK DEN")
                                self.mainAgent.built_hd = True

            if self.mainAgent.units(HYDRALISKDEN).ready.exists:
                if self.mainAgent.can_afford(RESEARCH_MUSCULARAUGMENTS) and self.mainAgent.built_gs is False:
                    # print("RESEARCH_MUSCULARAUGMENTS")
                    err = await self.mainAgent.do(
                        self.mainAgent.units(HYDRALISKDEN).ready.first(RESEARCH_MUSCULARAUGMENTS))
                    if not err:
                        # print("RESEARCH_MUSCULARAUGMENTS PERFORMED")
                        self.mainAgent.built_gs = True

            if self.mainAgent.units(EVOLUTIONCHAMBER).ready.exists:
                if self.mainAgent.can_afford(RESEARCH_ZERGGROUNDARMORLEVEL1) and self.mainAgent.built_ga1 is False:
                    # print("ATTEMPTING RESEARCH_ZERGGROUNDARMORLEVEL1")
                    err = await self.mainAgent.do(
                        self.mainAgent.units(EVOLUTIONCHAMBER).ready.first(RESEARCH_ZERGGROUNDARMORLEVEL1))
                    if not err:
                        # print("RESEARCH_ZERGGROUNDARMORLEVEL1 PERFORMED")
                        self.mainAgent.built_ga1 = True
                if self.mainAgent.can_afford(RESEARCH_ZERGMISSILEWEAPONSLEVEL1) and self.mainAgent.built_mw1 is False:
                    # print("ATTEMPTING RESEARCH_ZERGMISSILEWEAPONSLEVEL1")
                    err = await self.mainAgent.do(
                        self.mainAgent.units(EVOLUTIONCHAMBER).ready.first(RESEARCH_ZERGMISSILEWEAPONSLEVEL1))
                    if not err:
                        # print("RESEARCH_ZERGMISSILEWEAPONSLEVEL1 PERFORMED")
                        self.mainAgent.built_mw1 = True

            if larvae.amount > hatchpool.ready.amount * 3 and self.mainAgent.minerals > 700 and self.mainAgent.supply_left > 2:
                if self.mainAgent.can_afford(ROACH):
                    # print("MAKING SURPLUS LARVAE ROACH")
                    await self.mainAgent.do(larvae.random.train(ROACH))

            # siphons off excess workers, helps distribute workers too in the late game
            if self.mainAgent.minerals > 800 and (
                    self.mainAgent.workers.amount > hatchpool.ready.amount * 16 or self.mainAgent.workers.amount > 75):
                cointoss = random.randint(1, 4)
                # print("BUILDING EXCESS SPORE/SPINECRAWLER")
                if self.mainAgent.can_afford(SPORECRAWLER) and self.mainAgent.can_afford(SPINECRAWLER):
                    if cointoss == 1:
                        await self.mainAgent.build(SPORECRAWLER, near=hatchery)
                    if cointoss >= 2:
                        await self.mainAgent.build(SPINECRAWLER, near=hatchery)

            # autobuilds extractors for hatcheries lacking them when there are enough minerals
            # if self.mainAgent.minerals > 500 and (self.mainAgent.extractors_built < self.mainAgent.hatcheries_built*2
            #  or self.mainAgent.extractors_built > self.mainAgent.units(EXTRACTOR).amount):

            if (self.mainAgent.minerals > 500 and (
                    self.mainAgent.extractors_built < self.mainAgent.hatcheries_built * 2 or
                    self.mainAgent.extractors_built > self.mainAgent.units(EXTRACTOR).amount)) or \
                    (self.mainAgent.minerals > 50 and self.mainAgent.extractors_built < 3) \
                    and not self.mainAgent.already_pending(EXTRACTOR) and self.mainAgent.vespene < 500:
                # print("Entered postbuild gas build with", self.mainAgent.extractors_built, " extractors built and ",
                      #self.mainAgent.units(EXTRACTOR).amount, "extractors existing")
                targets = self.mainAgent.state.vespene_geyser.closer_than(20.0, hatchery)
                for vg in targets:
                    drone = self.mainAgent.select_build_worker(vg.position)
                    if drone is None:
                        break

                    if not self.mainAgent.units(EXTRACTOR).closer_than(1.0, vg).exists:
                        if self.mainAgent.can_afford(EXTRACTOR):
                            err = await self.mainAgent.do(drone.build(EXTRACTOR, vg))
                            if not err:
                                # print("BUILT POSTBUILD EXTRACTOR")
                                self.mainAgent.extractors_built += 1

            if self.mainAgent.supply_left < 6 and self.mainAgent.already_pending(
                    OVERLORD) < 3 and self.mainAgent.supply_cap < 200:
                if self.mainAgent.can_afford(OVERLORD) and larvae.exists:
                    await self.mainAgent.do(larvae.random.train(OVERLORD))

            if self.mainAgent.minerals > 600 and not self.mainAgent.already_pending(HATCHERY) and self.mainAgent.units(
                    HATCHERY).amount + self.mainAgent.already_pending(HATCHERY) < 5:
                self.mainAgent.hatcheries_built += 1
                location = await self.mainAgent.get_next_expansion()
                await self.mainAgent.build(HATCHERY, near=location)

            if self.mainAgent.can_afford(HATCHERY) and hatchpool.ready.amount < 3:
                self.mainAgent.hatcheries_built += 1
                location = await self.mainAgent.get_next_expansion()
                await self.mainAgent.build(HATCHERY, near=location)

            # drone replenishing code
            # takes into account the number of drones missing because .amount doesn't count in-progress units
            # builds drones until the counter hits the same number as the calculated gap in unit number
            # should work if units die because it recalculates and only resets when the .amount == desired # of workers

            if self.mainAgent.supply_used < 60 or self.mainAgent.built_hd is True and (
                    hatchpool.ready.amount >= 3 or self.mainAgent.workers.amount + self.mainAgent.already_pending(
                    DRONE)) < (hatchpool.ready.amount * 16):

                if (self.mainAgent.workers.amount + self.mainAgent.already_pending(DRONE)) < (
                        hatchpool.ready.amount * 16) and \
                        (self.mainAgent.workers.amount + self.mainAgent.already_pending(DRONE)) < 75:
                    if self.mainAgent.can_afford(DRONE) and larvae.exists and self.mainAgent.supply_left > 0:
                        # print("TRAINING DRONE NUMBER ", self.mainAgent.workers.amount)
                        self.mainAgent.drones_built += 1
                        # print("TRAINING DRONE NUMBER ", self.mainAgent.drones_built)
                        await self.mainAgent.do(larvae.random.train(DRONE))
                        # below is deprecated drone replenishing code
                    # self.mainAgent.drone_gapnum = (self.mainAgent.units(HATCHERY).ready.amount * 16) -
                    #  (self.mainAgent.workers.amount + self.mainAgent.already_pending(DRONE))
                    # if self.mainAgent.can_afford(DRONE) and larvae.exists and self.mainAgent.drone_gapnumcounter <
                    # self.mainAgent.drone_gapnum \
                    #         and self.mainAgent.supply_left >= 1 and not self.mainAgent.done_gap_closing:
                    #     self.mainAgent.drones_built += 1
                    #     self.mainAgent.drone_gapnumcounter += 1
                    #     # print("Replenished missing/dead drone ", self.mainAgent.drones_built)
                    #     await self.mainAgent.do(larvae.random.train(DRONE))
                    # elif self.mainAgent.drone_gapnumcounter >= self.mainAgent.drone_gapnum:
                    #     # experimental to see which works vs queen which seems to work
                    #     # the issue is that drones be destroyed mid-build, maybe wait (# of steps * number building)
                    #     # and check again? maybe check if eggs were destroyed?
                    #     self.mainAgent.done_gap_closing = True
                    #     pass
                if (self.mainAgent.workers.amount + self.mainAgent.already_pending(DRONE)) < (
                        hatchpool.ready.amount * 16) and \
                        (self.mainAgent.workers.amount + self.mainAgent.already_pending(DRONE)) < 75 \
                        and self.mainAgent.units(ROACH).amount + self.mainAgent.units(HYDRALISK).amount > 20:
                    if self.mainAgent.can_afford(DRONE) and larvae.exists and self.mainAgent.supply_left > 0:
                        self.mainAgent.drones_built += 1
                        # print("TRAINING DRONE NUMBER ", self.mainAgent.drones_built)
                        await self.mainAgent.do(larvae.random.train(DRONE))
                # if self.mainAgent.workers.amount >= (self.mainAgent.units(HATCHERY).ready.amount * 16):
                #     self.mainAgent.drone_gapnumcounter = 0
                #     self.mainAgent.done_gap_closing = False

                # queen replenishing code, similar to above drone code

                if self.mainAgent.units(QUEEN).amount + self.mainAgent.already_pending(QUEEN) < 6:
                    self.mainAgent.queen_gapnum = 6 - (
                                self.mainAgent.units(QUEEN).amount + self.mainAgent.already_pending(QUEEN))
                    if self.mainAgent.can_afford(
                            QUEEN) and self.mainAgent.queen_gapnumcounter < self.mainAgent.queen_gapnum and self.mainAgent.supply_left > 4:
                        err = await self.mainAgent.do(hatchery.train(QUEEN))
                        if not err:
                            self.mainAgent.queens_built += 1
                            self.mainAgent.queen_gapnumcounter += 1
                            # print("Replenished missing/dead queen ", self.mainAgent.queens_built)

                    elif self.mainAgent.queen_gapnumcounter >= self.mainAgent.queen_gapnum:
                        pass

                if self.mainAgent.units(QUEEN).amount >= 6:
                    self.mainAgent.queen_gapnumcounter = 0

                if self.mainAgent.can_afford(HYDRALISK) and self.mainAgent.units(
                        HYDRALISK).amount + self.mainAgent.already_pending(HYDRALISK) < 15 and \
                        larvae.exists and self.mainAgent.units(HYDRALISKDEN).ready.exists and \
                        self.mainAgent.supply_left >= 2 and self.mainAgent.units(
                    ROACH).amount + self.mainAgent.already_pending(ROACH) >= 7:
                    # print("MAKING HYDRALISK ", self.mainAgent.hydralisks_built)
                    self.mainAgent.hydralisks_built += 1
                    await self.mainAgent.do(larvae.random.train(HYDRALISK))

                if self.mainAgent.units(HYDRALISKDEN).ready.exists and self.mainAgent.units(
                        ROACH).amount + self.mainAgent.already_pending(ROACH) < 7:
                    if self.mainAgent.can_afford(ROACH) and larvae.exists and self.mainAgent.units(
                            ROACHWARREN).ready.exists and \
                            self.mainAgent.supply_left > 2:
                        # print("MAKING ROACH ", self.mainAgent.roaches_built)
                        self.mainAgent.roaches_built += 1
                        await self.mainAgent.do(larvae.random.train(ROACH))
                elif self.mainAgent.vespene > 150 and self.mainAgent.minerals < 150 and not self.mainAgent.units(
                        HYDRALISKDEN).ready.exists:
                    if self.mainAgent.can_afford(ROACH) and (
                            self.mainAgent.units(ROACH).amount + self.mainAgent.already_pending(ROACH) < 15 or
                            self.mainAgent.workers.amount > 40) and larvae.exists and self.mainAgent.units(
                        ROACHWARREN).ready.exists and \
                            self.mainAgent.supply_left > 2:
                        # print("MAKING ROACH ", self.mainAgent.roaches_built)
                        self.mainAgent.roaches_built += 1
                        await self.mainAgent.do(larvae.random.train(ROACH))

                if self.mainAgent.units(HYDRALISK).amount + self.mainAgent.already_pending(HYDRALISK) >= 15:
                    if self.mainAgent.can_afford(
                            ROACH) and self.mainAgent.workers.amount > 30 and larvae.exists and self.mainAgent.units(
                        ROACHWARREN).ready.exists and \
                            self.mainAgent.supply_left > 2:
                        # print("MAKING ROACH ", self.mainAgent.roaches_built)
                        self.mainAgent.roaches_built += 1
                        await self.mainAgent.do(larvae.random.train(ROACH))

        for queen in self.mainAgent.units(QUEEN).idle:
            abilities = await self.mainAgent.get_available_abilities(queen)
            # makes 4 starting tumors by default
            if AbilityId.BUILD_CREEPTUMOR_QUEEN in abilities and self.mainAgent.creeptumors_built_queen < 4:
                # while True:
                #     # print("trying to build creep tumor")
                # err2 = await self.mainAgent.build(CREEPTUMOR, near=self.mainAgent.units(HATCHERY).first, max_distance=20, unit=queen)
                # if not err2:
                #     # print("First tumor built")
                #     self.mainAgent.creeptumors_built += 1
                #     break

                for d in range(1, 10):
                    # print("searching for a spot for tumor")
                    pos = queen.position.to2.towards(self.mainAgent.game_info.map_center, d)
                    if self.mainAgent.can_place(CREEPTUMOR, pos):
                        err = await self.mainAgent.do(queen(BUILD_CREEPTUMOR_QUEEN, pos))
                        if not err:
                            # print("First tumors built")
                            self.mainAgent.creeptumors_built_queen += 1
                            break

            # recreates tumors when the number of tumors drops too low
            elif self.mainAgent.base_build_order_complete is True and AbilityId.BUILD_CREEPTUMOR_QUEEN in abilities and self.mainAgent.viable_tumor is False and \
                    self.mainAgent.creeptumors_built_queen >= 4 and self.mainAgent.rebuild_viable_tumor < 4 and \
                    not self.mainAgent.already_pending(CREEPTUMOR):
                # print("going into backup because only", self.mainAgent.units(CREEPTUMOR).ready.amount,
                #       "tumors are left ready")
                for d in range(1, 10):
                    # print("searching for a spot for tumor backup")
                    pos = queen.position.to2.towards(self.mainAgent.game_info.map_center, d)
                    # if await self.mainAgent.can_place(CREEPTUMOR, pos):
                    if self.mainAgent.can_place(CREEPTUMOR, pos):
                        err = await self.mainAgent.do(queen(BUILD_CREEPTUMOR_QUEEN, pos))
                        if not err:
                            # print("Backup tumors built")
                            self.mainAgent.creeptumors_built_queen += 1
                            self.mainAgent.rebuild_viable_tumor += 1
                            break

            elif AbilityId.EFFECT_INJECTLARVA in abilities:
                injection_target = hatchpool.ready.closest_to(queen.position)
                await self.mainAgent.do(queen(EFFECT_INJECTLARVA, injection_target))

        # sets viable_tumor to false so that if one is found, it's set to true for the next iteration through the above
        self.mainAgent.viable_tumor = False

        if self.mainAgent.base_build_order_complete:
            # queen sets down one tumor, then tumor self-spreads
            for tumor in self.mainAgent.units(CREEPTUMORBURROWED).ready:
                abilities = await self.mainAgent.get_available_abilities(tumor)
                if AbilityId.BUILD_CREEPTUMOR_TUMOR in abilities:
                    self.mainAgent.viable_tumor = True
                    for d in range(5, 10):
                        pos = tumor.position.towards_with_random_angle(target, d, max_difference=pi / 4)
                        if self.mainAgent.can_place(CREEPTUMOR, pos):
                            err = await self.mainAgent.do(tumor(BUILD_CREEPTUMOR_TUMOR, pos))
                            # if err:
                                # print("didn't build tumor2")
                            if not err:
                                self.mainAgent.creeptumors_built += 1
                            # # print("built tumor2")

        # resets viable_tumor here so that if four have been built but they all die, more gets rebuilt
        if self.mainAgent.rebuild_viable_tumor >= 4:
            self.mainAgent.rebuild_viable_tumor = 0

        # strict build order begins here
        if self.mainAgent.base_build_order_complete is False:
            if self.mainAgent.drones_built == 0 and larvae.exists and self.mainAgent.can_afford(DRONE):
                self.mainAgent.drones_built += 1
                # print("1")
                await self.mainAgent.do(larvae.random.train(DRONE))

            if self.mainAgent.overlords_built == 0 and larvae.exists and self.mainAgent.can_afford(OVERLORD):
                self.mainAgent.overlords_built += 1
                # print("2")
                await self.mainAgent.do(larvae.random.train(OVERLORD))

            if self.mainAgent.drones_built == 1 and self.mainAgent.overlords_built == 1 and self.mainAgent.already_pending(
                    OVERLORD) and larvae.exists:
                if self.mainAgent.can_afford(DRONE):
                    self.mainAgent.drones_built += 1
                    # print("BUILD 3")
                    await self.mainAgent.do(larvae.random.train(DRONE))

            if self.mainAgent.units(
                    OVERLORD).amount == 2 and self.mainAgent.overlords_built == 1 and self.mainAgent.drones_built >= 2:

                if self.mainAgent.drones_built == 2 and larvae.exists and self.mainAgent.can_afford(DRONE):
                    self.mainAgent.drones_built += 1
                    # print("4")
                    await self.mainAgent.do(larvae.random.train(DRONE))

                if self.mainAgent.drones_built == 3 and larvae.exists and self.mainAgent.can_afford(DRONE):
                    self.mainAgent.drones_built += 1
                    # print("5")
                    await self.mainAgent.do(larvae.random.train(DRONE))

                if self.mainAgent.drones_built == 4 and larvae.exists and self.mainAgent.can_afford(DRONE):
                    self.mainAgent.drones_built += 1
                    # print("6")
                    await self.mainAgent.do(larvae.random.train(DRONE))

                if self.mainAgent.hatcheries_built == 0 and self.mainAgent.can_afford(
                        HATCHERY) and not self.mainAgent.already_pending(HATCHERY):
                    # print("entered, hatcheries built: %s" % (str(self.mainAgent.hatcheries_built)))
                    self.mainAgent.hatcheries_built += 1
                    location = await self.mainAgent.get_next_expansion()
                    # print("7")
                    await self.mainAgent.build(HATCHERY, near=location)

                # experimental non-working pre-move worker for hatchery code, likely not worth pursuing

                # if self.mainAgent.hatcheries_built == 0 and self.mainAgent.minerals > 200 and not self.mainAgent.already_pending(HATCHERY):
                #     # print("entered, hatcheries built: %s" % (str(self.mainAgent.hatcheries_built)))
                #     location = await self.mainAgent.get_next_expansion()
                #     # print("7")
                #     await self.mainAgent.do(self.mainAgent.workers.random.move(location))
                #
                # if self.mainAgent.hatcheries_built == 0 and self.mainAgent.can_afford(HATCHERY) and not self.mainAgent.already_pending(HATCHERY):
                #     # print("entered, hatcheries built2: %s" % (str(self.mainAgent.hatcheries_built)))
                #     self.mainAgent.hatcheries_built += 1
                #     await self.mainAgent.select_build_worker(location).build(HATCHERY)

                if self.mainAgent.drones_built == 5 and self.mainAgent.hatcheries_built == 1 and larvae.exists and self.mainAgent.can_afford(
                        DRONE):
                    self.mainAgent.drones_built += 1
                    # print("8")
                    await self.mainAgent.do(larvae.closest_to(self.mainAgent.units(HATCHERY).ready.first).train(DRONE))

                if self.mainAgent.drones_built == 6 and self.mainAgent.hatcheries_built == 1 and larvae.exists and self.mainAgent.can_afford(
                        DRONE):
                    self.mainAgent.drones_built += 1
                    # print("9")
                    await self.mainAgent.do(larvae.closest_to(self.mainAgent.units(HATCHERY).ready.first).train(DRONE))

                if self.mainAgent.drones_built == 7 and self.mainAgent.can_afford(
                        EXTRACTOR) and self.mainAgent.built_gas1 is False:
                    # print("Entered gas build")
                    drone = self.mainAgent.workers.closest_to(self.mainAgent.units(HATCHERY).ready.first)
                    target = self.mainAgent.state.vespene_geyser.closest_to(self.mainAgent.units(HATCHERY).ready.first)
                    err = await self.mainAgent.do(drone.build(EXTRACTOR, target))
                    if not err:
                        self.mainAgent.built_gas1 = True
                        self.mainAgent.extractors_built += 1

                # if self.mainAgent.units(EXTRACTOR).ready.exists and not self.mainAgent.moved_workers_to_gas1:
                #     self.mainAgent.moved_workers_to_gas1 = True
                #     extractor1 = self.mainAgent.units(EXTRACTOR).first
                #     for num in range(0,3):
                #         # print("Moved workers to gas")
                #         await self.mainAgent.do(self.mainAgent.workers.closest_to(extractor1).gather(extractor1))

                if self.mainAgent.drones_built == 7 and self.mainAgent.can_afford(
                        SPAWNINGPOOL) and self.mainAgent.built_gas1 is True and self.mainAgent.built_sp is False:
                    for d in range(4, 15):
                        # print("searching for a spot for sp")
                        extractor1 = self.mainAgent.units(EXTRACTOR).first  # builds closer to extractor, toward center
                        pos = extractor1.position.to2.towards(self.mainAgent.game_info.map_center, d)
                        if await self.mainAgent.can_place(SPAWNINGPOOL, pos):
                            drone = self.mainAgent.workers.closest_to(self.mainAgent.units(HATCHERY).ready.first)
                            err = await self.mainAgent.do(drone.build(SPAWNINGPOOL, pos))
                            if not err:
                                self.mainAgent.built_sp = True
                                break

                if self.mainAgent.drones_built == 7 and self.mainAgent.built_sp is True and self.mainAgent.can_afford(
                        DRONE) and larvae.exists:
                    self.mainAgent.drones_built += 1
                    # print("10")
                    await self.mainAgent.do(larvae.closest_to(self.mainAgent.units(HATCHERY).ready.first).train(DRONE))

                if self.mainAgent.drones_built == 8 and self.mainAgent.built_sp is True and self.mainAgent.can_afford(
                        DRONE) and larvae.exists:
                    self.mainAgent.drones_built += 1
                    # print("11")
                    await self.mainAgent.do(larvae.closest_to(self.mainAgent.units(HATCHERY).ready.first).train(DRONE))

                if self.mainAgent.drones_built == 9 and self.mainAgent.built_sp is True and self.mainAgent.can_afford(
                        DRONE) and larvae.exists:
                    self.mainAgent.drones_built += 1
                    # print("12")
                    await self.mainAgent.do(larvae.closest_to(self.mainAgent.units(HATCHERY).ready.first).train(DRONE))

                if larvae.exists and self.mainAgent.can_afford(OVERLORD) and self.mainAgent.drones_built == 10:
                    self.mainAgent.overlords_built += 1
                    # print("13")
                    await self.mainAgent.do(
                        larvae.closest_to(self.mainAgent.units(HATCHERY).ready.first).train(OVERLORD))

            # 2nd hatchery should be finished now, simultaneously builds queens when 1st expansion is done at both
            # hatcheries
            if self.mainAgent.units(SPAWNINGPOOL).ready.exists:
                if self.mainAgent.drones_built == 10 and self.mainAgent.units(
                        HATCHERY).ready.amount == 2 and self.mainAgent.minerals >= 300 and self.mainAgent.queens_built == 0:
                    noqueue = 0
                    for hatchery in self.mainAgent.units(HATCHERY):
                        if noqueue == 2:
                            break
                        if hatchery.noqueue:
                            # print("built queen")
                            self.mainAgent.queens_built += 1
                            noqueue += 1
                            await self.mainAgent.do(hatchery.train(QUEEN))

            if self.mainAgent.queens_built == 2 and self.mainAgent.can_afford(
                    ZERGLING) and larvae.exists and self.mainAgent.zerglings_built < 4:
                self.mainAgent.zerglings_built += 1
                # print("TRAINING ZERGLING ", self.mainAgent.zerglings_built)
                await self.mainAgent.do(larvae.random.train(ZERGLING))

            if self.mainAgent.zerglings_built == 4 and self.mainAgent.can_afford(
                    RESEARCH_ZERGLINGMETABOLICBOOST) and self.mainAgent.research_zmb is False:
                self.mainAgent.research_zmb = True
                # print("RESEARCH ZMB")
                await self.mainAgent.do(self.mainAgent.units(SPAWNINGPOOL).ready.first(RESEARCH_ZERGLINGMETABOLICBOOST))

            if self.mainAgent.research_zmb is True and self.mainAgent.can_afford(
                    ZERGLING) and larvae.exists and self.mainAgent.zerglings_built < 6:
                self.mainAgent.zerglings_built += 1
                # print("TRAINING ZERGLING ", self.mainAgent.zerglings_built)
                await self.mainAgent.do(larvae.random.train(ZERGLING))

            if self.mainAgent.zerglings_built == 6 and self.mainAgent.can_afford(
                    HATCHERY) and self.mainAgent.hatcheries_built == 1 and not self.mainAgent.already_pending(HATCHERY):
                # print("entered, hatcheries built: %s" % (str(self.mainAgent.hatcheries_built)))
                self.mainAgent.hatcheries_built += 1
                location = await self.mainAgent.get_next_expansion()
                # print("2nd hatchery")
                await self.mainAgent.build(HATCHERY, near=location)

            if self.mainAgent.hatcheries_built == 2 and self.mainAgent.can_afford(
                    OVERLORD) and larvae.exists and self.mainAgent.overlords_built == 2:
                self.mainAgent.overlords_built += 1
                # print("building overlord ", self.mainAgent.overlords_built)
                await self.mainAgent.do(larvae.random.train(OVERLORD))

            if self.mainAgent.overlords_built == 3 and self.mainAgent.can_afford(
                    QUEEN) and self.mainAgent.queens_built == 2:
                noqueue = 0
                for hatchery in self.mainAgent.units(HATCHERY):
                    if noqueue == 1:
                        break
                    else:
                        if self.mainAgent.can_afford(QUEEN):
                            err = await self.mainAgent.do(hatchery.train(QUEEN))
                            if not err:
                                self.mainAgent.queens_built += 1
                                # print("built queen ", self.mainAgent.queens_built)
                                noqueue += 1

            if self.mainAgent.queens_built == 3 and self.mainAgent.can_afford(
                    OVERLORD) and larvae.exists and self.mainAgent.overlords_built < 5:
                self.mainAgent.overlords_built += 1
                # print("building overlord ", self.mainAgent.overlords_built)
                await self.mainAgent.do(larvae.random.train(OVERLORD))

            if self.mainAgent.overlords_built == 5 and self.mainAgent.can_afford(
                    QUEEN) and self.mainAgent.queens_built < 5:
                noqueue = 0
                for hatchery in self.mainAgent.units(HATCHERY):
                    if noqueue == 2:
                        break
                    else:
                        if self.mainAgent.can_afford(QUEEN):
                            err = await self.mainAgent.do(hatchery.train(QUEEN))
                            if not err:
                                self.mainAgent.queens_built += 1
                                # print("built queen ", self.mainAgent.queens_built)
                                noqueue += 1

            if self.mainAgent.queens_built == 5 and self.mainAgent.can_afford(
                    SPORECRAWLER) and self.mainAgent.workers.amount > 5 and self.mainAgent.sporecrawlers_built < 2:
                for hatchery in self.mainAgent.units(HATCHERY).ready:
                    if self.mainAgent.can_afford(SPORECRAWLER):
                        if not self.mainAgent.units(SPORECRAWLER).closer_than(20.0, hatchery).exists:
                            err = await self.mainAgent.build(SPORECRAWLER, near=hatchery)
                            if not err:
                                self.mainAgent.sporecrawlers_built += 1
                                # print("built sporecrawler ", self.mainAgent.sporecrawlers_built)

            if self.mainAgent.sporecrawlers_built >= 2 and self.mainAgent.built_rwarren is False and self.mainAgent.can_afford(
                    ROACHWARREN):
                for d in range(7, 15):
                    if self.mainAgent.can_afford(ROACHWARREN):
                        err = await self.mainAgent.build(ROACHWARREN, near=hatchpool.find_by_tag(
                            self.mainAgent.OG_hatchery).position.to2.towards(self.mainAgent.game_info.map_center, d))
                        # print("ATTEMPTING TO BUILD ROACH WARREN")
                        if not err:
                            self.mainAgent.built_rwarren = True
                            # print("BUILT ROACH WARREN")

            if self.mainAgent.built_rwarren is True:
                for extractor in self.mainAgent.units(EXTRACTOR):
                    if extractor.assigned_harvesters < extractor.ideal_harvesters:
                        # print("finding extractor worker")
                        if self.mainAgent.workers.exists:
                            await self.mainAgent.do(self.mainAgent.workers.random.gather(extractor))

            if self.mainAgent.built_rwarren is True and self.mainAgent.can_afford(UPGRADETOLAIR_LAIR) \
                    and self.mainAgent.built_lair is False and not self.mainAgent.units(LAIR).ready.exists:
                # print("ATTEMPTING TO BUILD LAIR")
                # if lairupgrade is not None:
                #     if self.mainAgent.can_afford(UPGRADETOLAIR_LAIR) and self.mainAgent.minerals > 150:
                if self.mainAgent.can_afford(UPGRADETOLAIR_LAIR):
                    err = await self.mainAgent.do(
                        hatchpool.ready.find_by_tag(self.mainAgent.OG_hatchery)(UPGRADETOLAIR_LAIR))
                    if not err:
                        # print("SUCCESSFUL LAIR UPGRADE")
                        self.mainAgent.built_lair = True

            if self.mainAgent.built_lair is True and self.mainAgent.roaches_built < 7 and self.mainAgent.can_afford(
                    ROACH):
                err = await self.mainAgent.do(larvae.random.train(ROACH))
                if not err:
                    self.mainAgent.roaches_built += 1
                    # print("BUILTROACH ", self.mainAgent.roaches_built)

            if not self.mainAgent.units(LAIR).ready.exists and self.mainAgent.built_rwarren is True:
                if self.mainAgent.can_afford(UPGRADETOLAIR_LAIR):
                    err = await self.mainAgent.do(
                        hatchpool.ready.find_by_tag(self.mainAgent.OG_hatchery)(UPGRADETOLAIR_LAIR))
                    if not err:
                        # print("SUCCESSFUL LAIR UPGRADE")
                        self.mainAgent.built_lair = True

        # checks if base build order requirements are done, allows for expansion of hatcheries at-will
        # currently runs as a test
        if self.mainAgent.roaches_built >= 7 and self.mainAgent.units(
                LAIR).ready.exists and self.mainAgent.base_build_order_complete is False:
            self.mainAgent.base_build_order_complete = True
            # print("DONE WITH BASE BUILD ORDER")


def main():
    # Start game as SafeRoach as the Bot, and begin logging
    sc2.run_game(sc2.maps.get("Abyssal Reef LE"), [
        Bot(Race.Zerg, SafeRoachAgent(True)),
        Computer(Race.Protoss, Difficulty.Hard)
    ], realtime=False)


if __name__ == '__main__':
    main()
