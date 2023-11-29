import math
import random
import time

import pygame

from scripts.particle import Particle
from scripts.spark import Spark
        
class Physics:
    def __init__(self, game, e_type, pos, size):
        self.game = game
        self.type = e_type
        self.pos = list(pos) #converts iterable to list, each entity will have its own list for updating
        self.size = size
        self.velocity = [0, 0]
        self.collisions = {'up': False,
                           'down': False,
                           'right': False,
                           'left': False
                        }
        self.action = ''
        self.anim_offset = (-3, -3) #creates padding around each animation image to account for space
        self.flip = False
        self.set_action('idle')
        self.last_movement = [0, 0]
    
    def set_action(self, action):
        if action != self.action:
            self.action = action
            self.animation = self.game.assets[self.type + '/' + self.action].copy()
        
    def update(self, tilemap, movement=(0, 0)):
        self.collisions = {'up': False,
                           'down': False,
                           'right': False,
                           'left': False
                        }
        
        frame_movement = (movement[0] + self.velocity[0],
                          movement[1] + self.velocity[1])

        self.update_x_axis(frame_movement, tilemap)
        self.update_y_axis(frame_movement, tilemap)
        self.update_flip(movement)
            
        self.last_movement = movement

        if self.collisions['down'] or self.collisions['up']:
            self.velocity[1] = 0
        
        self.animation.update()
        
    def update_x_axis(self, frame_movement, tilemap):
        self.pos[0] += frame_movement[0]
        entity_rect = self.rect()
        
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[0] > 0:
                    entity_rect.right = rect.left
                    self.collisions['right'] = True
                    
                if frame_movement[0] < 0:
                    entity_rect.left = rect.right
                    self.collisions['left'] = True
                    
                self.pos[0] = entity_rect.x
        
    def update_y_axis(self, frame_movement, tilemap):
        self.pos[1] += frame_movement[1]
        entity_rect = self.rect()
        
        for rect in tilemap.physics_rects_around(self.pos):
            if entity_rect.colliderect(rect):
                if frame_movement[1] > 0:
                    entity_rect.bottom = rect.top
                    self.collisions['down'] = True
                    
                if frame_movement[1] < 0:
                    entity_rect.top = rect.bottom
                    self.collisions['up'] = True
                    
                self.pos[1] = entity_rect.y
                
        #a way to mimic terminal velocity
        self.velocity[1] = min(5, self.velocity[1] + 0.1)
    
    def update_flip(self, movement):
        if movement[0] > 0:
            self.flip = False
        if movement[0] < 0:
            self.flip = True
    
    def render(self, surf, offset=(0, 0)):
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False), (self.pos[0] - offset[0] + self.anim_offset[0], self.pos[1] - offset[1] + self.anim_offset[1]))
   
    def rect(self):
        return pygame.Rect(self.pos[0], self.pos[1], self.size[0], self.size[1])
    
    
class InputHandler:
    def __init__(self, controls, player):
        self.controls = controls
        self.player = player

    def update(self):
        keys = pygame.key.get_pressed()
        movement = [False, False]
        
        if keys[self.controls['left']]:
            movement[0] = True
        if keys[self.controls['right']]:
            movement[1] = True
        if keys[self.controls['jump']]:
            self.player.jump()
        if keys[self.controls['dash']]:
            self.player.dash()
        if keys[self.controls['attack']]:
            self.player.attack()
        
        return movement[1] - movement[0]  


