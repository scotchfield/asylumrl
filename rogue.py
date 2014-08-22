'''
asylumRL by scotchfield
http://scootah.com/asylumrl

requires python2.x, pygame, and libtcod
headphones would also be nice!
'''

#import cProfile
import math
import os
import pygame
import random
import libtcodpy as libtcod

# http://stackoverflow.com/questions/36932/whats-the-best-way-to-implement-an-enum-in-python
def enum(*sequential, **named):
    enums = dict(zip(sequential, range(len(sequential))), **named)
    return type('Enum', (), enums)

Tokens = enum(
    'PLAYER', 'WALL', 'ASYLUM_DOOR', 'ASYLUM_DIRTY_PUDDLE', 'ASYLUM_CORRIDOR_END',
    'ASYLUM_BED_FRAME', 'ASYLUM_BED_MATTRESS', 'ASYLUM_TOILET', 'ASYLUM_CORPSE',
    'ASYLUM_STAIRCASE', 'BLUEPILL', 'CAVE_STAIRCASE', 'CAVE_KEY', 'INIT_STALKER', 'STALKER',
    'STORY_1', 'STORY_2', 'STORY_3', 'STORY_4', 'STORY_5', 'STORY_6', 'STORY_7', 'STORY_8', 
    'STORY_9', 'STORY_0', 'SEWAGE_EXIT', 'CHAIN_FENCE', 'RUSTED_MANHOLE',
    'NEWS_1', 'NEWS_2', 'NEWS_3', 'NEWS_4', 'NEWS_5', )

Directions = enum('NORTH', 'SOUTH', 'EAST', 'WEST')

stalker_token_obj = ['.', ',', ':', ';', '*', '(', ')']
story_enum_obj = [Tokens.STORY_1, Tokens.STORY_2, Tokens.STORY_3, Tokens.STORY_4, Tokens.STORY_5,
    Tokens.STORY_6, Tokens.STORY_7, Tokens.STORY_8, Tokens.STORY_9, Tokens.STORY_0]
news_enum_obj = [Tokens.NEWS_1, Tokens.NEWS_2, Tokens.NEWS_3, Tokens.NEWS_4, Tokens.NEWS_5]

def getConsoleText(token_enum):
    st = False
    if Tokens.ASYLUM_DOOR == token_enum:
        v = random.randint(0, 2)
        if v == 0:
            st = 'You kick the rotted door open.'
        elif v == 1:
            st = 'You crash through the rotting door.'
        elif v == 2:
            st = 'The door buckles easily as you kick it open.'
    elif Tokens.ASYLUM_BED_FRAME == token_enum:
        st = 'The bedframe is rusted, and creaks at your touch.'
    elif Tokens.ASYLUM_BED_MATTRESS == token_enum:
        st = 'This soiled mattress is covered in a fine dust coating.'
    elif Tokens.ASYLUM_TOILET == token_enum:
        st = 'A foul smelling toilet filled with rancid water.'
    elif Tokens.ASYLUM_CORPSE == token_enum:
        v = random.randint(0, 2)
        if v == 0:
            st = 'You see a rotted corpse lying on the room\'s floor.'
        elif v == 1:
            st = 'A rotting corpse rests on the floor of the room.'
        elif v == 2:
            st = 'There is a rotting corpse on the floor of this room.'
    elif Tokens.ASYLUM_STAIRCASE == token_enum:
        st = 'Press \'e\' to descend further into the asylum.'
    elif Tokens.BLUEPILL == token_enum:
        st = 'A blue sedative rests on the ground. Press \'e\' to take it.'
    elif Tokens.CAVE_STAIRCASE == token_enum:
        st = 'Press \'e\' to descend further into the asylum.'
    elif Tokens.CAVE_KEY == token_enum:
        st = 'A small brass key. Press \'e\' to take it.'
    elif Tokens.STALKER == token_enum:
        v = random.randint(0, 2)
        if v == 0:
            st = 'Oh god, what is that thing?'
        elif v == 1:
            st = 'What is that horrible thing?  Run!'
        elif v == 2:
            st = 'Dear god, get away from that thing!'
    elif token_enum in story_enum_obj:
        st = 'You see a page from your journal. Press \'e\' to take it.'
    elif Tokens.SEWAGE_EXIT == token_enum:
        st = 'An old sewage line. You can escape the asylum with this!'
    elif Tokens.RUSTED_MANHOLE == token_enum:
        st = 'The rusted manhole you used to escape the asylum.'
    elif token_enum in news_enum_obj:
        st = 'You see a discarded news article. Press \'e\' to read it.'
    return st


class GameObject(object):
    def __init__(self, token_enum, x, y, colour, token, blocking, obscuring, observed):
        self.token_enum = token_enum
        self.x = x
        self.y = y
        self.colour = colour
        self.token = token
        self.blocking = blocking
        self.obscuring = obscuring
        self.observed = observed

class GameTransition(GameObject):
    def setTransition(self, map_id, map_x, map_y):
        self.map_id = map_id
        self.map_x = map_x
        self.map_y = map_y

    def __init__(self, token_enum, x, y, colour, token):
        super(GameTransition, self).__init__(token_enum, x, y, colour, token, False, False, False)
        self.map_id = ''
        self.map_x = 0
        self.map_y = 0

class GameStalker(GameObject):
    def setMap(self, map_id):
        self.map = map_id

    def updateMapFov(self, map):
        self.map_fov = map.getFovFromTiles(map.getMap(self.map_id)['tiles'])

    def update(self, player, map, console, sound_obj):
        move_x = False
        move_y = False
        libtcod.map_compute_fov(self.map_fov, self.x, self.y,
            radius=self.fov, light_walls=True, algo=libtcod.FOV_BASIC)
        if libtcod.map_is_in_fov(self.map_fov, player.x, player.y):
            map_path = libtcod.path_new_using_map(self.map_fov, dcost=0.0)
            path = libtcod.path_compute(map_path, self.x, self.y, player.x, player.y)
            if path:
                if libtcod.path_size(map_path) == 0:
                    return True
                if random.randint(0, 5) > 0:
                    move_x, move_y = libtcod.path_get(map_path, 0)
        if move_x is False:
            stroll_x = 0
            stroll_y = 0
            if random.randint(0, 1) == 0:
                stroll_x = random.choice([1, -1])
            else:
                stroll_y = random.choice([1, -1])
            if libtcod.map_is_walkable(self.map_fov, self.x + stroll_x, self.y + stroll_y):
                move_x = self.x + stroll_x
                move_y = self.y + stroll_y
        if move_x is not False:
            self.x = move_x
            self.y = move_y
        if self.x == player.x and self.y == player.y:
            return True
        return False

    def __init__(self, x, y, map, map_id, fov):
        super(GameStalker, self).__init__(Tokens.STALKER, x, y,
            libtcod.Color(255, 255, 255), 's', False, True, False)
        self.fov = fov
        self.map_id = map_id
        self.map_fov = map.getFovFromTiles(map.getMap(self.map_id)['tiles'])

class GamePlayer(GameObject):
    def setMap(self, map_id):
        self.map = map_id
        self.has_key = False

    def addSanity(self, x, max_sanity, console, sound_obj):
        #if self.sanity < 1000 and self.sanity + x >= 1000:
        #    sound_obj['heartbeat'].stop()
        self.sanity = min(self.sanity + x, max_sanity)
        st = self.updateFov()
        if st is not False:
            console.append(st)

    def loseSanity(self, x, min_sanity, console, sound_obj):
        sound_obj['heartbeat'].set_volume(max(1.0 - float(self.sanity) / 1500.0, 0))
        self.sanity = max(self.sanity - x, min(min_sanity, self.sanity))
        st = self.updateFov()
        if st is not False:
            console.append(st)

    def addInventory(self, token_id, n):
        self.inventory[token_id] = self.inventory.get(token_id, 0) + n

    def removeInventory(self, token_id, n):
        self.inventory[token_id] = max(0, self.inventory.get(token_id, 0) - n)

    def getInventory(self, token_id):
        return self.inventory.get(token_id, 0)

    def updateFov(self, return_string=True):
        self.oldfov = self.fov
        self.fov = int(float(self.sanity) / 200.0) + 5
        if not return_string:
            self.oldfov = self.fov
            return False
        if self.fov < self.oldfov:
            sanity_obj = [
                'It\'s getting colder down here..',
                'Did it just get darker?  My mind is playing tricks..',
                'What was that noise?',
                'Is someone whispering?',
                'I think I can hear someone else down here..',
            ]
            return random.choice(sanity_obj)
        elif self.fov > self.oldfov:
            sanity_obj = [
                'That feels better..',
                'I think it\'s getting brighter..',
                'I hope this helps shut out the whispering voices..',
            ]
            return random.choice(sanity_obj)
        return False

    def __init__(self, x, y):
        super(GamePlayer, self).__init__(Tokens.PLAYER, x, y,
            libtcod.Color(255, 255, 0), '@', False, False, False)
        self.sanity = 1050
        self.fov = 0
        self.updateFov(return_string=False)
        self.inventory = {}
        self.turn = 0
        self.tick = 0
        self.has_key = False
        self.blackout = 0
        self.dead = 0
        self.pages = {}
        self.news = {}

