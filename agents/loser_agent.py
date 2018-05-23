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

from sc2.position import Point2


class LoserAgent(sc2.BotAI):

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

        # non-standard upgrade status
        self.can_burrow = 0
        self.zergling_speed = 0
        self.zergling_attack_boost = 0
        self.baneling_speed = 0
        self.roach_speed = 0
        self.roach_tunnel = 0
        self.overlord_speed = 0
        self.hydralisk_range = 0
        self.infestor_parasite = 0
        self.infestor_energy = 0
        self.ultralisk_defense = 0

        # standard upgrades
        # Ground melee
        self.melee1 = 0
        self.melee2 = 0
        self.melee3 = 0

        # Ground ranged
        self.ranged1 = 0
        self.ranged2 = 0
        self.ranged3 = 0

        # Ground defense
        self.carapace1 = 0
        self.carapace2 = 0
        self.carapace3 = 0

        # Flyer attack
        self.flyer_attack1 = 0
        self.flyer_attack2 = 0
        self.flyer_attack3 = 0

        # Flyer defense
        self.flyer_defense1 = 0
        self.flyer_defense2 = 0
        self.flyer_defense3 = 0

        # units built
        self.num_zerglings_built = 0
        self.num_drones_built = 0
        self.num_queens_built = 0
        self.num_roaches_built = 0
        self.num_hydralisks_built = 0
        self.num_banelines_built = 0
        self.num_lurkers_built = 0
        self.num_ravagers_built = 0
        self.num_num_mutalisks_built = 0
        self.num_corrupters_built = 0
        self.num_brood_lords_built = 0
        self.num_swarm_hosts_built = 0
        self.num_vipers_built = 0
        self.num_ultralisks_built = 0

        # Static defenses built
        self.num_spinecrawlers_built = 0
        self.num_sporecrawlers_built = 0

        # Structure built
        self.num_extractors_built = 0
        self.num_hatcheries_built = 0
        self.num_spawningpools_built = 0
        self.num_roachwarrens_built = 0
        self.num_hyraliskdens_built = 0
        self.num_lairs_built = 0
        self.num_infestation_pits_built = 0
        self.num_lurkerdens_built = 0
        self.num_hives_built = 0
        self.num_ultralisk_caverns_built = 0
        self.num_spires_built = 0
        self.num_greater_spires_built = 0

        # Units actively being used for things, gets set to null on strategy change
        self.strike_force = None

        # Previous strategy so you now when the strategy changes
        self.prev_strategy = None

        # True if strategy just changed in this iteration
        self.did_strategy_change = False


    '''
    Base on_step function
    Uses basic_build and performs actions based on the current strategy
    For now, strategies will change ever 100 steps
    Harass strategies are not implemented yet
    '''
    async def on_step(self, iteration, strategy_num=0):
        # self.log("Step: %s Idle Workers: %s Overlord: %s" % (str(iteration), str(self.get_idle_workers), str(self.units(OVERLORD).amount)))
        # self.log("Step: " + str(iteration))

        # TEMP: Until strategy is given by Q table
        strategy_num = (int)(iteration / 75) % 8

        # Build lings, queen, overlords, drones, and meleeattack1
        await self.basic_build(iteration)

        # Perform actions based on given strategy
        if strategy_num == -1:
            self.log("No given strategy")
        else:
            await self.perform_strategy(iteration, strategy_num)

    '''
    Builds a ton of lings
    Build drones and start gathering vespene
    Build a queen
    Build overlords as needed
    Builds a few hydralisks
    '''
    async def basic_build(self, iteration):
        hatchery = self.bases.ready.random
        # Build overlords if close to reaching cap
        if self.supply_used > self.supply_cap - 4 and self.num_larva > 0 and self.can_afford(OVERLORD):
            await self.do(self.random_larva.train(OVERLORD))
        else:
            # Build drones
            if self.units(DRONE).amount < 20 and self.can_afford(DRONE) and self.units(LARVA).amount > 0 and self.supply_used < self.supply_cap:
                await self.do(self.random_larva.train(DRONE))

            if self.units(HYDRALISKDEN).ready.exists and self.units(HYDRALISK).amount < 20 and self.supply_used < self.supply_cap - 3 \
                    and self.can_afford(HYDRALISK) and self.num_larva > 0:
                await self.do(self.random_larva.train(HYDRALISK))

            # Build lings
            if self.units(ZERGLING).amount < 100 and self.can_afford(ZERGLING) and self.num_larva > 0 and \
                    self.supply_used < self.supply_cap - 1 and self.units(SPAWNINGPOOL).ready.exists:
                await self.do(self.random_larva.train(ZERGLING))
        # Build Spawning pool
        if not self.units(SPAWNINGPOOL).exists and self.can_afford(SPAWNINGPOOL):
            p = hatchery.position.towards(self.game_info.map_center, 3)
            await self.build(SPAWNINGPOOL, near=p)

        if self.num_extractors_built < 1 and self.can_afford(EXTRACTOR):
            self.num_extractors_built += 1
            drone = self.workers.random
            target = self.state.vespene_geyser.closest_to(drone.position)
            await self.do(drone.build(EXTRACTOR, target))

        # If Extractor does not have 3 drones, give it more drones
        for extractor in self.units(EXTRACTOR):
            if extractor.assigned_harvesters < extractor.ideal_harvesters and self.workers.amount > 0:
                await self.do(self.workers.random.gather(extractor))

        # Build Spawning pool
        if not self.units(EVOLUTIONCHAMBER).exists and self.can_afford(SPAWNINGPOOL):
            p = hatchery.position.towards(self.game_info.map_center, 3)
            await self.build(EVOLUTIONCHAMBER, near=p)
        elif self.can_afford(RESEARCH_ZERGMELEEWEAPONSLEVEL1) and self.melee1 == 0 and self.units(EVOLUTIONCHAMBER).ready.exists:
            # Get melee1 upgrade
            self.melee1 = 1
            await self.do(self.units(EVOLUTIONCHAMBER).first(RESEARCH_ZERGMELEEWEAPONSLEVEL1))

        # Build a queen if you haven't
        if self.num_queens_built < 1 and self.units(SPAWNINGPOOL).ready.exists and self.can_afford(QUEEN) and \
                self.supply_used < self.supply_cap - 1:
            base = self.bases.random
            self.num_queens_built += 1
            await self.do(base.train(QUEEN))

        # Inject larva when possible
        elif self.units(QUEEN).amount > 0:
            queen = self.units(QUEEN).first
            abilities = await self.get_available_abilities(queen)
            if AbilityId.EFFECT_INJECTLARVA in abilities:
                await self.do(queen(EFFECT_INJECTLARVA, hatchery))

        # Upgrade to lair when possible
        if self.num_lairs_built == 0 and self.units(HATCHERY).amount > 0 and self.can_afford(AbilityId.UPGRADETOLAIR_LAIR) \
                and self.can_afford(UnitTypeId.LAIR) and self.units(SPAWNINGPOOL).ready.exists and self.units(QUEEN).amount > 0:
            hatchery = self.units(HATCHERY).first
            self.num_lairs_built += 1
            err = await self.do(hatchery(UPGRADETOLAIR_LAIR))
            if err:
                self.num_lairs_built -= 1

        # Build hydralisk den when possible
        if not self.units(HYDRALISKDEN).exists and self.units(LAIR).amount > 0 and self.can_afford(HYDRALISKDEN) \
                and self.num_hydralisks_built == 0:
            p = hatchery.position.towards(self.game_info.map_center, 3)
            self.num_hydralisks_built += 1
            await self.build(HYDRALISKDEN, near=p)

        # Build lurker den when possible
        if self.num_lurkerdens_built == 0 and self.units(HYDRALISKDEN).ready.amount > 0 and \
                self.can_afford(UPGRADETOLURKERDEN_LURKERDEN):
            # await self.do(self.units(HYDRALISKDEN).first(UPGRADETOLURKERDEN_LURKERDEN ))
            self.num_lurkerdens_built += 1
            await self.do(self.units(HYDRALISKDEN).first(MORPH_LURKERDEN))



    '''
    Calls the correct strategy function given the strategy enum value
    Strategy functions can be override in base classes
    '''
    async def perform_strategy(self, iteration, strategy_num):
        self.clean_strike_force()  # Clear dead units from strike force

        # Make sure given strategy num is valid
        if Strategies.has_value(strategy_num):
            # Valid strategy num, convert int into enum value
            strategy = Strategies(strategy_num)

            # Mark strategy as changed or not
            if strategy != self.prev_strategy:
                self.log("New strategy is " + str(strategy))
                self.did_strategy_change = True
                self.strike_force = None
            else:
                self.did_strategy_change = False

            self.prev_strategy = strategy  # Prepare for next iteration
        else:
            self.log_error(f"Unknown strategy number {strategy_num}")
            return

        # Call the proper strategy function

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
        # Strategy just changed, need to take a strike_force
        if self.strike_force is None:
            self.strike_force = army.take(desired_strike_force_size)

        # If strike force should include more members (If a unit was built)
        # Do not add more units if the entire army is already in strike force
        if len(self.strike_force) < desired_strike_force_size and len(army) > len(self.strike_force):

            self.strike_force += (army - self.strike_force).take(desired_strike_force_size - len(self.strike_force))


        # By now we must have at least 1 offensive unit
        target = self.select_target()
        unselected_army = army - self.strike_force

        # All strike force members attack
        for unit in self.strike_force:
            await self.do(unit.attack(target))

        # # Remaining offensive units just wait at their position
        # for unit in unselected_army:
        #     await self.do(unit.hold_position())


    '''
    Send all military units out to different areas
    Die for knowledge
    '''
    async def heavy_scouting(self, iteration):
        await self.scout_with_percentage_of_army(1, True, False)

    '''
    Send a good amount of military units out
    '''
    async def medium_scouting(self, iteration):
        await self.scout_with_percentage_of_army(.5, True, False)

    '''
    Send a couple of things out for scouting and pull back if damage is taken
    '''
    async def light_scouting(self, iteration):
        await self.scout_with_percentage_of_army(.5, True, True)

    async def scout_with_percentage_of_army(self, percentage, use_overlords, pull_back_if_damaged):
        map_width = self.game_info.map_size[0]
        map_height = self.game_info.map_size[1]

        army = self.army

        if use_overlords:
            army += self.units(OVERLORD)

        desired_strike_force_size = int(percentage * army.amount)
        if self.strike_force is None:
            self.strike_force = army.take(desired_strike_force_size)

        # If strike force should include more members (If a unit was built)
        # Do not add more units if the entire army is already in strike force
        if len(self.strike_force) < desired_strike_force_size and len(army) > len(self.strike_force):
            self.strike_force += (army - self.strike_force).take(desired_strike_force_size - len(self.strike_force))

        for unit_ref in self.strike_force:
            # Need to reacquire unit from self.units to see that a command has been queued
            id = unit_ref.tag
            unit = self.units.find_by_tag(id)

            if unit is None:
                # Unit died
                self.strike_force.remove(unit_ref)
                continue
            if pull_back_if_damaged and unit.health < unit.health_max:
                # If pull_back is true and unti is damaged, move to random hatchery
                if (len(self.bases) > 0):
                    await self.do(unit.move(self.bases[random.randrange(0, len(self.bases))].position))
            elif unit.noqueue:
                # Go to a new random position
                pos = lambda: None  # https://stackoverflow.com/questions/19476816/creating-an-empty-object-in-python
                pos.x = random.randrange(0, map_width)
                pos.y = random.randrange(0, map_height)
                position_to_search = Point2.from_proto(pos)
                await self.do(unit.move(position_to_search))

    '''
    Complete recall back to main base
    Build lots of static defenses
    Build lots of lurkers 
    '''
    async def heavy_defense(self, iteration):
        # Build 5 spinecrawlers and sporecrawlers, and 10 lurkers
        await self.prepare_defenses(4, 4, 10)

    '''
    Recall and distribute between main base and explansions
    Build some defensive structures and units
    '''
    async def medium_defense(self, iteration):
        # Build 3 spinecrawlers and sporecrawlers, and 5 lurkers
        await self.prepare_defenses(3, 3, 5)

    '''
    Distribute forces between main base and expansions
    Build a few defensive structures and units
    '''
    async def light_defense(self, iteration):
        # Build 1 spinecrawlers and sporecrawlers, and 3 lurkers
        await self.prepare_defenses(1, 1, 3)


    async def prepare_defenses(self, num_spine_crawlers_to_build, num_sporecrawlers_to_build, num_lurkers_to_build):
        hatchery = self.bases.ready.random

        # TODO: have some units go to expansions
        # Return all units to base
        for unit in self.army + self.overlords:
            if unit.distance_to(hatchery.position) > 20:
                await self.do(unit.move(hatchery.position))


        # Build spine crawlers
        if self.units(SPAWNINGPOOL).ready.exists and self.num_spinecrawlers_built < num_spine_crawlers_to_build \
                and self.can_afford(SPINECRAWLER):
            self.num_spinecrawlers_built += 1
            p = hatchery.position.towards(self.game_info.map_center, 3)
            await self.build(SPINECRAWLER, near=p)

        # Build spore crawlers
        if self.units(EVOLUTIONCHAMBER).ready.exists and self.num_sporecrawlers_built < num_sporecrawlers_to_build \
                and self.can_afford(SPORECRAWLER):
            self.num_sporecrawlers_built += 1
            p = hatchery.position.towards(self.game_info.map_center, 3)
            await self.build(SPORECRAWLER, near=p)


        # Build lurkers
        if self.units(LURKERDENMP).ready.exists and self.num_lurkers_built < num_lurkers_to_build \
                and self.can_afford(MORPH_LURKER) and self.num_larva > 0 and self.units(HYDRALISK).amount > 0:
            self.num_lurkers_built += 1
            hydralisk = self.units(HYDRALISK).random
            err = await self.do(hydralisk(MORPH_LURKER))
            if err:
                self.num_lurkers_built -= 1

        # Burrow all lurkers so they can attack
        for lurker in self.units(LURKERMP):
            abilities = await self.get_available_abilities(lurker)
            if AbilityId.BURROWDOWN_LURKER in abilities:
                await self.do(lurker(BURROWDOWN_LURKER))


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
    Removes dead units from strike force
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
        return self.units - self.units(DRONE) - self.units(OVERLORD) - self.units(LARVA) - self.units(EGG) \
               - self.units(QUEEN) - self.buildings - self.units(LURKERMPBURROWED)

    @property
    def overlords(self):
        return self.units(OVERLORD)

    @property
    def buildings(self):
        return self.units(HATCHERY) + self.units(LAIR) + self.units(HIVE) + self.units(EXTRACTOR) + self.units(SPAWNINGPOOL) \
               + self.units(ROACHWARREN) + self.units(CREEPTUMOR) + self.units(EVOLUTIONCHAMBER) + self.units(HYDRALISKDEN) \
               + self.units(SPIRE) + self.units(GREATERSPIRE) + self.units(ULTRALISKCAVERN) + self.units(INFESTATIONPIT) \
               + self.units(NYDUSNETWORK) + self.units(BANELINGNEST) + self.units(SPINECRAWLER) + self.units(SPORECRAWLER) \
                + self.units(LURKERDEN) + self.units(LURKERDENMP)

    @property
    def bases(self):
        return self.units(HATCHERY) | self.units(LAIR) | self.units(HIVE)

    def get_random_worker(self):
        return self.units(DRONE).random

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
    def num_larva(self):
        """Get the current amount of larva"""
        return self.units(LARVA).amount

    @property
    def random_larva(self):
        """Get a random larva"""
        return self.units(LARVA).random

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
