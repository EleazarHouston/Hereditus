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
        f"Jarl {name}"
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
    weak = ["Smallville", "Smallsville", "Droughtown", "Foodfree", "Weaklings", "Scraplings"]
    strong = ["Bulkland", "Gainstown", "Lifters", "Pressers", "Giants"]
    aggressive = ["Chasers", "Romans", "Barbarians"]
    passive = [""]
    retributive = [""]

    all_dispositions = {"weak": weak,
           "strong": strong,
           "aggressive": aggressive,
           "passive": passive,
           "retributive": retributive}
    
    if type == "random":
        type = random.choice(all_dispositions)
    random.shuffle(all_dispositions[type])
    return all_dispositions[type][0]

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
        "You have to harsher on your Torbs today, they were slacking.",
        "You barely have to give any instruction today, your Torbs are feeling productive.",
        "Your Torbs' weapons look very sharp today.",
        "Your Torbs' weapons look duller than they should.",
        ""
    ]
    random.shuffle(possibilities)
    return possibilities[0]