def getDictMapFromTiles(map):
    d = {}
    for k in map:
        if k.y not in d:
            d[k.y] = {}
        d[k.y][k.x] = k
    return d

class Map(object):
    def addMap(self, map_id, map):
        self.maps[map_id] = {'tiles': map}
        self.maps[map_id]['stalker_obj'] = []
        self.updateMap(map_id)

    def getFovFromTiles(self, map):
        max_x = 0
        max_y = 0
        for k in map:
            max_x = max(max_x, k.x)
            max_y = max(max_y, k.y)
        fov = libtcod.map_new(max_x + 1, max_y + 1)
        libtcod.map_clear(fov, True, True)
        for k in map:
            transparent = True
            walkable = True
            if k.obscuring:
                transparent = False
            if k.blocking:
                walkable = False
            libtcod.map_set_properties(fov, k.x, k.y, transparent, walkable)
        return fov

    def updateMap(self, map_id):
        self.maps[map_id]['d'] = getDictMapFromTiles(self.maps[map_id]['tiles'])
        self.maps[map_id]['fov'] = self.getFovFromTiles(self.maps[map_id]['tiles'])

    def computeFov(self, player):
        libtcod.map_compute_fov(self.maps[player.map]['fov'], player.x, player.y,
            radius=player.fov, light_walls=True, algo=libtcod.FOV_BASIC)

    def addStalker(self, map_id, fov):
        if map_id not in self.maps:
            return
        map = self.maps[map_id]['tiles']
        for obj in map:
            if obj.token_enum == Tokens.INIT_STALKER:
                map.remove(obj)
                stalker = GameStalker(obj.x, obj.y, self, map_id, fov)
                map.append(stalker)
                self.maps[map_id]['stalker_obj'].append(stalker)
        self.updateMap(map_id)

    def getMap(self, map_id):
        return self.maps[map_id]

    def __init__(self):
        self.maps = {}


def loadSounds():
    sound_obj = {}
    sound_obj['water-step'] = pygame.mixer.Sound('sounds\\water-step.wav')
    sound_obj['barrel-break'] = pygame.mixer.Sound('sounds\\barrel-break.wav')
    sound_obj['whisper-1'] = pygame.mixer.Sound('sounds\\whisper-1.wav')
    sound_obj['whisper-2'] = pygame.mixer.Sound('sounds\\whisper-2.wav')
    sound_obj['ohdearscare'] = pygame.mixer.Sound('sounds\\ohdearscare.wav')
    sound_obj['heartbeat'] = pygame.mixer.Sound('sounds\\heartbeat.wav')
    sound_obj['crash'] = pygame.mixer.Sound('sounds\\crash.wav')
    return sound_obj

def getWall(x, y):
    return GameObject(Tokens.WALL, x, y, libtcod.Color(255, 255, 255), '#', True, True, False)

def getFence(x, y):
    return GameObject(Tokens.CHAIN_FENCE, x, y, libtcod.Color(170, 170, 170), '#', True, False, False)

def getPuddle(x, y):
    puddle_colour = random.randint(1, 3)
    if puddle_colour == 1:
        puddle_colour = libtcod.Color(96, 128, 0)
    elif puddle_colour == 2:
        puddle_colour = libtcod.Color(0, 128, 64)
    else:
        puddle_colour = libtcod.Color(128, 128, 0)
    return GameObject(Tokens.ASYLUM_DIRTY_PUDDLE, x, y, puddle_colour, '_', False, False, False)

def getMapObject(map, x, y):
    if y in map:
        if x in map[y]:
            return map[y][x]
    return False

def getMapTileObject(map, x, y):
    for k in map:
        if k.x == x and k.y == y:
            return k
    return False

def getFreeMapLocation(map, width, height):
    x = random.randint(0, width)
    y = random.randint(0, height)
    obj = getMapObject(map, x, y)
    while obj:
        x = random.randint(0, width)
        y = random.randint(0, height)
        obj = getMapObject(map, x, y)
    return (x, y)

def buildRandomPartitionRooms(map, depth, x_divide, xa, ya, xb, yb, room_points):
    divide_room = depth > 0
    if depth == 2:
        if random.randint(1, 6) == 1:
            divide_room = False
    elif depth == 1:
        if random.randint(1, 3) == 1:
            divide_room = False
    if divide_room:
        if x_divide:
            mid = int((xa + xb) / 2) + random.randint(-4, 4)
            buildPartitionRooms(map, depth - 1, not x_divide, xa, ya, mid - 1, yb, room_points)
            buildPartitionRooms(map, depth - 1, not x_divide, mid + 1, ya, xb, yb, room_points)
            room_delta = (1, 0)
        else:
            mid = int((ya + yb) / 2) + random.randint(-4, 4)
            buildPartitionRooms(map, depth - 1, not x_divide, xa, ya, xb, mid - 1, room_points)
            buildPartitionRooms(map, depth - 1, not x_divide, xa, mid + 1, xb, yb, room_points)
            room_delta = (0, 1)
    else:
        room_variant = 0.3
        x_width = xb - xa
        y_width = yb - ya
        xa += int(x_width * random.uniform(0, room_variant))
        xb -= int(x_width * random.uniform(0, room_variant))
        ya += int(y_width * random.uniform(0, room_variant))
        yb -= int(y_width * random.uniform(0, room_variant))
        for i in range(xa + 1, xb):
            map.append(getWall(i, ya))
            map.append(getWall(i, yb))
        for i in range(ya, yb + 1):
            map.append(getWall(xa, i))
            map.append(getWall(xb, i))
        room_points.append((int((xb - xa) / 2)), int((yb - ya) / 2))

