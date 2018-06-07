from loser_agent import *

class DumbAgent(LoserAgent):
    def __init__(self, is_logging = False, is_printing_to_console = False, isMainAgent = False, fileName = ""):
        super().__init__(is_logging, is_printing_to_console, isMainAgent)

                         # For debugging
        self.is_logging = is_logging  # Setting this to true to write information to log files in the agents/logs directory
        self.is_printing_to_console = is_printing_to_console  # Setting this to true causes all logs to be printed to the console

        #ZerglingBanelingRushAgent.mainAgent = self

    async def on_step(self, iteration, strategy_num = -1):
        # self.log("Step: %s Overlord: %s" % (str(iteration), str(self.units(OVERLORD).amount)))
        # self.log("Step: " + str(iteration))

        # TEMP: Until strategy is given by Q table
        #strategy_num = (int)(iteration / 75) % 8

        # Build lings, queen, overlords, drones, and meleeattack1
        await self.basic_build(iteration)

        # Perform actions based on given strategy
        if strategy_num == -1:
            # self.mainAgent.log("No given strategy")
            pass
        else:
            await self.perform_strategy(iteration, strategy_num)

    async def basic_build(self, iteration):
        larvae = self.mainAgent.units(LARVA)
        if larvae.exists and self.mainAgent.can_afford(DRONE) and self.mainAgent.supply_left > 0:
            await self.mainAgent.do(larvae.random.train(DRONE))
        if larvae.exists and self.mainAgent.can_afford(OVERLORD) and self.mainAgent.supply_left == 0:
            await  self.mainAgent.do(larvae.random.train(OVERLORD))


def main():
    # Start game with LoserAgent as the Bot, and begin logging
    sc2.run_game(sc2.maps.get("Abyssal Reef LE"), [
        Bot(Race.Zerg, DumbAgent(True, False, True)),
        Computer(Race.Protoss, Difficulty.Medium)
    ], realtime=False)

if __name__ == '__main__':
    main()
