# DEPRECATED
# THIS IS FROM THE OLD DISCORD VERSION OF THE GAME, BEFORE THE WEB-SERVER VERSION CHANGE

import random

def player_strings(name):
    # May want to add positive, negative, and moderate strings later
    # Depending on how well-fed the torbs are, and how many torbs
    # have died recently, to mock colony's feelings toward the player
    possibilities = [
        "my Liege",
        "your Highness",
        f"{name} the Great",
        f"esteemed {name}",
        f"distinguished {name}",
        "magnificent Ruler",
        "my Sovereign",
        f"Chancellor {name}",
        f"Jarl {name}",
        f"noble {name}",
        f"exalted {name}",
        f"my Regent",
        f"Sage Ruler",
        f"majestic Overseer",
        f"High Steward {name}",
        f"eminent {name}",
        f"oh revered {name}",
        f"oh wise Protector",
        f"Prime Arbiter {name}"
    ]
    random.shuffle(possibilities)
    return possibilities[0]

def colony_strings(name):
    # May want to add logic later for positive and negative names,
    # according to how well the civilization is doing
    possibilities = [
        "your grand civilization",
        f"{name}",
        f"the magnificent {name}",
        f"{name}, the height of civilization,",
        f"{name}, the jewel of the world",
        f"{name}, the fertile land",
    ]
    random.shuffle(possibilities)
    return possibilities[0]

def torb_strings(name):
    #May need more advanced logic for changing names based on torb genes or number of children
    # i.e. "[X] the strong", "[X] the fertile"
    # Should be weighted according to most 'memorable' part of each torb
    return

def torb_names():
    possibilities = [
        "Aahl", "Abry", "Acla", "Adz", "Aev", "Aft", "Agor", "Ahm", "Aix", "Ajr", "Ake", "Alaz", "Amo", "Ant", "Aolt", "Apra", "Aquu", "Arr", "Asmo", "Atby", "Augo", "Avo", "Awre", "Axad", "Ayo", "Azzy",
        "Ba", "..."
    ]
    random.shuffle(possibilities)
    return possibilities[0]

def AI_names(type):
    #types = ["weak", "strong", "aggressive", "passive", "retributive"]
    weak = ["Fragileton", 
            "Faintville",
            "Droughttown",
            "Foodfree",
            "Weaklings",
            "Scraplings",
            "Brittleburg",
            "Meekshire",
            "Tenderland"]
    
    strong = ["Bulkland",
              "Gainstown",
              "Lifters",
              "Pressers",
              "Giants",
              "Ironhold",
              "Steelhaven",
              "Rockgard",
              "Fortitude"]
    
    aggressive = ["Chasers",
                  "Romans",
                  "Barbarians",
                  "Warland",
                  "Furytown",
                  "Raidridge",
                  "Blitzville",
                  "Strikefield"]
    
    passive = ["Sleepers",
               "Sleepyville",
               "Watchers",
               "Waiters",
               "Observers",
               "Quietude",
               "Peaceville",
               "Calmharbor",
               "Breezefield"]
    
    retributive = ["Elephants",
                   "Brutusites",
                   "Backtoyou",
                   "Postals",
                   "Grudgehaven",
                   "Vengefort"]
    
    all = weak + strong + aggressive + passive + retributive
    all_dispositions = {"weak": weak,
           "strong": strong,
           "aggressive": aggressive,
           "passive": passive,
           "retributive": retributive}
    
    if type == "random":
        type = random.choice(list(all_dispositions.keys()))
    out = random.choice(all_dispositions[type])
    print(f"Returning AI_name {out}")
    return out
    