def buildPartitionRooms(map, depth, x_split, xa, ya, xb, yb, door_right=False, vars={}):
    vars['rooms'] = vars.get('rooms', 0)
    vars['pages'] = vars.get('pages', 0)
    if depth > 0:
        if x_split:
            mid = int((xa + xb) / 2)# + random.randint(-4, 4)
            buildPartitionRooms(map, depth - 1, False, xa, ya, mid - 1, yb, door_right = True, vars = vars)
            buildPartitionRooms(map, depth - 1, False, mid + 1, ya, xb, yb, door_right = False, vars = vars)
            map.append(GameObject(Tokens.ASYLUM_CORRIDOR_END,
                mid, ya, libtcod.Color(255, 255, 255), Directions.NORTH, False, False, False))
            map.append(GameObject(Tokens.ASYLUM_CORRIDOR_END,
                mid, yb, libtcod.Color(255, 255, 255), Directions.SOUTH, False, False, False))
        else:
            mid = int((ya + yb) / 2)# + random.randint(-4, 4)
            buildPartitionRooms(map, depth - 1, False, xa, ya, xb, mid - 1, door_right, vars = vars)
            buildPartitionRooms(map, depth - 1, False, xa, mid + 1, xb, yb, door_right, vars = vars)
            if door_right:
                map.append(GameObject(Tokens.ASYLUM_CORRIDOR_END,
                    xa, mid, libtcod.Color(255, 255, 255), Directions.WEST, True, False, False))
            else:
                map.append(GameObject(Tokens.ASYLUM_CORRIDOR_END,
                    xb, mid, libtcod.Color(255, 255, 255), Directions.EAST, True, False, False))
    else:
        vars['rooms'] += 1
        for i in range(xa + 1, xb):
            map.append(getWall(i, ya))
            map.append(getWall(i, yb))
        for i in range(ya, yb + 1):
            map.append(getWall(xa, i))
            map.append(getWall(xb, i))
        for i in range(random.randint(2, 5)):
            puddle_colour = random.randint(1, 3)
            if puddle_colour == 1:
                puddle_colour = libtcod.Color(96, 128, 0)
            elif puddle_colour == 2:
                puddle_colour = libtcod.Color(0, 128, 64)
            else:
                puddle_colour = libtcod.Color(128, 128, 0)
            map.append(GameObject(Tokens.ASYLUM_DIRTY_PUDDLE,
                random.randint(xa + 1, xb - 1), random.randint(ya + 1, yb - 1),
                puddle_colour, '_', False, False, False))
        if door_right:
            map.remove(getMapTileObject(map, xb, ya + 2))
            map.append(GameObject(Tokens.ASYLUM_DOOR,
                xb, ya + 2, libtcod.Color(255, 255, 255), '|', True, True, False))
            bed_top = random.randint(0, 1)
            if bed_top:
                bed_top = ya + 1
                toilet_top = yb - 1
            else:
                bed_top = yb - 1
                toilet_top = ya + 1
            map.append(GameObject(Tokens.ASYLUM_BED_FRAME,
                xa + 1, bed_top, libtcod.Color(183, 65, 14), '|', True, False, False))
            map.append(GameObject(Tokens.ASYLUM_BED_FRAME,
                xa + 4, bed_top, libtcod.Color(183, 65, 14), '|', True, False, False))
            map.append(GameObject(Tokens.ASYLUM_BED_MATTRESS,
                xa + 2, bed_top, libtcod.Color(222, 221, 195), '=', True, False, False))
            map.append(GameObject(Tokens.ASYLUM_BED_MATTRESS,
                xa + 3, bed_top, libtcod.Color(222, 221, 195), '=', True, False, False))
            map.append(GameObject(Tokens.ASYLUM_TOILET,
                xa + 1, toilet_top, libtcod.Color(191, 151, 96), 'O', True, False, False))
        else:
            map.remove(getMapTileObject(map, xa, yb - 2))
            map.append(GameObject(Tokens.ASYLUM_DOOR,
                xa, yb - 2, libtcod.Color(255, 255, 255), '|', True, True, False))
            bed_top = random.randint(0, 1)
            if bed_top:
                bed_top = ya + 1
                toilet_top = yb - 1
            else:
                bed_top = yb - 1
                toilet_top = ya + 1
            map.append(GameObject(Tokens.ASYLUM_BED_FRAME,
                xb - 1, bed_top, libtcod.Color(183, 65, 14), '|', True, False, False))
            map.append(GameObject(Tokens.ASYLUM_BED_FRAME,
                xb - 4, bed_top, libtcod.Color(183, 65, 14), '|', True, False, False))
            map.append(GameObject(Tokens.ASYLUM_BED_MATTRESS,
                xb - 2, bed_top, libtcod.Color(222, 221, 195), '=', True, False, False))
            map.append(GameObject(Tokens.ASYLUM_BED_MATTRESS,
                xb - 3, bed_top, libtcod.Color(222, 221, 195), '=', True, False, False))
            map.append(GameObject(Tokens.ASYLUM_TOILET,
                xb - 1, toilet_top, libtcod.Color(191, 151, 96), 'O', True, False, False))
        gen_body = False
        gen_bluepill = False
        if ya > 10:
            if random.randint(0, 4) == 0:
                gen_body = True
        if random.randint(0, 2) == 0:
            gen_bluepill = True
        while gen_body:
            bx = random.randint(xa + 1, xb - 1)
            by = random.randint(ya + 1, yb - 1)
            if not getMapTileObject(map, bx, by):
                map.append(GameObject(Tokens.ASYLUM_CORPSE,
                    bx, by, libtcod.Color(128, 0, 0), '@', False, False, False))
                gen_body = False
        while gen_bluepill:
            bx = random.randint(xa + 1, xb - 1)
            by = random.randint(ya + 1, yb - 1)
            if not getMapTileObject(map, bx, by):
                map.append(GameObject(Tokens.BLUEPILL,
                    bx, by, libtcod.Color(0, 95, 191), 'o', False, False, False))
                gen_bluepill = False
        gen_page = random.randint(0, 3) == 0
        if vars['pages'] < 4 and vars['rooms'] + 4 - vars['pages'] == 16:
            gen_page = True
        if vars['pages'] == 4:
            gen_page = False
        if gen_page:
            page_token = Tokens.STORY_1
            if vars['pages'] == 1:
                page_token = Tokens.STORY_2
            elif vars['pages'] == 2:
                page_token = Tokens.STORY_3
            elif vars['pages'] == 3:
                page_token = Tokens.STORY_4
            while gen_page:
                bx = random.randint(xa + 1, xb - 1)
                by = random.randint(ya + 1, yb - 1)
                if not getMapTileObject(map, bx, by):
                    map.append(GameObject(page_token,
                        bx, by, libtcod.Color(255, 255, 115), '(', False, False, False))
                    gen_page = False
            vars['pages'] += 1

def buildAsylumCommonRooms(map, depth, y_split, xa, ya, xb, yb, door_bottom=False, vars={}):
    vars['rooms'] = vars.get('rooms', 0)
    vars['pages'] = vars.get('pages', 0)
    if depth > 0:
        if y_split:
            mid = int((ya + yb) / 2) + random.randint(-3, 3)
            buildAsylumCommonRooms(map, depth - 1, False, xa, ya, xb, mid - 1,
                door_bottom = True, vars = vars)
            buildAsylumCommonRooms(map, depth - 1, False, xa, mid + 1, xb, yb,
                door_bottom = False, vars = vars)
            map.append(GameObject(Tokens.ASYLUM_CORRIDOR_END,
                xa, mid, libtcod.Color(255, 255, 255), Directions.EAST, False, False, False))
            map.append(GameObject(Tokens.ASYLUM_CORRIDOR_END,
                xb, mid, libtcod.Color(255, 255, 255), Directions.WEST, False, False, False))
        else:
            mid = int((xa + xb) / 2) + random.randint(-4, 4)
            buildAsylumCommonRooms(map, depth - 1, False, xa, ya, mid - 1, yb,
                door_bottom, vars = vars)
            buildAsylumCommonRooms(map, depth - 1, False, mid + 1, ya, xb, yb,
                door_bottom, vars = vars)
            if door_bottom:
                map.append(GameObject(Tokens.ASYLUM_CORRIDOR_END,
                    mid, ya, libtcod.Color(255, 255, 255), Directions.NORTH, True, False, False))
            else:
                map.append(GameObject(Tokens.ASYLUM_CORRIDOR_END,
                    mid, yb, libtcod.Color(255, 255, 255), Directions.SOUTH, True, False, False))
    else:
        vars['rooms'] += 1
        for i in range(random.randint(4, 7)):
            puddle_colour = random.randint(1, 3)
            if puddle_colour == 1:
                puddle_colour = libtcod.Color(96, 128, 0)
            elif puddle_colour == 2:
                puddle_colour = libtcod.Color(0, 128, 64)
            else:
                puddle_colour = libtcod.Color(128, 128, 0)
            map.append(GameObject(Tokens.ASYLUM_DIRTY_PUDDLE,
                random.randint(xa + 1, xb - 1), random.randint(ya + 1, yb - 1),
                puddle_colour, '_', False, False, False))
        for i in range(xa + 1, xb):
            map.append(getWall(i, ya))
            map.append(getWall(i, yb))
        for i in range(ya, yb + 1):
            map.append(getWall(xa, i))
            map.append(getWall(xb, i))
        if door_bottom:
            door_x = random.randint(xa + 1, xb - 1)
            map.remove(getMapTileObject(map, door_x, yb))
            map.append(GameObject(Tokens.ASYLUM_DOOR,
                door_x, yb, libtcod.Color(255, 255, 255), '-', True, True, False))
        else:
            door_x = random.randint(xa + 1, xb - 1)
            map.remove(getMapTileObject(map, door_x, ya))
            map.append(GameObject(Tokens.ASYLUM_DOOR,
                door_x, ya, libtcod.Color(255, 255, 255), '-', True, True, False))
        gen_body = False
        gen_bluepill = False
        if random.randint(0, 4) == 0:
            gen_body = True
        if random.randint(0, 3) == 0:
            gen_bluepill = True
        while gen_body:
            bx = random.randint(xa + 1, xb - 1)
            by = random.randint(ya + 1, yb - 1)
            if not getMapTileObject(map, bx, by):
                map.append(GameObject(Tokens.ASYLUM_CORPSE,
                    bx, by, libtcod.Color(128, 0, 0), '@', False, False, False))
                gen_body = False
        while gen_bluepill:
            bx = random.randint(xa + 1, xb - 1)
            by = random.randint(ya + 1, yb - 1)
            if not getMapTileObject(map, bx, by):
                map.append(GameObject(Tokens.BLUEPILL,
                    bx, by, libtcod.Color(0, 95, 191), 'o', False, False, False))
                gen_bluepill = False
        gen_page = random.randint(0, 2) == 0
        if vars['pages'] < 2 and vars['rooms'] + 2 - vars['pages'] == 8:
            gen_page = True
        if vars['pages'] == 2:
            gen_page = False
        if gen_page:
            page_token = Tokens.STORY_5
            if vars['pages'] == 1:
                page_token = Tokens.STORY_6
            while gen_page:
                bx = random.randint(xa + 1, xb - 1)
                by = random.randint(ya + 1, yb - 1)
                if not getMapTileObject(map, bx, by):
                    map.append(GameObject(page_token,
                        bx, by, libtcod.Color(255, 255, 115), '(', False, False, False))
                    gen_page = False
            vars['pages'] += 1

