# Hereditus
Multiplayer web-based genetics colony-building game.

## Operation Sequence

### Round structure:
1) Players finish their actions and ready-up
2) Colony end-round order is randomized
3) Alive but infertile Torbs regain fertility
4) Torbs with 'gathering' action gather food
5) Juvenile Torbs grow into adults
6) Torbs with 'breeding' action sire the next generation of Torbs
7) Injured Torbs that didn't starve the previous year rest and heal
8) Ex-soldiers are removed from Armies
9) Armies scout out their scout targets
10) Armies attack their attack targets
11) Torbs with 'training' action join their new Armies
12) Torbs consume food if available, otherwise begin to starve
13) A new year & round begins

python manage.py runserver 0.0.0.0
cloudflared tunnel run hereditus