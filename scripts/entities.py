import pygame

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
        frame_movement = (movement[0] + self.velocity[0], movement[1] + self.velocity[1])

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
        
        for rect in tilemap.get_physics_rects(self.pos):
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
        
        for rect in tilemap.get_physics_rects(self.pos):
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
        surf.blit(pygame.transform.flip(self.animation.img(), self.flip, False),
                  (self.pos[0] - offset[0] + self.anim_offset[0], self.pos[1] - offset[1] + self.anim_offset[1]))
   
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
        # if keys[self.controls['pause']]:
        #     if self.player.ispaused:
        #         self.player.ispaused = False
        #     else:
        #         self.player.ispaused = True
        
        return movement[1] - movement[0]  


class Player(Physics):
    def __init__(self, game, pos, size, entity = 'player'):
        super().__init__(game, entity, pos, size)
        self.weapon = Weapon(game, self)
        self.entity = entity
        self.respawn_pos = 0
        self.air_time = 0
        self.ispaused = False #added
        self.jumps = 1
        self.wall_slide = False
        self.dashing = 0
        self.attacking = 0
        self.attack_cooldown = 0
        self.damage = 0
        self.dead = 0
        self.need_reset = False
         
    def update(self, tilemap, movement=(0, 0)):
        super().update(tilemap, movement=movement)
           
        self.check_collisions(movement)
        self.update_status()
        self.update_movement()
        self.weapon.update()
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
    
    #updates based on environment collisions
    def check_collisions(self, movement):
        #checking for free falling, kinda bad
        self.air_time += 1
        if self.air_time > 120:
            if not (self.collisions['right'] and self.collisions['left']):
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

    #updates and normalizes player movements
    def update_movement(self):
        self.dash_movement()
        
        #normalizing x axis movement         
        if self.velocity[0] > 0:
            self.velocity[0] = max(self.velocity[0] - 0.1, 0)
        else:
            self.velocity[0] = min(self.velocity[0] + 0.1, 0)
            
    # def pause(self):
    #         pygame.draw.rect(self.game.display, (128, 128, 128, 110), (0, 0, 900, 600))
    #         self.game.screen.blit(self.game.display, (0, 0))
    
    #renders player based on current state and weapon type
    def render(self, surf, offset=(0, 0)):
        if abs(self.dashing) <= 50:
            super().render(surf, offset=offset)
        
        #renders the weapons on top of the players if they aren't wall sliding or dashing
        if (self.action != 'wall_slide' and not self.is_dashing()):
            self.weapon.render(surf, offset=offset)
    
    #simple jumping, only complexity is having to account for wall sliding      
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
    
    #assigning dashing movement
    def dash(self):
        if not self.dashing:
            # self.game.sfx['dash'].play()
            if self.flip:
                self.dashing = -60
            else:
                self.dashing = 60
    
    #dash normalizing and particle stream effect 
    def dash_movement(self):
        if abs(self.dashing) in {60, 50}:
            self.game.effects.create_ball(self)
             
        #normalizing dashing after its been executed
        if self.dashing > 0:
            self.dashing = max(0, self.dashing - 1)
        if self.dashing < 0:
            self.dashing = min(0, self.dashing + 1)
        
        #finding the direction of a dash by using the first 10 frames
        if abs(self.dashing) > 50:
            self.velocity[0] = abs(self.dashing) / self.dashing * 8
            
            #dampening the dash after 10 frames, works as a cooldown 
            if abs(self.dashing) == 51:
                self.velocity[0] *= 0.1

            self.game.effects.create_dash_stream(self)
    
    def is_dashing(self):
        if abs(self.dashing) > 50:
            return True
        else:
            return False
    
    def attack(self):
        if self.attack_cooldown == 0:
            self.attacking += 1
            self.attack_cooldown = 10
        
    #checking for damage, and if battle manager reset player
    def update_status(self):
        if self.damage > 3:
            self.dead += 1
        
        if self.dead and self.need_reset:
            self.game.effects.create_dead(self)
            self.reset_self()

        #if self.ispaused:
        #     self.pause()
    
    #used by the battle manager to initiate a reset 
    def check_reset(self):
        if self.dead:
            self.need_reset = True
    
    #used by the battle manager to initiate a reset 
    def check_reset(self):
        if self.dead:
            self.need_reset = True
    
    def reset_self(self):
        self.air_time = 0
        self.jumps = 1
        #self.pause = 0 #added
        self.dead = 0
        self.wall_slide = False
        self.dashing = 0
        self.attacking = 0
        self.damage = 0
        self.respawn_self()
        
    #used by weapon class to assign damage based on the object 
    def assign_damage(self, object = 'dash'):
        if object == 'sword':
            self.damage += 1.5
            self.game.effects.create_damage(self, 2)
            
        if object == 'bullet':
            self.damage += 4
        else:
            self.damage += 1
            self.game.effects.create_damage(self)
    
    #spawns player in based on the spawner position in the map
    def respawn_self(self):
        #need to create a copy of respawn_pos, otherwise pos and respawn_pos become shared references
        self.pos = list(self.respawn_pos)
        self.need_reset = False
        self.game.effects.create_respawn(self)
        
    def push(self):
        if self.flip and self.last_movement[0] < 0:
            self.velocity[0] = 3.5
            self.velocity[1] = -2.5

        elif not self.flip and self.last_movement[0] > 0:
            self.velocity[0] = -3.5
            self.velocity[1] = -2.5

            