def generateAsylumMap(width, height):
    map = []
    buildPartitionRooms(map, 4, True, 0, 0, width, height)
    corridors = []
    for x in map:
        if Tokens.ASYLUM_CORRIDOR_END == x.token_enum:
            corridors.append(x)
    for obj in corridors:
        map.remove(obj)
        if obj.token is Directions.SOUTH:
            # TODO: SOUTH CAN ALWAYS BE THE STAIRS TO THE LOWER ASYLUM
            map.append(getWall(obj.x-1, obj.y+1))
            map.append(getWall(obj.x, obj.y+1))
            map.append(getWall(obj.x+1, obj.y+1))
            map.append(GameTransition(Tokens.ASYLUM_STAIRCASE, obj.x, obj.y,
                libtcod.Color(120, 120, 120), '>'))
        elif obj.token is Directions.EAST:
            map.append(getWall(obj.x, obj.y))
        else:
            map.append(getWall(obj.x, obj.y))
    return map

def generateAsylumCommonMap(width, height, asylum_map):
    map = []
    buildAsylumCommonRooms(map, 3, True, 1, 0, width, height)
    corridors = []
    for x in map:
        if Tokens.ASYLUM_CORRIDOR_END == x.token_enum:
            corridors.append(x)
    for obj in corridors:
        map.remove(obj)
        if obj.token is Directions.EAST:
            map.append(getWall(obj.x-1, obj.y-1))
            map.append(getWall(obj.x-1, obj.y))
            map.append(getWall(obj.x-1, obj.y+1))
            for x in asylum_map['tiles']:
                if Tokens.ASYLUM_STAIRCASE == x.token_enum:
                    x.setTransition('asylumcommon', obj.x, obj.y)
        elif obj.token is Directions.WEST:
            map.append(getWall(obj.x+1, obj.y-1))
            map.append(getWall(obj.x+1, obj.y))
            map.append(getWall(obj.x+1, obj.y+1))
            map.append(GameTransition(Tokens.ASYLUM_STAIRCASE, obj.x, obj.y,
                libtcod.Color(120, 120, 120), '>'))
        else:
            map.append(getWall(obj.x, obj.y))
    return map

def getMapDictNeighbours(map, x, y, dist):
    n = 0
    for i in range(x - dist, x + dist + 1):
        for j in range(y - dist, y + dist + 1):
            if getMapObject(map, i, j):
                n += 1
    return n

def getMapTileNeighbours(map, x, y, dist):
    n = 0
    for i in range(x - dist, x + dist + 1):
        for j in range(y - dist, y + dist + 1):
            if getMapTileObject(map, i, j):
                n += 1
    return n

def getMapWallNeighbours(map, x, y, dist):
    n = 0
    for i in range(x - dist, x + dist + 1):
        for j in range(y - dist, y + dist + 1):
            if j in map and i in map[j]:
                n += 1
    return n

def getMapWallFromTiles(map):
    w = {}
    for k in map:
        if k.y not in w:
            w[k.y] = {}
        w[k.y][k.x] = True
    return w

def getMapTilesFromWall(w):
    m = []
    for y in w:
        for x in w[y]:
            m.append(getWall(x, y))
    return m

def printWallMap(w, y_max):
    for y in range(y_max):
        st = ''
        for i in range(79):
            if y in w and i in w[y]:
                st = '{0}#'.format(st)
            else:
                st = '{0} '.format(st)
        print(st)
        y += 1

