import os
import sys
import math
import random

import pygame

from scripts.utils import load_image, load_images, Animation
from scripts.entities import  Player,InputHandler,BattleManager
from scripts.tilemap import Tilemap
from scripts.clouds import Clouds
from scripts.particle import Particle
from scripts.spark import Spark

class Game:
    def __init__(self):
        pygame.init()
        
        pygame.display.set_caption('ninja game')
        self.screen = pygame.display.set_mode((900, 600))
        self.display = pygame.Surface((320, 240), pygame.SRCALPHA)
        self.display_2 = pygame.Surface((320, 240))
        self.clock = pygame.time.Clock()
        self.assets = {
            'decor': load_images('tiles/decor'),
            'grass': load_images('tiles/grass'),
            'large_decor': load_images('tiles/large_decor'),
            'stone': load_images('tiles/stone'),
            'player': load_image('entities/player.png'),
            'background': load_image('background.png'),
            'clouds': load_images('clouds'),
            'player/idle': Animation(load_images('entities/player/idle'), img_dur=6),
            'player/run': Animation(load_images('entities/player/run'), img_dur=4),
            'player/jump': Animation(load_images('entities/player/jump')),
            'player/slide': Animation(load_images('entities/player/slide')),
            'player/wall_slide': Animation(load_images('entities/player/wall_slide')),
            'particle/leaf': Animation(load_images('particles/leaf'), img_dur=20, loop=False),
            'particle/particle': Animation(load_images('particles/particle'), img_dur=6, loop=False),
            'gun': load_image('gun.png'),
            'projectile': load_image('projectile.png'),
        }
        
        self.player1_controls = {
                                'left' : pygame.K_a,
                                'right' : pygame.K_d,
                                'jump' : pygame.K_w,
                                'dash' : pygame.K_e,
                                'attack' : pygame.K_SPACE
                            }
        self.player2_controls = {
                                'left' : pygame.K_LEFT,
                                'right' : pygame.K_RIGHT,
                                'jump' : pygame.K_UP,
                                'dash' : pygame.K_m,
                                'attack' : pygame.K_RSHIFT
                            }
        #todo: fix sounds     
        # self.sfx = {
        #     'jump': pygame.mixer.Sound('data/sfx/jump.wav'),
        #     'dash': pygame.mixer.Sound('data/sfx/dash.wav'),
        #     'hit': pygame.mixer.Sound('data/sfx/hit.wav'),
        #     'shoot': pygame.mixer.Sound('data/sfx/shoot.wav'),
        #     'ambience': pygame.mixer.Sound('data/sfx/ambience.wav'),
        # }
        
        # self.sfx['ambience'].set_volume(0.2)
        # self.sfx['shoot'].set_volume(0.4)
        # self.sfx['hit'].set_volume(0.8)
        # self.sfx['dash'].set_volume(0.3)
        # self.sfx['jump'].set_volume(0.7)
        
        self.tilemap = Tilemap(self, tile_size=16)
        self.clouds = Clouds(self.assets['clouds'], count=16)
        self.player1 = Player(self, (50, 50), (8, 15))
        self.player2 = Player(self, (50, 400), (8, 15))
        
        self.player1_input = InputHandler(self.player1_controls, self.player1)
        self.player2_input = InputHandler(self.player2_controls, self.player2)
        self.battle_manager = BattleManager(self, self.player1, self.player2, self.assets)
        
        self.player1.gun = 1
        self.player2.gun = 1
        
        self.level = 4
        self.load_level(self.level)
        self.transition = 0
        self.screenshake = 0
    
    def next_map_effect(self):
        self.transition = min(30, self.transition + 1)  
    
    def load_level(self, map_id):
        self.tilemap.load('data/maps/' + str(map_id) + '.json')
        
        self.leaf_spawners = []
        for tree in self.tilemap.extract([('large_decor', 2)], keep=True):
            self.leaf_spawners.append(pygame.Rect(4 + tree['pos'][0], 4 + tree['pos'][1], 23, 13))
            
        for spawner in self.tilemap.extract([('spawners', 0), ('spawners', 1)]):
            if spawner['variant'] == 0:
                self.player2.pos = spawner['pos']
                self.player1.pos = spawner['pos']
                self.player1.air_time = 0
                self.player2.air_time = 0
            
        self.projectiles = []
        self.particles = []
        self.sparks = []
        self.scroll = [0, 0]
        self.dead = 0
        self.transition = -30
        
        
    def run(self):
        # pygame.mixer.music.load('data/music.wav')
        # pygame.mixer.music.set_volume(0.5)
        # pygame.mixer.music.play(-1)
        
        # self.sfx['ambience'].play(-1)
        
        while True:
            self.display.fill((0, 0, 0, 0))
            self.display_2.blit(self.assets['background'], (0, 0))
            self.screenshake = max(0, self.screenshake - 1)
                         
            if self.transition < 0:
                self.transition += 1
            
            mid_x = (self.player1.rect().centerx + self.player2.rect().centerx) / 2
            mid_y = (self.player1.rect().centery + self.player2.rect().centery) / 2
            
            self.scroll[0] += (mid_x - self.display.get_width() / 2 - self.scroll[0]) / 30
            self.scroll[1] += (mid_y - self.display.get_height() / 2 - self.scroll[1]) / 30
            
            render_scroll = (int(self.scroll[0]), 0)
            #render_scroll = (int(self.scroll[0]), int(self.scroll[1]))
            
            for rect in self.leaf_spawners:
                if random.random() * 49999 < rect.width * rect.height:
                    pos = (rect.x + random.random() * rect.width, rect.y + random.random() * rect.height)
                    self.particles.append(Particle(self, 'leaf', pos, velocity=[-0.1, 0.3], frame=random.randint(0, 20)))
            
            self.clouds.update()
            self.clouds.render(self.display_2, offset=render_scroll)
            self.tilemap.render(self.display, offset=render_scroll)
            
            self.battle_manager.update()
            
            # if not self.player1.dead:                   
            self.player1.update(self.tilemap, (self.player1_input.update(), 0))
            self.player1.render(self.display, offset=render_scroll)
            
            # if not self.player2.dead:
            self.player2.update(self.tilemap, (self.player2_input.update(), 0))
            self.player2.render(self.display, offset=render_scroll)
            
            
            #bullets for the gun
            # [[x, y], direction, timer]
            for projectile in self.projectiles.copy():
                projectile[0][0] += projectile[1]
                projectile[2] += 1
                img = self.assets['projectile']
                
                #drawing bullet to screen, accounting for image size and the camera scrolling
                self.display.blit(img, (projectile[0][0] - img.get_width() / 2 - render_scroll[0], projectile[0][1] - img.get_height() / 2 - render_scroll[1]))
            
                #checking if bullet hit a solid block, removing it if true and making a spark
                if self.tilemap.solid_check(projectile[0]):
                    self.projectiles.remove(projectile)
                    for i in range(4):
                        #shooting sparks left if projectile is going right and vice versa                                                           
                        self.sparks.append(Spark(projectile[0], random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0), 2 + random.random()))
                       
                #disposing of bullet after 6 seconds
                elif projectile[2] > 360:
                    self.projectiles.remove(projectile)
            
            #rendering sparks   
            for spark in self.sparks.copy():
                kill = spark.update()
                spark.render(self.display, offset=render_scroll)
                if kill:
                    self.sparks.remove(spark)
                    
            display_mask = pygame.mask.from_surface(self.display)
            display_sillhouette = display_mask.to_surface(setcolor=(0, 0, 0, 180), unsetcolor=(0, 0, 0, 0))
            
            for offset in [(-1, 0), (1, 0), (0, -1), (0, 1)]:
                self.display_2.blit(display_sillhouette, offset)
            
            for particle in self.particles.copy():
                kill = particle.update()
                particle.render(self.display, offset=render_scroll)
                if particle.type == 'leaf':
                    particle.pos[0] += math.sin(particle.animation.frame * 0.035) * 0.3
                if kill:
                    self.particles.remove(particle)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    sys.exit()
           
            #map transition, done by changing the size of a circle
            if self.transition:
                transition_surf = pygame.Surface(self.display.get_size())
                pygame.draw.circle(transition_surf, (255, 255, 255), (self.display.get_width() // 2, self.display.get_height() // 2), (30 - abs(self.transition)) * 8)
                transition_surf.set_colorkey((255, 255, 255))
                self.display.blit(transition_surf, (0, 0))
                
            self.display_2.blit(self.display, (0, 0))
            
            #screenshake 
            screenshake_offset = (random.random() * self.screenshake - self.screenshake / 2, random.random() * self.screenshake - self.screenshake / 2)
            self.screen.blit(pygame.transform.scale(self.display_2, self.screen.get_size()), screenshake_offset)
            pygame.display.update()
            self.clock.tick(60)

Game().run()