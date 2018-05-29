from loser_agent import *

class ZerglingBanelingRushAgent(LoserAgent):
    def __init__(self, is_logging = False):
        super().__init__()

        self.drone_counter = 0
        self.overlord_counter = 0
        self.zergling_counter = 0
        self.baneling_counter = 0
        self.extractor_started = False
        self.hatchery_started = False
        self.spawning_pool_started = False
        self.moved_workers_to_gas = False
        self.moved_workers_from_gas = False
        self.moved_worker_to_expand = False
        self.queen_started = False
        self.mboost_started = False
        self.baneling_nest_started = False
        self.attacking = False

        # For debugging
        self.is_logging = is_logging
        if self.is_logging:

            # Make logs directory if it doesn't exist
            if not os.path.exists("./logs"):
                os.mkdir("./logs")
            self.log_file_name = "./logs/" + strftime("%Y-%m-%d %H:%M:%S", localtime()) + ".log"
            self.log_file = open(self.log_file_name, "w+")  # Create log file based on the time

    async def on_step(self, iteration):
        self.log("Step: %s Idle Workers: %s Overlord: %s" % (str(iteration), str(self.get_idle_workers), str(self.units(OVERLORD).amount)))
        self.log(str(self.game_time))
        self.log(str(self.get_vespene))

        hatchery = self.units(HATCHERY).ready.first
        larvae = self.units(LARVA)
        target = self.known_enemy_structures.random_or(self.enemy_start_locations[0]).position

        if iteration == 0:
            await self.do(larvae.random.train(DRONE))
            self.drone_counter += 1
            print("Drone " + str(self.drone_counter))

        if self.game_time > 75 and self.workers.exists:
            for extractor in self.units(EXTRACTOR):
                if extractor.assigned_harvesters < extractor.ideal_harvesters and self.workers.exists:
                    await self.do(self.workers.random.gather(extractor))

        if self.overlord_counter == 0 and larvae.exists and self.can_afford(OVERLORD):
            await self.do(larvae.random.train(OVERLORD))
            self.overlord_counter += 1
            print ("Overlord " + str(self.overlord_counter))

        if self.overlord_counter ==  1:
            if self.can_afford(DRONE) and larvae.exists and self.supply_left > 0:
                await self.do(larvae.random.train(DRONE))
                self.drone_counter += 1
                print("Drone " + str(self.drone_counter))
                print("Game Time: " + str(self.game_time))

        if self.game_time > 100:
            if self.overlord_counter == 1 and larvae.exists and self.can_afford(OVERLORD):
                await self.do(larvae.random.train(OVERLORD))
                self.overlord_counter += 1
                print ("Overlord " + str(self.overlord_counter))
            elif self.game_time > 110 and self.overlord_counter == 2 and larvae.exists and self.can_afford(OVERLORD):
                await self.do(larvae.random.train(OVERLORD))
                self.overlord_counter += 1
                print ("Overlord " + str(self.overlord_counter))

        if self.game_time > 50 and self.moved_worker_to_expand == False:
            pos = await self.get_next_expansion()
            err = await self.do(self.workers.closest_to(pos).move(pos))
            if not err:
                self.moved_worker_to_expand = True
                print("Worked moved to expansion point")
                print("Game Time: " + str(self.game_time))

        if self.game_time > 60 and self.moved_worker_to_expand == True and not self.hatchery_started and self.can_afford(HATCHERY):
            pos = await self.get_next_expansion()
            drone = self.workers.closest_to(pos)
            err = await self.build(HATCHERY, near=pos, max_distance=20, unit=drone)
            if not err:
                self.hatchery_started = True
                print("Hatchery Started")
                print("Game Time: " + str(self.game_time))

        if not self.extractor_started and not self.attacking:
            if self.can_afford(EXTRACTOR) and self.workers.exists:
                drone = self.workers.random
                target = self.state.vespene_geyser.closest_to(drone.position)
                err = await self.do(drone.build(EXTRACTOR, target))
                if not err:
                    self.extractor_started = True
                    print("Extractor Started")
                    print("Game Time: " + str(self.game_time))

        elif not self.spawning_pool_started:
            if self.can_afford(SPAWNINGPOOL):
                for d in range(4, 15):
                    pos = hatchery.position.to2.towards(self.game_info.map_center, d)
                    if await self.can_place(SPAWNINGPOOL, pos):
                        drone = self.workers.closest_to(pos)
                        err = await self.do(drone.build(SPAWNINGPOOL, pos))
                        if not err:
                            self.spawning_pool_started = True
                            print("Spawning pool started")
                            break

        elif not self.queen_started and self.units(SPAWNINGPOOL).ready.exists:
            if self.can_afford(QUEEN):
                err = await self.do(hatchery.train(QUEEN))
                if not err:
                    self.queen_started = True
                    print("Queen Started")
                    print("Game Time: " + str(self.game_time))

        for queen in self.units(QUEEN).idle:
            abilities = await self.get_available_abilities(queen)
            if AbilityId.EFFECT_INJECTLARVA in abilities:
                await self.do(queen(EFFECT_INJECTLARVA, hatchery))
                print("Larva Injected")
                print("Game Time: " + str(self.game_time))

        if self.get_vespene >= 100:
            sp = self.units(SPAWNINGPOOL).ready
            if sp.exists and self.minerals >= 100 and not self.mboost_started:
                await self.do(sp.first(RESEARCH_ZERGLINGMETABOLICBOOST))
                self.mboost_started = True
                print("Researched Metabolic Boost")
                print("Game Time: " + str(self.game_time))

        if self.units(SPAWNINGPOOL).ready.exists:
            if larvae.exists and self.can_afford(ZERGLING) and self.supply_left >= 1:
                if self.zergling_counter < 5 and self.queen_started:
                    await self.do(larvae.random.train(ZERGLING))
                    self.zergling_counter += 1

        if self.zergling_counter >= 5:
            self.attacking = True

            for unit in self.units(ZERGLING) | self.units(QUEEN) | self.units(BANELING):
                await self.do(unit.attack(target.to2.towards(self.game_info.map_center, 30)))

            if self.baneling_counter != 0:
                for worker in self.workers:
                    await self.do(worker.attack(target.to2.towards(self.game_info.map_center, 30)))

        if not self.baneling_nest_started:
            if self.can_afford(BANELINGNEST) and self.units(SPAWNINGPOOL).ready.exists:
                for d in range(4, 15):
                    pos = hatchery.position.to2.towards(self.game_info.map_center, d)
                    if await self.can_place(BANELINGNEST, pos):
                        drone = self.workers.closest_to(pos)
                        err = await self.do(drone.build(BANELINGNEST, pos))
                        if not err:
                            self.baneling_nest_started = True
                            print("Baneling nest started")
                            break

        if self.units(BANELINGNEST).ready.exists:
            for zergling in self.units(ZERGLING).ready:
                if self.can_afford(MORPHZERGLINGTOBANELING_BANELING) and larvae.exists and self.baneling_counter < self.zergling_counter / 2:
                    err = await self.do(zergling(MORPHZERGLINGTOBANELING_BANELING))
                    if not err:
                        self.baneling_counter += 1
                        print("Morphed baneling")
                else:
                    break


def main():
    # Start game with LoserAgent as the Bot, and begin logging
    sc2.run_game(sc2.maps.get("Abyssal Reef LE"), [
        Bot(Race.Zerg, ZerglingBanelingRushAgent(True)),
        Computer(Race.Terran, Difficulty.Easy)
    ], realtime=False)

if __name__ == '__main__':
    main()
