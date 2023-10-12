class HereditusException(Exception):
    """For all Hereditus Exceptions"""
    pass

class EvolutionEngineException(HereditusException):
    pass

class InvalidParents(EvolutionEngineException):
    pass

class PlayerException(HereditusException):
    pass