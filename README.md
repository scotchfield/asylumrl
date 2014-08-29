asylumrl
========

AsylumRL, a 7-day roguelike for 7drl2012.

Overview
--------

Hastily written in Python 2.6. Requires pygame (for the sound libraries) and libtcod (for the console rendering and much more).

Several sounds from the game were obtained from freesound.org and resampled:

 * "Barrel Break 1.wav" by kevinkace: http://www.freesound.org/people/kevinkace/sounds/66769/
 * "crash.wav" by sagetyrtle: http://www.freesound.org/people/sagetyrtle/sounds/40158/
 * "Heartbeat.wav" by jobro: http://www.freesound.org/people/jobro/sounds/74829/
 * "OhDearScare.wav" by TheGoliath: http://www.freesound.org/people/TheGoliath/sounds/124954/
 * "water step.wav" by nathanaelj83: http://www.freesound.org/people/nathanaelj83/sounds/145242/

Procedural cave generation is based on Jim Babcock's cellular automata method:  
http://roguebasin.roguelikedevelopment.org/index.php?title=Cellular_Automata_Method_for_Generating_Random_Cave-Like_Levels

Pythonic enums are taken from Alec Thomas's answer on stackoverflow:  
http://stackoverflow.com/questions/36932/whats-the-best-way-to-implement-an-enum-in-python  
Thank you for simplifying a lot of simple issues!  i didn't use enums in a truly efficient way in this 7drl, but this is very helpful code.