from loser_agent import *

class SpawnPoolRavagerAgent(LoserAgent):
    def __init__(self, is_logging = False, isMainAgent = False):
        super().__init__(is_logging, "", isMainAgent)

        

    async def on_step(self, iteration):
        self.mainAgent.log("Step: %s Idle Workers: %s Overlord: %s" % (str(iteration), str(self.get_idle_workers), str(self.mainAgent.units(OVERLORD).amount)))
        #self.log(str(self.researched))
        self.mainAgent.log(str(self.get_minerals)) # no attribute "mineral_content" but "get_minerals()" is recognized
def main():
    # Start game with LoserAgent as the Bot, and begin logging
    sc2.run_game(sc2.maps.get("Abyssal Reef LE"), [
        Bot(Race.Zerg, SpawnPoolRavagerAgent(True, True)),
        Computer(Race.Protoss, Difficulty.Medium)
    ], realtime=False)

if __name__ == '__main__':
    main()
