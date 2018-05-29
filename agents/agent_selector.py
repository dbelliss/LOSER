#!/usr/bin/python3
# https://chatbotslife.com/building-a-basic-pysc2-agent-b109cde1477c
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
from loser_agent import *
from saferoach_agent import SafeRoachAgent
from zerglingBanelingRush_agent import SpawnPoolRavagerAgent
from NeuralNetwork import NeuralNetwork
from strategies import Strategies
import time
import numpy


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


class AgentSelector(LoserAgent):
    #TODO Implement previous known enemy list so that we dont lose info over time
    def __init__(self, is_logging = False, is_printing_to_console = False, isMainAgent = False):
        super().__init__(is_logging, is_printing_to_console, isMainAgent, "AgentSelector_")
        print(bcolors.OKGREEN + "###AgentSelector Constructor" + bcolors.ENDC)

        # List of build orders
        self.agents = [LoserAgent(), LoserAgent()]
        self.nAgents = len(self.agents)

        # Choose RandomBuild
        self.chooseRandomBuild()

        # Number of strategies
        self.strategies = Strategies
        self.nStrategies = len(Strategies)

        # Choose RandomStrategy
        self.chooseRandomStrategy()

        # Properties
        self.stepsPerAgent = 100
        self.curAgentIndex = 0
        self.strategiesIndex = 0
        self.curStep = 0
        self.timesSwitched = 0

        # number of calculated inputs such as army size, mineral rate, etc. prevInput list must be same length as this value
        self.nInputs = 11

        self.prevInputs = [0] * self.nInputs
        self.prevAgent = 0
        self.prevStrategy = 0
        self.lastFitness = 0

        # inputs = nData inputs + nAgents (for last agent selected) + nStrategies (for last strategy selected)
        # outputs = nAgents
        self.agentNN = NeuralNetwork(self.nInputs + self.nAgents + self.nStrategies, self.nAgents, 1, 1, 100)

        # inputs = nData inputs + 2 * nAgents (for last and current agent selected) + nStrategies (for last strategy selected)
        # outputs = nStrategies
        self.strategyNN = NeuralNetwork(self.nInputs + 2 * self.nAgents + self.nStrategies, self.nStrategies, 1, 1, 100)

    def fitness(self):
        return (self.lastFitness + .5) % 1

    def chooseRandomBuild(self):
        self.curAgentIndex = 0
        print(bcolors.OKGREEN + "###RandomBuildIndex: {}".format(self.agents[self.curAgentIndex]) + bcolors.ENDC)

    def chooseRandomStrategy(self):
        self.strategiesIndex = 0
        print(bcolors.OKGREEN + "###RandomStrategyIndex: {}".format(self.strategiesIndex) + bcolors.ENDC)

    '''
    Counting our own ground units for NN inputs
    This function excludes dealing with workers since we want to know how our workers are partioned
    '''
    def ground_unit_breakdown(self):
        queens = self.mainAgent.units(QUEEN).amount + self.mainAgent.units(QUEENBURROWED).amount
        zerglings = self.mainAgent.units(ZERGLING).amount + self.mainAgent.units(ZERGLINGBURROWED).amount
        banelings = self.mainAgent.units(BANELING).amount + self.mainAgent.units(BANELINGBURROWED).amount
        roaches = self.mainAgent.units(ROACH).amount + self.mainAgent.units(ROACHBURROWED).amount
        ravagers = self.mainAgent.units(RAVAGER).amount + self.mainAgent.units(RAVAGERBURROWED).amount
        hydralisks = self.mainAgent.units(HYDRALISK).amount + self.mainAgent.units(HYDRALISKBURROWED).amount
        lurkers = self.mainAgent.units(LURKER).amount + self.mainAgent.units(LURKERBURROWED).amount
        infestors = self.mainAgent.units(INFESTOR).amount + self.mainAgent.units(INFESTORBURROWED).amount
        swarm_host = self.mainAgent.units(SWARMHOSTMP).amount + self.mainAgent.units(SWARMHOSTBURROWEDMP).amount
        ultralisks = self.mainAgent.units(ULTRALISK).amount + self.mainAgent.units(ULTRALISKBURROWED).amount
        locusts = self.mainAgent.units(LOCUSTMP).amount #TODO looks like there isnt a locust burrowed type but it can be flying as well?
        broodlings = self.mainAgent.units(BROODLING).amount
        changelings = self.mainAgent.units(CHANGELING).amount
        infested_terrans = self.mainAgent.units(INFESTORTERRAN).amount + self.mainAgent.units(INFESTORTERRANBURROWED).amount #TODO check this is the right constant or if I should be using INFESTEDTERRAN
        # nydus_worms = self.mainAgent.units().amount + self.mainAgent.units().amount TODO Not sure how to handle nydus netowrks...input will be helpful
        return [queens, zerglings, banelings, roaches, ravagers, hydralisks, lurkers, swarm_host, ultralisks, locusts, broodlings, changelings, infested_terrans]

    '''
    Counting our own flying units for NN inputs
    '''
    def flying_unit_breakdown(self):
        overlords = self.mainAgent.units(OVERLORD).amount
        overseers = self.mainAgent.units(OVERSEER).amount
        mutalisks = self.mainAgent.units(MUTALISK).amount
        corruptors = self.mainAgent.units(CORRUPTOR).amount
        brood_lords = self.mainAgent.units(BROODLORD).amount
        vipers = self.mainAgent.units(VIPER).amount
        return [overlords, overseers, mutalisks, corruptors, brood_lords, vipers]

    '''
    Counting our own building units for NN inputs
    '''
    def building_breakdown(self):
        hatcheries = self.mainAgent.units(HATCHERY).amount
        spine_crawlers = self.mainAgent.units(SPINECRAWLER).amount
        spore_crawlers = self.mainAgent.units(SPORECRAWLER).amount
        extractors = self.mainAgent.units(EXTRACTOR).amount
        spawning_pools = self.mainAgent.units(SPAWNINGPOOL).amount
        evolution_chambers = self.mainAgent.units(EVOLUTIONCHAMBER).amount
        roach_warrens = self.mainAgent.units(ROACHWARREN).amount
        baneling_nests = self.mainAgent.units(BANELINGNEST).amount
        creep_tumors = self.mainAgent.units(CREEPTUMOR).amount
        lairs = self.mainAgent.units(LAIR).amount
        hydralisk_dens = self.mainAgent.units(HYDRALISKDEN).amount
        lurker_dens = self.mainAgent.units(LURKERDEN).amount
        infestation_pits = self.mainAgent.units(INFESTATIONPIT).amount
        spires = self.mainAgent.units(SPIRE).amount
        # nydus_network TODO need to figure out how to handle nydus netowrks
        hives = self.mainAgent.units(HIVE).amount
        greater_spires = self.mainAgent.units(GREATERSPIRE).amount
        ultralisk_caverns = self.mainAgent.units(ULTRALISKCAVERN).amount
        return [hatcheries, spine_crawlers, spore_crawlers, extractors, spawning_pools, evolution_chambers, roach_warrens, baneling_nests, \
                creep_tumors, lairs, hydralisk_dens, lurker_dens, infestation_pits, spires, hives, greater_spires, ultralisk_caverns]

    def total_worker_count(self):
        return self.mainAgent.workers.amount

    def idle_workers_count(self):
        return self.mainAgent.workers.idle.amount

    def vespene_worker_count(self):
        workers = 0
        for extractor in self.mainAgent.units(EXTRACTOR):
            workers = workers + extractor.assigned_harvesters
        return workers

    # Should this be updated to go through mineral fields and count workers?
    def mineral_worker_count(self):
        return self.mainAgent.total_worker_count() - self.mainAgent.vespene_worker_count() - self.mainAgent.idle_workers_count()

    '''
    Breakdown how our workers are being utilize
    Let me know if workers can be classified as something else (ex: building something) since I could not find the equivalent for
    mineral fields as the function used to find all vespene workers
    '''
    def worker_breakdown(self):
        return [self.total_worker_count(), self.idle_workers_count(), self.vespene_worker_count(), self.mineral_worker_count()]

    #TODO Potentially add rate collection for minerals and vespene which can be calculated using how many workers we have mining each?
    def resource_breakdown(self):
        return [self.mainAgent.minerals, self.mainAgent.vespene]

    '''
    Breakdown entirety of protoss known structures and returns them as an array
    '''
    def protoss_breakdown(self):
        probes, zealots, stalkers, sentries, adepts, high_templars, dark_templars, immortals, colussuses, \
        disruptors, archons, observers, warp_prisms, phoenixes, void_rays, oracles, carriers, tempests, \
        mothership_core, mothership, nexuses, pylons, assimilators, gateways, forges, cybernetics_cores, \
        photon_cannons, robotoics_facilities, warp_gates, stargates, twilight_councils, robotics_bays, \
        fleet_beacons, templar_archives, dark_shrines = (0,) * 35
        for unit in self.mainAgent.known_enemy_units:
            if unit.name == 'Probe':
                 probes = probes + 1
            if unit.name == 'Zealot':
                zealots = zealots + 1
            if unit.name == 'Stalker':
                stalkers = stalkers + 1
            if unit.name == 'Sentry':
                sentries = sentries + 1
            if unit.name == 'Adept':
                adepts = adepts + 1
            if unit.name == 'HighTemplar':
                high_templars = high_templars + 1
            if unit.name == 'DarkTemplar':
                dark_templars = dark_templars + 1
            if unit.name == 'Immortal':
                immortals = immortals + 1
            if unit.name == 'Colussus':
                colussuses = colussuses + 1
            if unit.name == 'Disruptor':
                disruptors = disruptors + 1
            if unit.name == 'Archon':
                archons = archons + 1
            if unit.name == 'Observer':
                observers = observers + 1
            if unit.name == 'WarpPrism':
                warp_prisms = warp_prisms + 1
            if unit.name == 'Phoenix':
                phoenixes = phoenixes + 1
            if unit.name == 'VoidRay':
                void_rays = void_rays + 1
            if unit.name == 'Oracle':
                oracles = oracles + 1
            if unit.name == 'Carrier':
                carriers = carriers + 1
            if unit.name == 'Tempest':
                tempests = tempests + 1
            if unit.name == 'MothershipCore':
                mothership_core = mothership_core + 1
            if unit.name == 'Mothership':
                mothership = mothership + 1
            if unit.name == 'Nexus':
                nexuses = nexuses + 1
            if unit.name == 'Pylon':
                pylons = pylons + 1
            if unit.name == 'Assimilator':
                assimilators = assimilators + 1
            if unit.name == 'Gateway':
                gateways = gateways + 1
            if unit.name == 'Forge':
                forges = forges + 1
            if unit.name == 'CyberneticsCore':
                cybernetics_cores = cybernetics_cores + 1
            if unit.name == 'PhotonCannon':
                photon_cannons = photon_cannons + 1
            if unit.name == 'RoboticsFacility':
                robotoics_facilities = robotoics_facilities + 1
            if unit.name == 'WarpGate':
                warp_gates = warp_gates + 1
            if unit.name == 'Stargate':
                stargates = stargates + 1
            if unit.name == 'TwilightCouncil':
                twilight_councils = twilight_councils + 1
            if unit.name == 'RoboticsBay':
                robotics_bays = robotics_bays + 1
            if unit.name == 'FleetBeacon':
                fleet_beacons = fleet_beacons + 1
            if unit.name == 'TemplarArchives':
                templar_archives = templar_archives + 1
            if unit.name == 'DarkShrine':
                dark_shrines = dark_shrines + 1
        return [probes, zealots, stalkers, sentries, adepts, high_templars, dark_templars, immortals, colussuses, \
                disruptors, archons, observers, warp_prisms, phoenixes, void_rays, oracles, carriers, tempests, \
                mothership_core, mothership, nexuses, pylons, assimilators, gateways, forges, cybernetics_cores, \
                photon_cannons, robotoics_facilities, warp_gates, stargates, twilight_councils, robotics_bays, \
                fleet_beacons, templar_archives, dark_shrines]

    '''
    START OF DEPRICATED CODE
    The following functions sandwiched between THIS STATEMENT and the next are all depricated
    but are kept so that the overall functionality of agent_selector does not break while the code is updated
    TODO: Update normalize_inputs() after the above code is finished to feed all inputs into NN
    '''
    def ground_army_count(self):
        return self.mainAgent.units(QUEEN).amount + self.mainAgent.units(ZERGLING).amount + self.mainAgent.units(BANELING).amount \
        + self.mainAgent.units(ROACH).amount + self.mainAgent.units(RAVAGER).amount + self.mainAgent.units(HYDRALISK).amount \
        + self.mainAgent.units(LURKER).amount + self.mainAgent.units(INFESTOR).amount + self.mainAgent.units(SWARMHOSTMP).amount \
        + self.mainAgent.units(ULTRALISK).amount + self.mainAgent.units(LOCUSTMP).amount + self.mainAgent.units(BROODLING).amount \
        + self.mainAgent.units(CHANGELING).amount

    def flying_army_count(self):
        return self.mainAgent.units(OVERSEER).amount + self.mainAgent.units(MUTALISK).amount + self.mainAgent.units(CORRUPTOR).amount \
                + self.mainAgent.units(BROODLORD).amount + self.mainAgent.units(VIPER).amount

    def mineral_count(self):
        return self.mainAgent.minerals

    def vespene_count(self):
        return self.mainAgent.vespene

    def building_count(self):
        return self.mainAgent.units(HATCHERY).amount + self.mainAgent.units(LAIR).amount + self.mainAgent.units(HIVE).amount + self.mainAgent.units(EXTRACTOR).amount + self.mainAgent.units(SPAWNINGPOOL).amount \
               + self.mainAgent.units(ROACHWARREN).amount + self.mainAgent.units(CREEPTUMOR).amount + self.mainAgent.units(EVOLUTIONCHAMBER).amount + self.mainAgent.units(HYDRALISKDEN).amount \
               + self.mainAgent.units(SPIRE).amount + self.mainAgent.units(GREATERSPIRE).amount + self.mainAgent.units(ULTRALISKCAVERN).amount + self.mainAgent.units(INFESTATIONPIT).amount \
               + self.mainAgent.units(NYDUSNETWORK).amount + self.mainAgent.units(BANELINGNEST).amount + self.mainAgent.units(SPINECRAWLER).amount + self.mainAgent.units(SPORECRAWLER).amount \
               + self.mainAgent.units(LURKERDEN).amount + self.mainAgent.units(LURKERDENMP).amount

    def enemy_count(self):
        return self.mainAgent.known_enemy_units.amount

    def enemy_building_count(self):
        return self.mainAgent.known_enemy_structures.amount

    # May need to change the building normalization
    def normalize_inputs(self):
        minerals = (self.mineral_count()/1000)
        vespene = (self.vespene_count()/1000)
        total_workers = (self.total_worker_count()/200)
        mineral_workers = (self.mineral_worker_count()/200)
        vespene_workers = (self.vespene_worker_count()/200)
        idle_workers = (self.idle_workers_count()/100)
        ground_army = (self.ground_army_count()/200)
        flying_army = (self.flying_army_count()/200)
        buildings = (self.building_count()/200)
        enemies = (self.enemy_count()/200)
        enemy_buildings = (self.enemy_building_count()/200)
        return [minerals, vespene, total_workers, mineral_workers, vespene_workers, idle_workers, ground_army, flying_army, buildings, enemies, enemy_buildings]

    '''
    END OF DEPRICATED CODE
    '''

    async def on_step(self, iteration):
        # Run fitness on a certain number of steps
        if (iteration % self.stepsPerAgent == 0):
            # self.log(bcolors.OKBLUE + "Normalize inputs: %s" % (str(self.mainAgent.normalize_inputs())) + bcolors.ENDC)
            # print(bcolors.OKGREEN + "Ground unit breakdown: %s" % str(self.ground_unit_breakdown()))
            # print(bcolors.OKGREEN + "Flying unit breakdown: %s" % str(self.flying_unit_breakdown()))
            # print(bcolors.OKGREEN + "Building unit breakdown: %s" % str(self.building_breakdown()))
            # print(bcolors.OKGREEN + "Worker unit breakdown: %s" % str(self.worker_breakdown()))
            # print(bcolors.OKGREEN + "Resource breakdown: %s" % str(self.resource_breakdown()))
            # flying_army, buildings, workers = self.enemy_breakdown()
            # self.log("Flying: {0} Buildings: {1} Workers: {2}".format(str(flying_army), str(buildings), str(workers)))
            # print(bcolors.OKGREEN + "Enemy units: %s" % str(self.mainAgent.known_enemy_units))
            # print(bcolors.OKGREEN + "Protoss breakdown: %s" % str(self.protoss_breakdown()))
            print(bcolors.OKGREEN + "###Fitness function: {}".format(iteration) + bcolors.ENDC)
            self.learn()
            self.selectNewAgentsAndStrategies()

        # TODO
        # Call the current agent on_step
        await self.agents[self.curAgentIndex].on_step(iteration)


    def learn(self):
        curFitness = self.fitness()

        #bogus correct choice and fitness equations for now
        correctChoice = 1 if curFitness > self.lastFitness else 0
        self.lastFitness = curFitness

        #create list for all the inputs to the neural network
        prevAgent = [0] * self.nAgents
        prevStrategy = [0] * self.nStrategies
        curAgent = [1 - correctChoice] * self.nAgents
        curStrategy = [1 - correctChoice] * self.nStrategies

        #this is for the predicted agent that was used as input for the strategy NN. Must be 1 hot like it was during prediction
        predAgent = [0] * self.nAgents

        #set the 1 hot encoding for prev agents and certainty that the current choice was correct
        #these are part of the X's that are used to teach the NN
        prevAgent[self.prevAgent] = 1
        prevStrategy[self.prevStrategy] = 1
        predAgent[self.curAgentIndex] = 1

        #set certainty that the choice was correct
        #these are the y's
        curAgent[self.curAgentIndex] = correctChoice
        curStrategy[self.strategiesIndex] = correctChoice

        #appends all the input lists together, also puts them into lists of lists for the NN
        # ie [1, 2, 3] + [4, 5] => [[1, 2, 3, 4 ,5]]
        agentInputList = [self.prevInputs + prevAgent + prevStrategy]
        agentOutputList = [curAgent]
        strategyInputList = [self.prevInputs + predAgent + prevAgent + prevStrategy]
        strategyOutputList = [curStrategy]
        self.log("Training agentNN with inputs: {0} and outputs {1}".format(str(agentInputList), str(agentOutputList)))
        self.log("Training strategyNN with inputs: {0} and outputs {1}".format(str(strategyInputList), str(strategyOutputList)))
        self.agentNN.train(agentInputList, agentOutputList)
        self.strategyNN.train(strategyInputList, strategyOutputList)


    def selectNewAgentsAndStrategies(self):

        #define other inputs to NN
        # curInputs = [0]
        curInputs = self.mainAgent.normalize_inputs()

        #create list for all the inputs to the neural network
        curAgent = [0] * self.nAgents
        curStrategy = [0] * self.nStrategies

        #set previous choices as 1 hot
        curAgent[self.curAgentIndex] = 1
        curStrategy[self.strategiesIndex] = 1

        #appends all the input lists together, also puts them into lists of lists for the NN
        # ie [1, 2, 3] + [4, 5] => [[1, 2, 3, 4 ,5]]
        agentInputList = [curInputs + curAgent + curStrategy]
        print(bcolors.WARNING + "###agentInputList: {}".format(agentInputList) + bcolors.ENDC)
        self.log("Predicting agentNN with inputs: {0}".format(str(agentInputList)))

        nextAgent = self.agentNN.predict(agentInputList)[0].tolist() #extract first row from returned numpy array
        nextAgentIndex = nextAgent.index(max(nextAgent))
        nextAgent = [nextAgent[i] if i == nextAgentIndex else 0 for i in range(len(nextAgent))]

        strategyInputList = [curInputs + nextAgent + curAgent + curStrategy]
        self.log("Predicting strategyNN with inputs: {0}".format(str(strategyInputList)))
        nextStrategy = self.strategyNN.predict(strategyInputList)[0].tolist() #extract first row from returned numpy array

        self.prevAgent = self.curAgentIndex
        self.prevStrategy = self.strategiesIndex
        self.prevInputs = curInputs
        self.curAgentIndex = nextAgentIndex
        self.strategiesIndex = nextStrategy.index(max(nextStrategy))

def main():
    # Start game with AgentSelector as the Bot, and begin logging
    sc2.run_game(sc2.maps.get("Abyssal Reef LE"), [
        Bot(Race.Zerg, AgentSelector(True, True, True)),
        Computer(Race.Protoss, Difficulty.Medium)
    ], realtime=False)

if __name__ == '__main__':
    main()
