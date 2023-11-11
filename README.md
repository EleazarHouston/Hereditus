# Hereditus
Multiplayer chat-based genetics colony building game.

## Operation Sequence

### Initialize:
1) Simulator is created
2) Players join the game
3) AI Players are created
4) Colonies are created
5) Colonies are initialized with generation 0

### Round structure:
1) Scouts and armies are un-enlisted
2) Torb fertility is reset
3) Torbs are assigned to activities
4) Un-assigned Torbs gather food
5) Armies scout out other Colonies
6) Colonies choose their attack target
7) Colonies action order randomized and send armies to attack their targets
8) Colony meal