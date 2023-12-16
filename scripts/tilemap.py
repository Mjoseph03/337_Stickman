import json
import random
import pygame

#autotiling logic, determines if adj tiles are the same or not.
AUTOTILE_MAP = {
    tuple(sorted([(1, 0), (0, 1)])): 0,
    tuple(sorted([(1, 0), (0, 1), (-1, 0)])): 1,
    tuple(sorted([(-1, 0), (0, 1)])): 2, 
    tuple(sorted([(-1, 0), (0, -1), (0, 1)])): 3,
    tuple(sorted([(-1, 0), (0, -1)])): 4,
    tuple(sorted([(-1, 0), (0, -1), (1, 0)])): 5,
    tuple(sorted([(1, 0), (0, -1)])): 6,
    tuple(sorted([(1, 0), (0, -1), (0, 1)])): 7,
    tuple(sorted([(1, 0), (-1, 0), (0, 1), (0, -1)])): 8,
}

NEIGHBOR_OFFSETS = [(-1, 0), (-1, -1), (0, -1), (1, -1), (1, 0), (0, 0), (-1, 1), (0, 1), (1, 1)]

#makes it easier to follow the logic, and kinda modular 
PHYSICS_TILES = {'grass', 'stone'}
WEAPON_TILES = {'gunTile'}
TRANSITION_TILES = {'transition'}
AUTOTILE_TYPES = {'grass', 'stone'}

class Tilemap:
    def __init__(self, game, tile_size=16):
        self.game = game
        self.tile_size = tile_size
        self.tilemap = {}
        self.offgrid_tiles = []
    
    #returns a list of tile, regardless if its on or off grid. Super useful
    #for spawners
    def extract(self, id_pairs, keep=False):
        matches = []
        for tile in self.offgrid_tiles.copy():
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                if not keep:
                    self.offgrid_tiles.remove(tile)
                    
        for loc in self.tilemap:
            tile = self.tilemap[loc]
            if (tile['type'], tile['variant']) in id_pairs:
                matches.append(tile.copy())
                matches[-1]['pos'] = matches[-1]['pos'].copy()
                matches[-1]['pos'][0] *= self.tile_size
                matches[-1]['pos'][1] *= self.tile_size
                if not keep:
                    del self.tilemap[loc]
        return matches
    
    #returns the tiles immediately around a entity. Useful for physics
    def get_tiles_around(self, pos):
        tiles = []
        tile_loc = (int(pos[0] // self.tile_size), int(pos[1] // self.tile_size))
        for offset in NEIGHBOR_OFFSETS:
            check_loc = str(tile_loc[0] + offset[0]) + ';' + str(tile_loc[1] + offset[1])
            if check_loc in self.tilemap:
                tiles.append(self.tilemap[check_loc])
        return tiles
    
    #serializing map dictionaries to json
    def save(self, path):
        f = open(path, 'w')
        json.dump({'tilemap': self.tilemap, 'tile_size': self.tile_size, 'offgrid': self.offgrid_tiles}, f)
        f.close()
    
    #deserializing json map and loading it into dictionaries 
    def load(self, path):
        f = open(path, 'r')
        map_data = json.load(f)
        f.close()
        self.tilemap = map_data['tilemap']
        self.tile_size = map_data['tile_size']
        self.offgrid_tiles = map_data['offgrid']
    
    #checks for tiles that arent air tiles 
    def solid_check(self, pos):
        tile_loc = str(int(pos[0] // self.tile_size)) + ';' + str(int(pos[1] // self.tile_size))
        if tile_loc in self.tilemap:
            if self.tilemap[tile_loc]['type'] in PHYSICS_TILES:
                return self.tilemap[tile_loc]
    
    #returns a dictionary of the location and variant of the transition tiles  
    def get_transition_tiles_loc(self):
        transition_tiles = []
        for tile_loc in self.tilemap:
            tile = self.tilemap[tile_loc]
            if tile['type'] in TRANSITION_TILES:
                transition_tile = {
                    'coord': pygame.Rect(tile['pos'][0] * self.tile_size, tile['pos'][1] * self.tile_size, self.tile_size, self.tile_size),
                    'variant': tile.get('variant', 0)
                }
                transition_tiles.append(transition_tile)
        return transition_tiles
    
    #returns a list of gun tile locations
    def get_gun_tile_loc(self):
        gun_tile = []
        for tile_loc in self.tilemap:
            tile = self.tilemap[tile_loc]
            if tile['type'] in WEAPON_TILES:
                tile_rect = pygame.Rect(tile['pos'][0] * self.tile_size,
                                        tile['pos'][1] * self.tile_size,
                                        self.tile_size,
                                        self.tile_size)
                gun_tile.append(tile_rect)
        return gun_tile
    
    #gives a 'random' chance for the gun to be immediately despawned when the map is loaded 
    def spawn_gun_by_chance(self):
        if random.random() > 0.5:
            self.despawn_gun_tile()
    
    #removes gun tile from the runtime map dictionary 
    def despawn_gun_tile(self):
        for tile_loc in list(self.tilemap.keys()):
            tile = self.tilemap[tile_loc]
            if tile['type'] in WEAPON_TILES:
                del self.tilemap[tile_loc]
    
    #returns the pygame rect of all the adj tiles around the passed entity pos
    def get_physics_rects(self, pos):
        rects = []
        for tile in self.get_tiles_around(pos):
            if tile['type'] in PHYSICS_TILES:
                rects.append(pygame.Rect(tile['pos'][0] * self.tile_size,
                                         tile['pos'][1] * self.tile_size,
                                         self.tile_size,
                                         self.tile_size))
        return rects
    
    #logic behind autotiling, stolen from the guide and I haven't thought about it since..
    def autotile(self):
        for loc in self.tilemap:
            tile = self.tilemap[loc]
            neighbors = set()
            for shift in [(1, 0), (-1, 0), (0, -1), (0, 1)]:
                check_loc = str(tile['pos'][0] + shift[0]) + ';' + str(tile['pos'][1] + shift[1])
                if check_loc in self.tilemap:
                    if self.tilemap[check_loc]['type'] == tile['type']:
                        neighbors.add(shift)
            neighbors = tuple(sorted(neighbors))
            if (tile['type'] in AUTOTILE_TYPES) and (neighbors in AUTOTILE_MAP):
                tile['variant'] = AUTOTILE_MAP[neighbors]
    
    #applying tile images ontop of map based on the: list position for offtiles (expensive) dict xy string coord (cheap). 
    def render(self, surf, offset=(0, 0)):
        for tile in self.offgrid_tiles:
            surf.blit(self.game.assets[tile['type']][tile['variant']], (tile['pos'][0] - offset[0], tile['pos'][1] - offset[1]))
        
        #pretty annoying, but overall worth it given the performance gains 
        for x in range(offset[0] // self.tile_size, (offset[0] + surf.get_width()) // self.tile_size + 1):
            for y in range(offset[1] // self.tile_size, (offset[1] + surf.get_height()) // self.tile_size + 1):
                loc = str(x) + ';' + str(y)
                if loc in self.tilemap:
                    tile = self.tilemap[loc]
                    try:
                        surf.blit(self.game.assets[tile['type']][tile['variant']], (tile['pos'][0] * self.tile_size - offset[0], tile['pos'][1] * self.tile_size - offset[1]))
                    except Exception as e:
                        #top tier error handling I know..
                        print(f"Error rendering: {tile['type']}, {tile['variant']}, {tile['pos']}" )
    