class Player(Physics):
    #todo: find a different player model for player 2
    #      have weapon pickup handling
    def __init__(self, game, pos, size):
        super().__init__(game, 'player', pos, size)
        self.air_time = 0
        self.jumps = 1
        self.wall_slide = False
        self.dashing = 0
        self.attacking = 0
        self.health = 10
        self.dead = 0
        self.gun = 0
        self.sword = 0
         
    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)
        
        self.check_collisions(movement)
        self.update_dashing()
        
    def check_collisions(self, movement):
        #checking for free falling
        self.air_time += 1
        if self.air_time > 120:
            # if not self.game.dead:
            #     self.game.screenshake = max(16, self.game.screenshake)
            self.dead += 1
        
        #if player is on the ground
        if self.collisions['down']:
            self.air_time = 0
            self.jumps = 1
        self.wall_slide = False
        
        #if the player is wall jumping/sliding
        if (self.collisions['right'] or self.collisions['left']) and self.air_time > 4:
            self.wall_slide = True
            self.velocity[1] = min(self.velocity[1], 0.5)
            
            if self.collisions['right']:
                self.flip = False
            else:
                self.flip = True
                
            self.set_action('wall_slide')
        
        #handling after wall sliding
        if not self.wall_slide:
            if self.air_time > 4:
                self.set_action('jump')
            elif movement[0] != 0:
                self.set_action('run')
            else:
                self.set_action('idle') 
    
    def update_dashing(self):
        self.dash_effect()
        self.dash_movement()
        
        #normalizing x axis movement         
        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)
            
    def render(self, surf, offset=(0, 0)):
        #renders gun on top of player
        if self.gun:
            super().render(surf, offset=offset)
            if self.flip:
                surf.blit(pygame.transform.flip(self.game.assets['gun'], True, False), (self.rect().centerx - 4 - self.game.assets['gun'].get_width() - offset[0], self.rect().centery - offset[1]))
            else:
                surf.blit(self.game.assets['gun'], (self.rect().centerx + 4 - offset[0], self.rect().centery - offset[1]))
        if abs(self.dashing) <= 50:
            super().render(surf, offset=offset)
              
    def jump(self):
        if self.wall_slide:
            if self.flip and self.last_movement[0] < 0:
                self.velocity[0] = 3.5
                self.velocity[1] = -2.5
                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
                return True
            elif not self.flip and self.last_movement[0] > 0:
                self.velocity[0] = -3.5
                self.velocity[1] = -2.5
                self.air_time = 5
                self.jumps = max(0, self.jumps - 1)
                return True
                
        elif self.jumps:
            self.velocity[1] = -3
            self.jumps -= 1
            self.air_time = 5
            return True
    
    def dash(self):
        if not self.dashing:
            # self.game.sfx['dash'].play()
            if self.flip:
                self.dashing = -60
            else:
                self.dashing = 60
    
    def dash_effect(self):
         #makes a burst of 20 particles in a circle
         if abs(self.dashing) in {60, 50}:
            for i in range(20):
                angle = random.random() * math.pi * 2 #random angle within 360 deg
                speed = random.random() * 0.5 + 0.5 #random speed
                pvelocity = [math.cos(angle) * speed, math.sin(angle) * speed] #calculating based on speed and angle of particle
                self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))

    def dash_movement(self):
        #normalizing dashing after its been executed
        if self.dashing > 0:
            self.dashing = max(0, self.dashing - 1)
        if self.dashing < 0:
            self.dashing = min(0, self.dashing + 1)
        
        #finding the direction of a dash by using the first 10 frames
        if abs(self.dashing) > 50:
            self.velocity[0] = abs(self.dashing) / self.dashing * 8
            
            #dampening the dash after 10 frames, works as a cool-down 
            if abs(self.dashing) == 51:
                self.velocity[0] *= 0.1
                
            #creating the particle stream while dashing
            pvelocity = [abs(self.dashing) / self.dashing * random.random() * 3, 0]
            self.game.particles.append(Particle(self.game, 'particle', self.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))
    
    def attack(self):
        self.attacking += 1
        
        if self.gun and len(self.game.projectiles) < 120:
            if (self.flip):
                #self.game.sfx['shoot'].play()
                #appending to projectile list, adding some offset based on direction
                self.game.projectiles.append([[self.rect().centerx - 7, self.rect().centery], -1.5, 0])
                for i in range(4):
                    self.game.sparks.append(Spark(self.game.projectiles[-1][0],
                                                  random.random() - 0.5 + math.pi,
                                                  2 + random.random()))

            if (not self.flip):
                #self.game.sfx['shoot'].play()
                self.game.projectiles.append([[self.rect().centerx + 7, self.rect().centery], 8, 0])
                for i in range(4):
                    self.game.sparks.append(Spark(self.game.projectiles[-1][0],
                                                  random.random() - 0.5,
                                                  2 + random.random()))
            
            self.attacking = 0

        #todo: trigger an attack animation/change the attack height
        if self.sword:
            pass

        