def generateCaveMap(
        width, height, map_id, parent_map, puddle_count, corpse_count, bluepill_count, page_obj,
        exit_token=Tokens.CAVE_STAIRCASE):
    map = []
    max_density = int(float(width - 1) * float(height - 1) * 0.4)
    density = 0
    map_d = getDictMapFromTiles(map)
    while density < max_density:
        x = random.randint(1, width - 1)
        y = random.randint(1, height - 1)
        if not getMapObject(map_d, x, y):
            density += 1
            wall = getWall(x, y)
            map.append(wall)
            map_d[y] = map_d.get(y, {})
            map_d[y][x] = wall
    map_w = getMapWallFromTiles(map)
    for i in range(4):
        map_w_next = {}
        for x in range(1, width - 1):
            for y in range(1, height - 1):
                wall_count_one = getMapWallNeighbours(map_w, x, y, 1)
                wall_count_two = getMapWallNeighbours(map_w, x, y, 2)
                if wall_count_one >= 5 or wall_count_two <= 2:
                    map_w_next[y] = map_w_next.get(y, {})
                    map_w_next[y][x] = True
        map_w = map_w_next
    map = getMapTilesFromWall(map_w)
    for i in range(0, width - 1):
        map.append(getWall(i, 0))
        map.append(getWall(i, height - 1))
    for i in range(1, height - 1):
        map.append(getWall(0, i))
        map.append(getWall(width - 1, i))
    #mid_x = random.randint(int(width * 0.25), int(width * 0.75))
    #mid_y = random.randint(int(height * 0.25), int(height * 0.75))
    mid_x = int(width / 2.0)
    mid_y = int(height / 2.0)
    obj = getMapTileObject(map, mid_x, mid_y)
    if obj:
        map.remove(obj)
    map_fov = libtcod.map_new(width + 1, height + 1)
    libtcod.map_clear(map_fov, True, True)
    for obj in map:
        libtcod.map_set_properties(map_fov, obj.x, obj.y, False, False)
    map_path = libtcod.path_new_using_map(map_fov, dcost=0.0)
    map_d = getDictMapFromTiles(map)
    for x in range(1, width - 1):
        for y in range(1, height - 1):
            obj = getMapObject(map_d, x, y)
            if obj and obj.token_enum == Tokens.WALL:
                continue
            path = libtcod.path_compute(map_path, x, y, mid_x, mid_y)
            if path is False:
                cut_done = False
                step_x = 1
                if x > mid_x:
                    step_x = -1
                for xx in range(x, mid_x, step_x):
                    if cut_done:
                        break
                    obj = getMapObject(map_d, xx, y)
                    if obj:
                        map.remove(obj)
                        del map_d[y][xx]
                        libtcod.map_set_properties(map_fov, xx, y, True, True)
                    cut_path = libtcod.path_compute(map_path, xx, y, mid_x, mid_y)
                    if cut_path is not False:
                        cut_done = True
                step_y = 1
                if y > mid_y:
                    step_y = -1
                for yy in range(y, mid_y, step_y):
                    if cut_done:
                        break
                    obj = getMapObject(map_d, mid_x, yy)
                    if obj:
                        map.remove(obj)
                        del map_d[yy][mid_x]
                        libtcod.map_set_properties(map_fov, mid_x, yy, True, True)
                    cut_path = libtcod.path_compute(map_path, mid_x, yy, mid_x, mid_y)
                    if cut_path is not False:
                        cut_done = True
                map_path = libtcod.path_new_using_map(map_fov, dcost=0.0)

    for i in range(puddle_count):
        px = random.randint(1, width - 1)
        py = random.randint(1, height - 1)
        p_obj = getMapTileObject(map, px, py)
        while p_obj:
            px = random.randint(1, width - 1)
            py = random.randint(1, height - 1)
            p_obj = getMapTileObject(map, px, py)
        puddle_colour = random.randint(1, 3)
        if puddle_colour == 1:
            puddle_colour = libtcod.Color(96, 128, 0)
        elif puddle_colour == 2:
            puddle_colour = libtcod.Color(0, 128, 64)
        else:
            puddle_colour = libtcod.Color(128, 128, 0)
        map.append(GameObject(Tokens.ASYLUM_DIRTY_PUDDLE, px, py,
            puddle_colour, '_', False, False, False))

    for page_token in page_obj:
        px = random.randint(1, width - 1)
        py = random.randint(1, height - 1)
        p_obj = getMapTileObject(map, px, py)
        while p_obj:
            px = random.randint(1, width - 1)
            py = random.randint(1, height - 1)
            p_obj = getMapTileObject(map, px, py)
        map.append(GameObject(page_token,
            px, py, libtcod.Color(255, 255, 115), '(', False, False, False))

    obj = True
    while obj:
        enter_x = random.randint(1, width - 1)
        enter_y = random.randint(1, height - 1)
        obj = getMapTileObject(map, enter_x, enter_y)

    if parent_map:
        for x in parent_map['tiles']:
            if Tokens.ASYLUM_STAIRCASE == x.token_enum or Tokens.CAVE_STAIRCASE == x.token_enum:
                x.setTransition(map_id, enter_x, enter_y)

    exit_distance = 0
    while exit_distance < width / 2.0:
        exit_x = random.randint(1, width - 1)
        exit_y = random.randint(1, height - 1)
        obj = getMapTileObject(map, exit_x, exit_y)
        if not obj:
            exit_distance = getDistance(enter_x, enter_y, exit_x, exit_y)

    map.append(GameTransition(exit_token, exit_x, exit_y, libtcod.Color(175, 175, 175), '>'))

    key_distance = 0
    while key_distance < width / 2.0:
        key_x = random.randint(1, width - 1)
        key_y = random.randint(1, height - 1)
        obj = getMapTileObject(map, key_x, key_y)
        if not obj:
            key_distance = getDistance(enter_x, enter_y, key_x, key_y)
            if key_distance < width / 2.0:
                key_distance = getDistance(exit_x, exit_y, key_x, key_y)
            else:
                key_distance = 0

    map.append(GameObject(Tokens.CAVE_KEY, key_x, key_y, libtcod.Color(191, 151, 96), '~',
        False, False, False))

    stalker_distance = 0
    while stalker_distance < width / 2.0:
        stalker_x = random.randint(1, width - 1)
        stalker_y = random.randint(1, height - 1)
        obj = getMapTileObject(map, stalker_x, stalker_y)
        if not obj:
            stalker_distance = getDistance(enter_x, enter_y, stalker_x, stalker_y)
            if stalker_distance < width / 2.0:
                stalker_distance = getDistance(exit_x, exit_y, stalker_x, stalker_y)
            else:
                stalker_distance = 0

    map.append(GameObject(Tokens.INIT_STALKER, stalker_x, stalker_y, libtcod.Color(0, 0, 0), 's',
        False, False, False))

    for i in range(corpse_count):
        gen_body = True
        while gen_body:
            bx = random.randint(1, width - 1)
            by = random.randint(1, height - 1)
            if not getMapTileObject(map, bx, by):
                map.append(GameObject(Tokens.ASYLUM_CORPSE,
                    bx, by, libtcod.Color(128, 0, 0), '@', False, False, False))
                gen_body = False
    for i in range(bluepill_count):
        gen_bluepill = True
        while gen_bluepill:
            bx = random.randint(1, width - 1)
            by = random.randint(1, height - 1)
            if not getMapTileObject(map, bx, by):
                map.append(GameObject(Tokens.BLUEPILL,
                    bx, by, libtcod.Color(0, 95, 191), 'o', False, False, False))
                gen_bluepill = False

    return map

def getEmptyMapXY(map, xa, ya, xb, yb):
    obj = True
    while obj:
        ox = random.randint(xa, xb)
        oy = random.randint(ya, yb)
        obj = getMapTileObject(map, ox, oy)
    return ox, oy

def generateOutside(width, height, map_id, parent_map, puddle_count):
    map = []
    for i in range(3, width - 2):
        map.append(getFence(i, 3))
        map.append(getFence(i, height - 4))
    for i in range(3, height - 4):
        map.append(getFence(3, i))
        map.append(getFence(width - 3, i))

    enter_x = random.randint(6, width - 6)
    enter_y = random.randint(6, height - 6)
    if parent_map:
        for x in parent_map['tiles']:
            if Tokens.SEWAGE_EXIT == x.token_enum:
                x.setTransition(map_id, enter_x, enter_y)
    map.append(GameObject(Tokens.RUSTED_MANHOLE, enter_x, enter_y,
        libtcod.Color(183, 65, 14), 'o', False, False, False))

    for i in range(puddle_count):
        px, py = getEmptyMapXY(map, 4, 4, width - 4, height - 4)
        map.append(getPuddle(px, py))

    for i in range(int(float(width) / 2.0)):
        sx, sy = getEmptyMapXY(map, 0, 0, width - 1, 2)
        map.append(GameObject(Tokens.INIT_STALKER, sx, sy, libtcod.Color(0, 0, 0), 's',
            False, False, False))
        sx, sy = getEmptyMapXY(map, 0, height - 3, width - 1, height)
        map.append(GameObject(Tokens.INIT_STALKER, sx, sy, libtcod.Color(0, 0, 0), 's',
            False, False, False))
        sx, sy = getEmptyMapXY(map, 0, 3, 2, height - 3)
        map.append(GameObject(Tokens.INIT_STALKER, sx, sy, libtcod.Color(0, 0, 0), 's',
            False, False, False))
        sx, sy = getEmptyMapXY(map, width - 3, 3, width - 1, height - 3)
        map.append(GameObject(Tokens.INIT_STALKER, sx, sy, libtcod.Color(0, 0, 0), 's',
            False, False, False))

    for token in [Tokens.NEWS_1, Tokens.NEWS_2, Tokens.NEWS_3, Tokens.NEWS_4, Tokens.NEWS_5]:
        ox, oy = getEmptyMapXY(map, 4, 4, width - 4, height - 4)
        map.append(GameObject(token, ox, oy, libtcod.Color(255, 255, 255), '(', False, False, False))

    return map

def breakFence(map, map_id):
    fence_obj = []
    for obj in map.getMap(map_id)['tiles']:
        if obj.token_enum == Tokens.CHAIN_FENCE:
            fence_obj.append(obj)
    if len(fence_obj) > 0:
        obj = random.choice(fence_obj)
        map.getMap(map_id)['tiles'].remove(obj)
        map.updateMap(map_id)

def movePlayer(map, player, delta, console, sound_obj):
    m = map.getMap(player.map)
    x = player.x + delta[0]
    y = player.y + delta[1]
    obj = getMapObject(m['d'], x, y)
    if not obj or not obj.blocking:
        player.x = x
        player.y = y
        if obj:
            if obj.token_enum is Tokens.ASYLUM_DIRTY_PUDDLE:
                sound_obj['water-step'].play()
            t = getConsoleText(obj.token_enum)
            if t:
                console.append(t)
    else:
        if obj.token_enum is Tokens.ASYLUM_DOOR:
            sound_obj['barrel-break'].play()
            m['tiles'].remove(obj)
            map.updateMap(player.map)
            console.append(getConsoleText(Tokens.ASYLUM_DOOR))
        else:
            t = getConsoleText(obj.token_enum)
            if t:
                console.append(t)
    player.turn += 1
    player.loseSanity(1, 600, console, sound_obj)

