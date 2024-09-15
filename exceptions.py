# DEPRECATED
# THIS IS FROM THE OLD DISCORD VERSION OF THE GAME, BEFORE THE WEB-SERVER VERSION CHANGE

class HereditusException(Exception):
    """For all Hereditus Exceptions"""
    pass

class EvolutionEngineException(HereditusException):
    pass

class InvalidParents(EvolutionEngineException):
    pass

class PlayerException(HereditusException):
    pass

class TorbException(HereditusException):
    pass

class SimulatorException(HereditusException):
    pass

class ColonyException(HereditusException):
    pass