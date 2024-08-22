import random
from math import sqrt
import logging
from exceptions import SimulatorException
from colony import Colony
logging.basicConfig(level=logging.DEBUG,format='{asctime} ({filename}) [{levelname:^8s}] {message}', style='{')

class Simulator:
    _instances = {}
    _next_SID = 0
    
    def __init__(self, SID, battle_draw_chance = 0.01):
        self.SID = SID
        self.colonies = {}
        self.colony_count = 0
        self.battle_draw_chance = battle_draw_chance
        self.evolution_engines = {}
        self.started = False
        self.year: int = 0
        Simulator._instances[SID] = self
        Simulator._next_SID += 1
        logging.info(f"{self.log_head()}: Initialization successful")
        return
    
    def new_evolution_engine(self):
        logging.debug(f"{self.log_head()}: Initializing new Evolution Engine")
        from evolution_engine import EvolutionEngine
        self.evolution_engines[EvolutionEngine._next_EEID] = EvolutionEngine(EvolutionEngine._next_EEID)
        logging.info(f"{self.log_head()}: EvolutionEngine {EvolutionEngine._next_EEID -1} initialized.")
        return
    
    def new_colony(self, name, EEID, PID):
        logging.debug(f"{self.log_head()}: Creating new Colony")
        from colony import Colony
        from player import Player

        for CID, colony in Colony._instances.items():
            if colony.name == name:
                raise SimulatorException("Colony Name already in use")
            

        new_col = self.colonies[Colony._next_CID] = Colony(CID = Colony._next_CID, name = name, EEID = EEID, PID = PID, SID = self.SID)
        Player._instances[PID].assign_colony(new_col.CID)
        self.colony_count += 1
        logging.info(f"{self.log_head()}: New Colony {name} created")
        return
    
    def init_all_colonies(self, num_torbs):
        from ai_player import AIPlayer
        logging.debug(f"{self.log_head()}: Initializing global generation 0")
        for CID, colony in self.colonies.items():
            colony.init_gen_zero(num_torbs)
        self.started = True
        logging.info(f"{self.log_head()}: Global generation zero created")
        for PID, ai in AIPlayer._AI_instances.items():
            logging.debug(f"{self.log_head()}: Calling AI decisions for {ai.name}")
            ai.make_decisions()
        return
    
    def scout(self):
        return

    def combat(self):
        logging.debug(f"{self.log_head()}: Starting global combat")
        from story_strings import winner_adjectives, loser_adjectives
        out_str = ""
        colonies = [colony for CID, colony in self.colonies.items() if not colony.destroyed]
        if len(colonies) < 2:
            return "There were no other colonies to fight this year."
        random.shuffle(colonies)
        for colony in colonies:
            if any(torb.alive for torb in colony.soldiers) and colony.attack_target != None:
                col0 = colony.name
                col1 = Colony._instances[colony.attack_target].name
                logging.debug(f"{self.log_head()}: Sending {col0} and {col1} to battle")

                winner, loser = self.battle(colony, Colony._instances[colony.attack_target])
                if isinstance(winner, Colony) and loser.food >= 1:
                    food_stolen = random.randrange(0, loser.food)
                    winner.food += food_stolen
                    loser.food -= food_stolen
                if winner == None:
                    out_str += f"The battle between **{col0}** and **{col1}** ended without a clear winner.\n"
                else:
                    out_str += f"The {winner_adjectives()} **{winner.name}** won against the {loser_adjectives()} **{loser.name}** and claimed {food_stolen} food.\n"
        logging.info(f"{self.log_head()}: Global combat round complete")
        return out_str

    def battle(self, col0: Colony, col1: Colony):
        logging.debug(f"{self.log_head()}: Starting battle between {col0.name} and {col1.name}")
        army0 = col0.soldiers
        army1 = col1.soldiers
        logging.debug(f"{self.log_head()}: Army0 {len(army0)}, Army1 {len(army1)}")
        while len(army0) > 0 and len(army1) > 0:
            
            random.shuffle(army0)
            random.shuffle(army1)
            self.fight(army0[0], army1[0])
            logging.debug(f"{self.log_head()}: {col0.name} {army0[0].generation}-{army0[0].ID} is fighting {col1.name} {army1[0].generation}-{army1[0].ID}")
            if army0[0].alive == False:
                logging.debug(f"{self.log_head()}: Colony {col0.name} Torb {army0[0].generation}-{army0[0].ID} died in battle")
                army0.pop(0)
            if army1[0].alive == False:
                logging.debug(f"{self.log_head()}: Colony {col1.name} Torb {army1[0].generation}-{army1[0].ID} died in battle")
                army1.pop(0)
            draw_roll = random.uniform(0, 1)
            if draw_roll > (1-self.battle_draw_chance):
                logging.info(f"{self.log_head()}: The battle ended in a draw with roll {draw_roll}")
                break
        if len(army1) == 0:
            winner = col0
            loser = col1
            logging.info(f"{self.log_head()}: {col0.name} won the battle")
        elif len(army0) == 0:
            logging.info(f"{self.log_head()}: {col1.name} won the battle")
            winner = col1
            loser = col0
        else:
            winner = None
            loser = None
            logging.info(f"{self.log_head()}: Neither army won the battle")
        return winner, loser
    
    def fight(self, torb0, torb1):
        logging.debug(f"{self.log_head()}: Torbs from {torb0.colony.name} and {torb1.colony.name} are fighting")
        torb0_power = sqrt(torb0.strength.get_allele(is_random=True) * torb0.agility.get_allele(is_random=True))
        torb0_resilience = sqrt(torb0.health.get_allele(is_random=True) * torb0.defense.get_allele(is_random=True))
        torb1_power = sqrt(torb1.strength.get_allele(is_random=True) * torb1.agility.get_allele(is_random=True))
        torb1_resilience = sqrt(torb1.health.get_allele(is_random=True) * torb1.defense.get_allele(is_random=True))
        
        torb0_hit = random.uniform(1, torb0_power)
        torb0_protection = random.uniform(1, torb0_resilience)
        torb1_hit = random.uniform(1, torb1_power)
        torb1_protection = random.uniform(1, torb1_resilience)
        
        impact_torb0 = torb1_hit - torb0_protection
        impact_torb1 = torb0_hit - torb1_protection
        
        if impact_torb0 > 0:
            torb0.adjust_hp(-impact_torb0)
        if impact_torb1 > 0:
            torb1.adjust_hp(-impact_torb1)
        return
    
    def next_round(self, override: bool = False):
        from player import Player
        logging.info(f"{self.log_head()}: Calculating round results")
        unready = self.check_ready()
        if len(unready) > 0 and not override:
            unready_player_names = ', '.join([Player._instances[colony.PID].name for colony in unready])
            unready_colonies = ', '.join([colony.name for colony in unready])
            logging.error(f"{self.log_head()}: {unready_player_names} unready with colonies {unready_colonies}")
            raise SimulatorException(f"The following players' Colonies are not ready for the next round: {unready_player_names}.")

        for CID, colony in self.colonies.items():
            colony.new_round()
            colony.gather()
            
        combat_notice = self.combat()

        for CID, colony in self.colonies.items():
            colony.initiate_soldiers()
            colony.colony_meal()
            colony.breeding = []
            colony.resting = []
            colony.growing = []
            colony.attack_target = None
        self.year += 1
        logging.info(f"{self.log_head()}: Round complete")

        from ai_player import AIPlayer
        for PID, ai in AIPlayer._AI_instances.items():
            logging.debug(f"{self.log_head()}: Calling AI decisions for {ai.name}")
            ai.make_decisions()

        return combat_notice, self.year
    
    def log_head(self):
        return f"SID-{self.SID:02d}"
    
    def ready_all(self):
        logging.debug(f"{self.log_head()}: Forcibly readying all Colonies")
        for CID, colony in self.colonies.items():
            colony.ready = True
        logging.info(f"{self.log_head()}: Forcibly set all Colonies ready")
        return
    
    def global_scout(self):
        """Give basic scouting information on every Colony"""
        
        from colony import ArmyStats
        known_info = {}
        # Depending on how many colonies there are, this will be a very large output
        # Will need to add discord support for multiple pages in message or other form of compression
        search_colonies = [colony for CID, colony in self.colonies.items()]
        random.shuffle(search_colonies)
        for colony in search_colonies:
            army_stats = colony.army_info()
            known_info[colony.name] = army_stats
            
        return known_info

    def specific_scout(self, target_colony_CID):
        # May add other things here later, hidden-ness of the target colony, etc.
        return self.colonies[target_colony_CID].army_info()
        
    def check_ready(self):
        unready = []
        for CID, colony in self.colonies.items():
            if colony.ready == False:
                unready.append(colony)
        return unready