def getDistance(xa, ya, xb, yb):
    val = (xb - xa) ** 2 + (yb - ya) ** 2
    return int(val ** 0.5)

def renderConsole(SCREEN_WIDTH, SCREEN_HEIGHT, map, player, console, sound_obj):
    if player.dead > 0:
        fade_colour = min(255, player.dead * 3)
        libtcod.console_set_default_background(0, libtcod.Color(fade_colour, fade_colour, fade_colour))

    libtcod.console_clear(0)
    
    sx = player.x - int(SCREEN_WIDTH / 2)
    sy = player.y - int(SCREEN_HEIGHT / 2)
    blackout_mult = 1.0
    if player.blackout - player.tick > -20 and player.tick - player.blackout > 0:
        blackout_mult = float(player.tick - player.blackout) / 20.0

    for i in range(sy, sy + SCREEN_HEIGHT - 4):
        if i in map['d']:
            for k in map['d'][i]:
                obj = map['d'][i][k]
                if libtcod.map_is_in_fov(map['fov'], obj.x, obj.y):
                    if obj.token_enum is Tokens.ASYLUM_CORPSE and not obj.observed:
                        sound_obj['ohdearscare'].play()
                        player.loseSanity(50, 400, console, sound_obj)
                        console.append(getConsoleText(obj.token_enum))
                        player.blackout = player.tick + 20
                    elif obj.token_enum is Tokens.STALKER and not obj.observed:
                        sound_obj['ohdearscare'].play()
                        player.loseSanity(75, 200, console, sound_obj)
                        console.append(getConsoleText(obj.token_enum))
                        player.blackout = player.tick + 40
                    if player.blackout >= player.tick:
                        if obj.token_enum not in [Tokens.ASYLUM_CORPSE, Tokens.STALKER]:
                            continue
                    no_mult = False
                    if obj.token_enum in [Tokens.ASYLUM_CORPSE, Tokens.STALKER]:
                        no_mult = True
                    if obj.token_enum == Tokens.STALKER:
                        obj.token = random.choice(stalker_token_obj)
                        stalker_colour = random.randint(0, 255)
                        obj.colour = libtcod.Color(stalker_colour, stalker_colour, stalker_colour)
                    if no_mult:
                        libtcod.console_set_default_foreground(0, obj.colour)
                    else:
                        dist = getDistance(player.x, player.y, obj.x, obj.y)
                        dist_mult = 0.2 + (0.8 * float(player.fov - dist) / float(player.fov))
                        torch_mult = 0.8 + 0.2 * math.cos(float(player.tick / 10.0))
                        libtcod.console_set_default_foreground(0,
                            obj.colour * dist_mult * torch_mult * blackout_mult)
                    libtcod.console_print(0, obj.x - sx, obj.y - sy, obj.token)
                    obj.observed = True
                elif obj.observed:
                    if player.blackout >= player.tick:
                        continue
                    libtcod.console_set_default_foreground(0, obj.colour * 0.08 * blackout_mult)
                    libtcod.console_print(0, obj.x - sx, obj.y - sy, obj.token)
    libtcod.console_set_default_foreground(0, player.colour)
    libtcod.console_print(0, player.x - sx, player.y - sy, player.token)
    for i in range(4):
        libtcod.console_set_default_foreground(0, libtcod.Color(200, 200, 200) * ((2.0 + i) / 5.0))
        libtcod.console_print(0, 0, SCREEN_HEIGHT - 1 - i, console[-(4 - i)])
    libtcod.console_set_default_foreground(0, libtcod.Color(100, 100, 100))
    if player.getInventory(Tokens.BLUEPILL) > 0:
        libtcod.console_set_color_control(
            libtcod.COLCTRL_1, libtcod.Color(0, 95, 191), libtcod.Color(0, 0, 0))
        libtcod.console_print_ex(0, SCREEN_WIDTH - 1, 0,
            libtcod.BKGND_NONE, libtcod.RIGHT, '%co%c:%d' % (
                libtcod.COLCTRL_1, libtcod.COLCTRL_STOP, player.getInventory(Tokens.BLUEPILL)))
    libtcod.console_print_ex(0, SCREEN_WIDTH - 10, 0,
        libtcod.BKGND_NONE, libtcod.RIGHT, 's:%d' % (player.sanity))

    libtcod.console_print(0, 0, 0, 'journal pages: %c%s %s %s %s %s %s %s %s %s %s' %
        (libtcod.COLCTRL_1,
         '1' if Tokens.STORY_1 in player.pages else ' ',
         '2' if Tokens.STORY_2 in player.pages else ' ',
         '3' if Tokens.STORY_3 in player.pages else ' ',
         '4' if Tokens.STORY_4 in player.pages else ' ',
         '5' if Tokens.STORY_5 in player.pages else ' ',
         '6' if Tokens.STORY_6 in player.pages else ' ',
         '7' if Tokens.STORY_7 in player.pages else ' ',
         '8' if Tokens.STORY_8 in player.pages else ' ',
         '9' if Tokens.STORY_9 in player.pages else ' ',
         '0' if Tokens.STORY_0 in player.pages else ' '))

    # hallucinations
    static_p = 1.0 - (float(player.fov) / 10.0) ** 0.1
    if (random.random() < static_p):
        static_x = random.randint(0, SCREEN_WIDTH - 1)
        static_y = random.randint(0, SCREEN_HEIGHT - 1)
        libtcod.console_set_default_foreground(0, libtcod.Color(50, 50, 50))
        libtcod.console_print(0, static_x, static_y, '.')

    libtcod.console_flush()

def printMapDict(map_d):
    y = 0
    done = False
    while not done:
        if y not in map_d:
            done = True
        st = ''
        for i in range(79):
            obj = getMapObject(map_d, i, y)
            if obj:
                st = '{0}{1}'.format(st, obj.token)
            else:
                st = '{0} '.format(st)
        print(st)
        y += 1

def getTitleMult(x):
    return 0.8 + 0.2 * math.cos(float(x / 10.0))

def showTitle(SCREEN_WIDTH, SCREEN_HEIGHT):
    done = False
    i = 0
    while not done:
        i += 1
        mult = 0.6 + 0.4 * math.cos(float(i / 10.0))
        key = libtcod.console_check_for_keypress()
        if key.vk is not libtcod.KEY_NONE:
            done = True

        libtcod.console_set_default_foreground(0, libtcod.Color(250, 250, 250) * getTitleMult(i))
        libtcod.console_print_ex(0, SCREEN_WIDTH - 2, 1, libtcod.BKGND_NONE, libtcod.RIGHT, 'asylumRL')
        libtcod.console_set_default_foreground(0, libtcod.Color(200, 200, 200) * getTitleMult(i + 10))
        libtcod.console_print_ex(0, SCREEN_WIDTH - 2, 2, libtcod.BKGND_NONE, libtcod.RIGHT, '7drl 2012')
        libtcod.console_set_default_foreground(0, libtcod.Color(200, 200, 200) * getTitleMult(i + 20))
        libtcod.console_print_ex(0, SCREEN_WIDTH - 2, 3, libtcod.BKGND_NONE, libtcod.RIGHT, 'scotchfield')
        libtcod.console_set_default_foreground(0, libtcod.Color(128, 128, 250) * getTitleMult(i + 30))
        libtcod.console_print_ex(0, SCREEN_WIDTH - 2, SCREEN_HEIGHT - 2,
            libtcod.BKGND_NONE, libtcod.RIGHT, 'put your headphones on and turn up the volume')

        libtcod.console_set_default_foreground(0, libtcod.Color(216, 216, 216) * getTitleMult(i + 30))
        libtcod.console_set_color_control(
            libtcod.COLCTRL_1, libtcod.Color(0, 95, 191) * getTitleMult(i + 30), libtcod.Color(0, 0, 0))
        libtcod.console_print(0, 1, 1, '%cw%c: move north' % (libtcod.COLCTRL_1, libtcod.COLCTRL_STOP))
        libtcod.console_print(0, 1, 2, '%ca%c: move west' % (libtcod.COLCTRL_1, libtcod.COLCTRL_STOP))
        libtcod.console_print(0, 1, 3, '%cs%c: move south' % (libtcod.COLCTRL_1, libtcod.COLCTRL_STOP))
        libtcod.console_print(0, 1, 4, '%cd%c: move east' % (libtcod.COLCTRL_1, libtcod.COLCTRL_STOP))
        libtcod.console_print(0, 1, 5, '%ce%c: interact' % (libtcod.COLCTRL_1, libtcod.COLCTRL_STOP))
        libtcod.console_print(0, 1, 6, '%cr%c: use' % (libtcod.COLCTRL_1, libtcod.COLCTRL_STOP))
        libtcod.console_print(0, 1, 8, '%cq%c: quit' % (libtcod.COLCTRL_1, libtcod.COLCTRL_STOP))
        libtcod.console_print(0, 1, 10, '%c0-9%c: read journal page' % (
            libtcod.COLCTRL_1, libtcod.COLCTRL_STOP))

        libtcod.console_flush()