def random_event():
    # These have no impact, they are merely fluff
    possibilities = [
        "The sun warms your Torbs' backs.",
        "A crow flies overhead.",
        "The wind picks up.",
        "A wolf howls in the distance.",
        "Sounds of hammers and saws are heard through the colony.",
        "You get a feeling that good times are coming.",
        "You get a feeling that bad times are coming.",
        "Plumes of smoke rise in the distance.",
        "The sound of distant weapons clashing echoes through your colony.",
        "A bear is seen at the edge of the forest.",
        "Your Torbs have to shoo raccoons away from your food stores.",
        "The sound of birds chirping raise your spirits.",
        "The clouds foretell of a telling victory in battle in the near future.",
        "The clouds foretell of a telling defeat in battle in the near future.",
        "Lightning in the distance spooks one of your Torbs.",
        "Your Torbs seem slightly more fond of you today than usual.",
        "Your Torbs seem slightly less fond of you today than usual.",
        "One of your Torbs seems taller today.",
        "One of your Torbs seems shorter today.",
        "The sun is surprisingly bright today.",
        "The sun is darker today than usual.",
        "Your Torbs seem happy today.",
        "Your Torbs seem sad today.",
        "Today's meal tasted delicious.",
        "Today's meal was quite bland.",
        "You have to be harsher on your Torbs today, they were slacking.",
        "You barely have to give any instruction today, your Torbs are feeling productive.",
        "Your Torbs' weapons look very sharp today.",
        "Your Torbs' weapons look duller than they should.",
        "A gentle breeze carries the scent of wildflowers.",
        "A kaleidoscope of butterflies flutters through your colony.",
        "A small bird lands nearby, observing you curiously.",
        "Dew glistens on the grass in the early morning light.",
        "A playful squirrel scampers across your path.",
        "The moon seems unusually large tonight.",
        "The moon seems unusually small tonight.",
        "You find an oddly shaped rock that looks like a smiling face.",
        "You find an oddly shaped rock that looks like a frowning face.",
        "You find an oddly shaped tree branch that looks like a trident.",
        "You find an oddly shaped tree branch that looks like a trumpet.",
        "Your shadow is particularly amorphous today.",
        "A cool mist rolls in from the nearby hills.",
        "A small frog leaps into a pond as you approach.",
        "The leaves rustle softly as if whispering secrets to each other.",
        "A shooting star streaks across the sky.",
        "An old tree creaks gently in the wind.",
        "A friendly bee buzzes around you before fly away.",
        "A cloud overhead looks remarkably like a portal you once saw.",
        "You spot two birds playfully chasing each other.",
        "The sun casts long, dramatic shadows as it sets.",
        "You feel a tap on your shoulder, but when you turn no one is there.",
        "The day is unnaturally quiet today.",
        "You hear the sound of a distant waterfall."
    ]
    random.shuffle(possibilities)
    return possibilities[0]

def winner_adjectives():
    possibilities = [
        "mighty",
        "fearsome",
        "awe-inspiring",
        "fear-inducing",
        "tremendous",
        "battle-hardened",
        "experienced",
        "well-trained",
        "quick-footed",
        "well-prepared",
        "heroic",
        "coordinated",
        "renowned",
        "unyielding",
        "impressive",
        "opportunistic",
        "prolific"
    ]
    random.shuffle(possibilities)
    return possibilities[0]

def loser_adjectives():
    possibilities = [
        "feeble",
        "uncoordinated",
        "fearful",
        "unimpressive",
        "underprepared",
        "inexperienced",
        "lead-footed",
        "puny",
        "outmatched",
        "overwhelmed",
        "disorganized",
        "frail",
        "disheartened",
        "weakened",
        "panicked",
        "inept",
        "clumsy",
        "battered",
        "subdued",
        "beleaguered"        
    ]
    random.shuffle(possibilities)
    return possibilities[0]

def ready_message(name):
    possibilities = [
        f"{name}'s Torbs are well-prepared for whatever happens next.",
        f"The Colony lead by {name} stands vigilant and ready.",
        f"{name}'s Colony has completed its preparations.",
        f"Ready is the name of the game in {name}'s Colony.",
        f"All is in order at {name}'s Colony, awaiting the next challenge.",
        f"Steadfast and prepared, {name}'s Colony awaits what's to come.",
        f"The Torbs in {name}'s Colony brace themselves for the future.",
        f"Alert and poised, {name}'s Torbs stand ready.",
        f"Everything in {name}'s Colony is set, eyes on the horizon.",
        f"{name}'s Torbs are fully prepared.",
        f"Anticipation builds in {name}'s Colony as they wait for danger.",
        f"With preparations complete, {name}'s Torbs look to the future.",
        f"The groundwork is laid, and {name}'s Colony is ready for new prospects.",
        f"The stage is set for {name}'s Colony to embrace their next adventure.",
        f"Readiness resonates through the ranks of {name}'s Torbs.",
        f"A sense of preparedness envelops the atmosphere in {name}'s Colony.",
        f"Eyes forward is the motto in {name}'s Colony.",
        f"Look to the future is the rallying cry from {name}'s Torbs.",
        f"The adrenaline is pumping in {name}'s Torbs, they're ready to rock.",
        f"A pulse of readiness surges through {name}'s Torbs.",
        f"Like a well-oiled machine, {name}'s Colony hums with preparedness.",
        f"The anticipation of what will come next fuels the spirit in {name}'s Colony.",
        f"For {name}'s Torbs, readiness is the shield against the unknown.",
        f"In {name}'s Colony, the gears of readiness are always turning."
    ]
    random.shuffle(possibilities)
    return possibilities[0]