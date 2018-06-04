from loser_agent import *

class RavagerAgent(LoserAgent):
    def __init__(self, is_logging = False):
        super().__init__()

        self.drone_counter = 0
        self.overlord_counter = 0
        self.zergling_counter = 0
        self.spawning_pool_started = False

        # For debugging
        self.is_logging = is_logging
        if self.is_logging:

            # Make logs directory if it doesn't exist
            if not os.path.exists("./logs"):
                os.mkdir("./logs")
            self.log_file_name = "./logs/" + strftime("%Y-%m-%d %H:%M:%S", localtime()) + ".log"
            self.log_file = open(self.log_file_name, "w+")  # Create log file based on the time

    async def on_step(self, iteration):

        hatchery = self.units(HATCHERY).ready.first
        larvae = self.units(LARVA)
        target = self.known_enemy_structures.random_or(self.enemy_start_locations[0]).position

        if not self.spawning_pool_started and self.can_afford(SPAWNINGPOOL):
            for d in range(4, 15):
                pos = hatchery.position.to2.towards(self.game_info.map_center, d)
                if await self.can_place(SPAWNINGPOOL, pos):
                    drone = self.workers.closest_to(pos)
                    err = await self.do(drone.build(SPAWNINGPOOL, pos))
                    if not err:
                        self.spawning_pool_started = True
                        print("Spawning pool started")
                        break

        if self.spawning_pool_started:
            if self.can_afford(DRONE) and larvae.exists and self.supply_left > 0 and self.drone_counter < 3:
                await self.do(larvae.random.train(DRONE))
                self.drone_counter += 1
                print("Drone " + str(self.drone_counter))
                print("Game Time: " + str(self.game_time))



def main():
    # Start game with LoserAgent as the Bot, and begin logging
    sc2.run_game(sc2.maps.get("Abyssal Reef LE"), [
        Bot(Race.Zerg, RavagerAgent(True)),
        Computer(Race.Protoss, Difficulty.Easy)
    ], realtime=False)

if __name__ == '__main__':
    main()