def showPage(token_enum, SCREEN_WIDTH, SCREEN_HEIGHT):
    done = False
    i = 0
    while not done:
        i += 1
        mult = 0.8 + 0.2 * math.cos(float(i / 10.0))
        key = libtcod.console_check_for_keypress()
        if key.vk is not libtcod.KEY_NONE:
            done = True

        st = ''
        if token_enum == Tokens.STORY_1:
            st = "page 1\njanuary 9th\n\nmy request for a journal was finally approved.  thanks for speeding that request along, you assholes.  it's been just over two weeks since the police brought me here against my will to the asylum.  i know you fuckers at the office are reading this when you sedate me, so you'd better pay attention.  brought me here against my free will!  i'm not crazy.  i'm not fucking crazy."
        elif token_enum == Tokens.STORY_2:
            st = "page 2\njanuary 12th\n\nthis journal is empowering.  i'm surprised that you bastards haven't taken it away from me yet.  what, are you insulted that i'm not playing your games and answering your questions?  is this the only way you're going to get a look in my head?  i won't be compliant, not here, and not in your interrogations.  besides, you saw what i wrote on the walls of my apartment.  why should this be any different?"
        elif token_enum == Tokens.STORY_3:
            st = "page 3\njanuary 14th\n\nthis is quite a cocktail of drugs you've got me on.  compliant patients are sedated patients, right?  how many of these blue pills can you shove down my fucking throat each day?  i've got a great idea, why don't you let me show you the things i've seen?  if you read my diaries from home, you know what i see when i close my eyes.  at least when i close my eyes without this blue pill bullshit in my body."
        elif token_enum == Tokens.STORY_4:
            st = "page 4\njanuary 28th\n\nby the request of the warden, i willingly agree to exercise my right to compliance.  please don't take away my journal again."
        elif token_enum == Tokens.STORY_5:
            st = "page 5\njanuary 29th\n\nfeeling great, feeling fine.  maybe the pills are finally working.  they make me feel clear.  i'm smiling."
        elif token_enum == Tokens.STORY_6:
            st = "page 6\nfebruary 3rd\n\nhad an outburst today.  filled with regret.  the warden discovered i've been hiding the blue pills they've been trying to cram down my throat.  i've started to see things again.  it's funny, after the silence afforded by the blue pills, i finally understand how to see them.  i hear them without trying now.  you bastards tried to shut them up, but you only unlocked the door."
        elif token_enum == Tokens.STORY_7:
            st = "page 7\nfebruary 4th\n\nhearing more voices.  give me more fucking pills, i dare you.  i fucking dare you!  the eyes are at the door, my friends."
        elif token_enum == Tokens.STORY_8:
            st = "page 8\nfebruary 9th\n\nreprimanded for assulting a guard today at free time.  after it happened, your crew roughed me up pretty good, and fed me a barrel of blue pills.  if i did what you say i did, i deserve every last drop of punishment.  not sure why the guard didn't mention that i was on the other side of the room when he got hurt."
        elif token_enum == Tokens.STORY_9:
            st = "page 9\nfebruary 28th\n\ni've made a mistake.  i've made a terrible mistake.  the things i see, the voices i hear..  they are not my ally.  god, what have i done?"
        elif token_enum == Tokens.STORY_0:
            st = "final page\nmarch 11th\n\ni can't hear anything outside my room.  no screaming, no hollering to get back in my bed.  something has happened."
        elif token_enum == Tokens.NEWS_1:
            st = "The Gazette, March 9th\n5.9 magnitude earthquake sparks stampede, killing 13\n\nA 5.9 magnitude earthquake struck the heart of the city yesterday, causing structural damage on several city buildings and resulting in the deaths of 13 people.\nIn what appears to be an unprecidented twist of fate, the quake appears to have been centered directly under the city itself."
        elif token_enum == Tokens.NEWS_2:
            st = "The Gazette, March 10th\nAftershocks confirmed, more deaths reported\n\nGeologists have confirmed yet another aftershock last night, forcing the mayor to declare a state of emergency.  Researchers are unable to explain why these aftershocks are occurring at the same intensity as the original quake, if not stronger."
        elif token_enum == Tokens.NEWS_3:
            st = "The Gazette, March 11th\nMass hysteria results in thousands of deaths\n\nGovernment officials declare that they have been forced to enact a curfew.  All citizens are requested to stay indoors at home, to lock and bar their doors and windows, and to remain safe until the hysteria can be contained."
        elif token_enum == Tokens.NEWS_4:
            st = "The news article has been overwritten with frantic handwriting.\n\nMY FAMILY RAN FROM THE HORRORS AND HID IN THE ONLY SAFEHOUSE WE COULD FIND!  PLEASE SAVE US!  WE WAIT IN THE ASYLUM SAFEHOUSE!"
        elif token_enum == Tokens.NEWS_5:
            st = "PAMPHLET FROM THE CHURCH OF THE SHAMBLING STALKER\n\nREPENT, OUR TIME IS HERE!  YOU ARE SHEEP FOR THE SLAUGHTER, BUT IN DEATH, YOUR SOUL WILL REMAIN!  ONLY YOUR BELIEF CAN HELP YOU RETAIN YOUR SANITY IN THESE TROUBLING TIMES!\n\nThe article is stained with blood."
        else:
            st = 'hmm..'

        libtcod.console_set_default_foreground(0, libtcod.Color(216, 216, 216) * getTitleMult(i))
        libtcod.console_print_rect(0, 5, 5, SCREEN_WIDTH - 10, SCREEN_HEIGHT - 10, st)

        libtcod.console_flush()