class BattleManager:
    def __init__(self, game, player1, player2):
        self.game = game
        self.player1 = player1
        self.player2 = player2
        self.unlock = [False, False]
        self.maps = [0,1,2,3,4,5,6,7,8]
        self.current_map = 4
    
    def update(self):        
        self.update_map_section(self.game.tilemap)
        self.check_players_status()
    
    #using helper methods inside player class to check their state
    def check_players_status(self):
        for player in [self.player1, self.player2]:
            self.check_weapon_pickup(player, self.game.tilemap)
            player.check_reset()
            player.update_status()
    
    #checks if any players died to update their unlock status
    def update_unlocked_section(self):
        if self.player1.dead and self.unlock[0]:
            self.unlock[0] = False
        if self.player2.dead and self.unlock[1]:
            self.unlock[1] = False
            
        if self.player2.dead:
            self.unlock[0] = True
        if self.player1.dead:
            self.unlock[1] = True
    
    #checks if players unlocked, and if they hit the appropriate tile
    def update_map_section(self, tilemap):
        self.update_unlocked_section()
        for tile_rect in tilemap.get_transition_tiles_loc():
            if self.unlock[0] and self.player1.rect().colliderect(tile_rect):
                self.next_map(1)

            if self.unlock[1] and self.player2.rect().colliderect(tile_rect):
                self.next_map(2)

    #checks if a player picks up a spawned in weapon
    def check_weapon_pickup(self, player, tilemap):
        for tile_rect in tilemap.get_gun_tile_loc():
            if player.rect().colliderect(tile_rect):
                player.weapon.change_weapon('gun')
                tilemap.despawn_gun_tile()    

    #logic behind changing maps
    def next_map(self, adv_player = 0):
        if adv_player:
            #prevents the game from attempting to load a map that doesn't exist
            if adv_player == 1 and self.current_map < len(self.maps) - 1:
                self.current_map += 1
                self.game.load_level(self.current_map)
                
            if adv_player == 2 and self.current_map > 0:
                self.current_map -= 1
                self.game.load_level(self.current_map) 
            
            self.unlock = [False, False]
            for player in[self.player1, self.player2]:
                player.reset_self()
                
            self.game.next_map_effect()
    

class Weapon:
    def __init__(self, game, player, weapon = 'sword'):
        self.player = player
        self.game = game
        self.weapon = weapon
        self.enabled = True
        self.hitbox = 0
        self.gun_pos = 0       
        self.sword_width = self.game.assets['sword'].get_width()
        self.sword_height = self.game.assets['sword'].get_height()
        self.gun_width = self.game.assets['gunImg'].get_width()       
        self.gun_height = self.game.assets['gunImg'].get_height()
        self.count_shots = 0
        
    def enable(self):
        self.enabled = True
    
    def disable(self):
        self.enabled = False
    
    def update(self):
        if self.enabled:
            if self.weapon == 'sword':
                self.update_sword()
                
            if self.weapon == 'gun':
                self.update_gun()
                if self.count_shots > 5:
                    self.change_weapon()
                
        self.projectile_collisions()
        self.sword_collisions()
        
    def update_gun(self):
        if self.player.flip:
            gun_x = self.player.pos[0] - self.gun_width
        else:
            gun_x = self.player.pos[0] + self.player.size[0]

        gun_y = self.player.pos[1] + (self.player.size[1] - self.gun_height) // 2
        self.gun_pos = (gun_x, gun_y)
        
        if self.player.attacking:
            self.shoot_projectile()
            self.player.attacking = 0
    
    def update_sword(self):
        if self.player.flip:
            sword_x = self.player.pos[0] - self.sword_width
        else:
            sword_x = self.player.pos[0] + self.player.size[0]
        sword_y = self.player.pos[1] + (self.player.size[1] - self.sword_height) // 2
        self.hitbox = pygame.Rect(sword_x, sword_y, self.sword_width, self.sword_height)
        
        if self.player.attacking:
            self.sword_collisions()
            self.player.attacking = 0

    def change_weapon(self, new_weapon = 'sword'):
        self.weapon = new_weapon
        self.game.effects.create_pickup(self.player)

    def shoot_projectile(self):
        #self.game.sfx['shoot'].play()
        self.count_shots += 1
        projectile_speed = -1.5 if self.player.flip else 1.5
        self.game.projectiles.append([[self.gun_pos[0], self.gun_pos[1] + self.gun_height // 2], projectile_speed, 0])
        self.game.effects.create_shooting_spark(self.game.projectiles, self.player.flip)

    def projectile_collisions(self):
        for projectile in self.game.projectiles.copy():
            if not self.player.is_dashing() and self.player.rect().collidepoint(projectile[0]):
                self.player.assign_damage('bullet')
                self.game.projectiles.remove(projectile)
    
    def sword_collisions(self):
        for opponent in self.game.players:
            if opponent != self.player:
                if self.hitbox.colliderect(opponent.rect()) and self.player.attacking:
                    opponent.assign_damage('sword')
    
    def render(self, surf, offset=(0, 0)):
        if self.enabled:
            if self.weapon == 'sword':
                cooldown_offset = 3 if self.player.attack_cooldown > 0 else 0
                weapon_pos = (self.hitbox.x - offset[0], self.hitbox.y - offset[1] + cooldown_offset)
                if self.player.flip:
                    surf.blit(pygame.transform.flip(self.game.assets['sword'], True, False), weapon_pos)
                else:
                    surf.blit(self.game.assets['sword'], weapon_pos)
            
            if self.weapon == 'gun':
                weapon_pos = (self.gun_pos[0] - offset[0], self.gun_pos[1] - offset[1])
                if self.player.flip:
                    surf.blit(pygame.transform.flip(self.game.assets['gunImg'], True, False), weapon_pos)
                else:
                    surf.blit(self.game.assets['gunImg'], weapon_pos)
                