class BattleManager:
    def __init__(self, game, player1, player2, assets):
        self.game = game
        self.player1 = player1
        self.player2 = player2
        self.assets = assets
        self.unlock = [False, False]
        self.maps = [0,1,2,3,4,5,6,7,8]
        self.current_map = 4
        
    def update(self):        
        self.players_collision_bullet(self.game.projectiles)
        self.players_collision_sword()
        self.update_map_section(self.game.tilemap)
        self.update_players()
        
    def update_players(self):
        if self.player1.dead:
            self.player_death_effect(self.player1)
            self.reset_player(self.player1)
            self.player1.pos = [5,5] #temp
        
        if self.player2.dead:
            self.player_death_effect(self.player2)
            self.reset_player(self.player2)
            self.player2.pos = [5,5]
            
    def is_player_dashing(self, player):
        if abs(player.dashing) > 50:
            return True
        else:
            return False
    
    def is_player_shooting(self):
        pass
    
    def update_unlocked_section(self):
        #checking if unlocked players died
        if self.player1.dead and self.unlock[0]:
            self.unlock[0] = False
        if self.player2.dead and self.unlock[1]:
            self.unlock[1] = False
            
        #unlocking next section 
        if self.player2.dead:
            self.unlock[0] = True
        if self.player1.dead:
            self.unlock[1] = True
    
    def update_map_section(self, tilemap):
        self.update_unlocked_section()
        transition_tiles = tilemap.get_transition_tiles()

        for tile_rect in transition_tiles:
            if self.unlock[0] and self.player1.rect().colliderect(tile_rect):
                self.next_map(1)

            if self.unlock[1] and self.player2.rect().colliderect(tile_rect):
                self.next_map(2)

    def next_map(self, adv_player = 0):
        if adv_player:
            if adv_player == 1 and self.current_map < len(self.maps) - 1:
                self.current_map += 1
                self.game.load_level(self.current_map)
                
            if adv_player == 2 and self.current_map > 0:
                self.current_map -= 1
                self.game.load_level(self.current_map) 
            
            self.unlock = [False, False]
            self.game.next_map_effect()
            
    def players_collision_bullet(self, projectiles):
        for projectile in projectiles.copy():
            if not self.is_player_dashing(self.player1) and self.player1.rect().collidepoint(projectile[0]):
                self.player1.dead += 1
                projectiles.remove(projectile)
            
            if not self.is_player_dashing(self.player2) and self.player2.rect().collidepoint(projectile[0]):
                self.player2.dead += 1
                projectiles.remove(projectile)
    
    def players_collision_sword(self):
        #todo: find and use a sword png to do collision detection on. Similar to bullet
        pass    
    
    def player_death_effect(self, player):
        if player.dead:
            #creates an explosion like effect to make player deaths obvious 
            for i in range(30):
                angle = random.random() * math.pi * 2
                speed = random.random() * 5
                self.game.sparks.append(Spark(player.rect().center, angle,
                                              2 + random.random()))
                self.game.particles.append(Particle(self, 'particle', 
                                                    player.rect().center,
                                                    velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5],
                                                    frame=random.randint(0, 7)))
    
    def rect(self, player):
        #helper to convert pixels to rect 
        return pygame.Rect(player.pos[0], player.pos[1], player.size[0], player.size[1])
    
    #outside of the player class cause of a weird bug   
    def reset_player(self, player):
        player.air_time = 0
        player.jumps = 1
        player.wall_slide = False
        player.dashing = 0
        player.attacking = 0
        player.health = 10
        player.dead = 0
        player.gun = 1
        player.sword = 0
        player.velocity = [0,0]