def main():
    SCREEN_WIDTH = 60
    SCREEN_HEIGHT = 35
    LIMIT_FPS = 20

    print('generating the world..  there\'s no need to be scared..')
    console = ['', '', '', '']
    map = Map()
    map.addMap('asylum', generateAsylumMap(random.randint(20, 26), random.randint(44, 56)))
    map.addMap('asylumcommon', generateAsylumCommonMap(
        random.randint(40, 52), random.randint(16, 22), map.getMap('asylum')))
    map.addMap('cave1', generateCaveMap(
        random.randint(55, 70), random.randint(55, 70), 'cave1', map.getMap('asylumcommon'),
        random.randint(15, 35), random.randint(2, 5), random.randint(2, 5),
        [Tokens.STORY_7, Tokens.STORY_8]))
    map.addStalker('cave1', 10)
    map.addMap('cave2', generateCaveMap(
        random.randint(85, 120), random.randint(75, 90), 'cave2', map.getMap('cave1'),
        random.randint(30, 50), random.randint(3, 6), random.randint(3, 6),
        [Tokens.STORY_9, Tokens.STORY_0]))
    map.addStalker('cave2', 14)
    map.addMap('cave3', generateCaveMap(
        random.randint(125, 160), random.randint(105, 150), 'cave3', map.getMap('cave2'),
        random.randint(60, 90), random.randint(5, 7), random.randint(5, 7), [],
        exit_token=Tokens.SEWAGE_EXIT))
    map.addStalker('cave3', 18)
    map.addMap('outside', generateOutside(
        random.randint(15, 19), random.randint(13, 17), 'outside', map.getMap('cave3'),
        random.randint(14, 24)))
    map.addStalker('outside', 99)
    #cProfile.run("generateCaveMap(150, 150, 'cave1', None, 90, 7, 7)")
    player = GamePlayer(5, 1)
    player.setMap('asylum')

    map.computeFov(player)

    font = os.path.join('fonts', 'consolas10x10_gs_tc.png')
    libtcod.console_set_custom_font(font, libtcod.FONT_TYPE_GREYSCALE | libtcod.FONT_LAYOUT_TCOD)
    libtcod.console_init_root(SCREEN_WIDTH, SCREEN_HEIGHT, 'asylumRL by scotchfield', False)
    libtcod.sys_set_fps(LIMIT_FPS)

    pygame.init()
    pygame.mixer.init()
    sound_obj = loadSounds()

    showTitle(SCREEN_WIDTH, SCREEN_HEIGHT)

    sound_obj['heartbeat'].play(loops=-1)
    sound_obj['heartbeat'].set_volume(max(1.0 - float(player.sanity) / 1500.0, 0))
    done = False
    done_request = False
    while not done:
        player.tick += 1
        if random.randint(1, 5000) == 1:
            sound_obj['whisper-1'].play()
        if random.randint(1, 5000) == 1:
            sound_obj['whisper-2'].play()
        if player.dead > 0:
            player.dead += 1
            
        key = libtcod.console_check_for_keypress()
        player_moved = False
        if key.vk == libtcod.KEY_NONE:
            pass
        elif player.dead == 0:
            #print(key.c)
            if key.c == ord('q'):
                console.append('Press \'y\' if you want to quit..')
                done_request = True
            elif key.c == ord('y'):
                if done_request:
                    done = True
            elif key.c == ord('w'):
                movePlayer(map, player, (0, -1), console, sound_obj)
                map.computeFov(player)
                player_moved = True
            elif key.c == ord('s'):
                movePlayer(map, player, (0, 1), console, sound_obj)
                map.computeFov(player)
                player_moved = True
            elif key.c == ord('a'):
                movePlayer(map, player, (-1, 0), console, sound_obj)
                map.computeFov(player)
                player_moved = True
            elif key.c == ord('d'):
                movePlayer(map, player, (1, 0), console, sound_obj)
                map.computeFov(player)
                player_moved = True
            elif key.c == ord('e'):
                obj = getMapObject(map.getMap(player.map)['d'], player.x, player.y)
                if not obj:
                    pass
                elif Tokens.ASYLUM_STAIRCASE == obj.token_enum:
                    console.append('You descend the dark staircase.')
                    player.setMap(obj.map_id)
                    player.x = obj.map_x
                    player.y = obj.map_y
                    map.computeFov(player)
                    player_moved = True
                elif Tokens.CAVE_STAIRCASE == obj.token_enum:
                    if player.has_key:
                        console.append('You descend even deeper into the asylum caves.')
                        player.setMap(obj.map_id)
                        player.x = obj.map_x
                        player.y = obj.map_y
                        map.computeFov(player)
                    else:
                        console.append('The passage is sealed with a brass lock. You\'ll need a key.')
                    player_moved = True
                elif Tokens.SEWAGE_EXIT == obj.token_enum:
                    if player.has_key:
                        console.append('You descend into the sewage line.')
                        player.setMap(obj.map_id)
                        player.x = obj.map_x
                        player.y = obj.map_y
                        map.computeFov(player)
                    else:
                        console.append('The passage is sealed with a brass lock. You\'ll need a key.')
                    player_moved = True
                elif Tokens.BLUEPILL == obj.token_enum:
                    if player.getInventory(Tokens.BLUEPILL) < 4:
                        console.append('You pick up the sedative.  Press \'r\' to use it.')
                        player.addInventory(Tokens.BLUEPILL, 1)
                        map.getMap(player.map)['tiles'].remove(obj)
                        map.updateMap(player.map)
                        map.computeFov(player)
                    else:
                        console.append('You can\'t comfortably hold any more!')
                    player_moved = True
                elif Tokens.CAVE_KEY == obj.token_enum:
                    console.append('You pick up the brass key.')
                    player.has_key = True
                    map.getMap(player.map)['tiles'].remove(obj)
                    map.updateMap(player.map)
                    map.computeFov(player)
                    player_moved = True
                elif obj.token_enum in story_enum_obj:
                    console.append('You pick up the torn journal page.')
                    player.pages[obj.token_enum] = True
                    showPage(obj.token_enum, SCREEN_WIDTH, SCREEN_HEIGHT)
                    map.getMap(player.map)['tiles'].remove(obj)
                    map.updateMap(player.map)
                    map.computeFov(player)
                    player_moved = True
                elif obj.token_enum in news_enum_obj:
                    console.append('You read the discarded news article.')
                    player.news[obj.token_enum] = True
                    showPage(obj.token_enum, SCREEN_WIDTH, SCREEN_HEIGHT)
                    player_moved = True
            elif key.c == ord('r'):
                if player.getInventory(Tokens.BLUEPILL) > 0:
                    console.append('You consume the sedative..')
                    player.removeInventory(Tokens.BLUEPILL, 1)
                    player.addSanity(400, 1450, console, sound_obj)
                else:
                    console.append('You don\'t have any sedatives to use.')
                    player_moved = True
            elif key.c == ord('1'):
                if Tokens.STORY_1 in player.pages:
                    showPage(Tokens.STORY_1, SCREEN_WIDTH, SCREEN_HEIGHT)
                    player_moved = True
            elif key.c == ord('2'):
                if Tokens.STORY_2 in player.pages:
                    showPage(Tokens.STORY_2, SCREEN_WIDTH, SCREEN_HEIGHT)
                    player_moved = True
            elif key.c == ord('3'):
                if Tokens.STORY_3 in player.pages:
                    showPage(Tokens.STORY_3, SCREEN_WIDTH, SCREEN_HEIGHT)
                    player_moved = True
            elif key.c == ord('4'):
                if Tokens.STORY_4 in player.pages:
                    showPage(Tokens.STORY_4, SCREEN_WIDTH, SCREEN_HEIGHT)
                    player_moved = True
            elif key.c == ord('5'):
                if Tokens.STORY_5 in player.pages:
                    showPage(Tokens.STORY_5, SCREEN_WIDTH, SCREEN_HEIGHT)
                    player_moved = True
            elif key.c == ord('6'):
                if Tokens.STORY_6 in player.pages:
                    showPage(Tokens.STORY_6, SCREEN_WIDTH, SCREEN_HEIGHT)
                    player_moved = True
            elif key.c == ord('7'):
                if Tokens.STORY_7 in player.pages:
                    showPage(Tokens.STORY_7, SCREEN_WIDTH, SCREEN_HEIGHT)
                    player_moved = True
            elif key.c == ord('8'):
                if Tokens.STORY_8 in player.pages:
                    showPage(Tokens.STORY_8, SCREEN_WIDTH, SCREEN_HEIGHT)
                    player_moved = True
            elif key.c == ord('9'):
                if Tokens.STORY_9 in player.pages:
                    showPage(Tokens.STORY_9, SCREEN_WIDTH, SCREEN_HEIGHT)
                    player_moved = True
            elif key.c == ord('0'):
                if Tokens.STORY_0 in player.pages:
                    showPage(Tokens.STORY_0, SCREEN_WIDTH, SCREEN_HEIGHT)
                    player_moved = True
            else:
                done_request = False
        if player.dead > 0:
            player.dead += 1
            if player.dead > 100:
                done = True
        if player_moved:
            done_request = False
            if len(player.news) == 5:
                if random.randint(0, 5) == 0:
                    breakFence(map, 'outside')
                    map.updateMap(player.map)
                    map.computeFov(player)
                    sound_obj['crash'].play()
                for stalker in map.getMap(player.map)['stalker_obj']:
                    stalker.updateMapFov(map)
            for stalker in map.getMap(player.map)['stalker_obj']:
                player_caught = stalker.update(player, map, console, sound_obj)
                if player_caught:
                    player.dead = 1
        renderConsole(SCREEN_WIDTH, SCREEN_HEIGHT, map.getMap(player.map), player, console, sound_obj)

    pygame.mixer.quit()
            

if __name__ == "__main__":
    #cProfile.run("main()")
    main()
