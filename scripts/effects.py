import math
import pygame
import random

class Particle:
    def __init__(self, game, p_type, pos, velocity=[0, 0], frame=0):
        self.game = game
        self.type = p_type
        self.pos = list(pos)
        self.velocity = list(velocity)
        self.animation = self.game.assets['particle/' + p_type].copy()
        self.animation.frame = frame
    
    def update(self):
        kill = False
        if self.animation.done:
            kill = True
        
        self.pos[0] += self.velocity[0]
        self.pos[1] += self.velocity[1]
        
        self.animation.update()
        
        return kill
    
    def render(self, surf, offset=(0, 0)):
        img = self.animation.img()
        surf.blit(img, (self.pos[0] - offset[0] - img.get_width() // 2, self.pos[1] - offset[1] - img.get_height() // 2))


class Spark:
    def __init__(self, pos, angle, speed):
        self.pos = list(pos)
        self.angle = angle
        self.speed = speed
    
    def update(self):
        #since position is in cartesian, and angle is polar, conversion is needed 
        self.pos[0] += math.cos(self.angle) * self.speed
        self.pos[1] += math.sin(self.angle) * self.speed
        
        self.speed = max(0, self.speed - 0.1)
        return not self.speed
    
    def render(self, surf, offset=(0, 0), color = (255,255,255)):
        #essentially creating a polygon. Has to handle a spark in each orientation.
        #casting points away from the center by adding cosine of angle*speed. 
        render_points = [
            (self.pos[0] + math.cos(self.angle) * self.speed * 3 - offset[0], self.pos[1] + math.sin(self.angle) * self.speed * 3 - offset[1]),
            (self.pos[0] + math.cos(self.angle + math.pi * 0.5) * self.speed * 0.5 - offset[0], self.pos[1] + math.sin(self.angle + math.pi * 0.5) * self.speed * 0.5 - offset[1]),
            (self.pos[0] + math.cos(self.angle + math.pi) * self.speed * 3 - offset[0], self.pos[1] + math.sin(self.angle + math.pi) * self.speed * 3 - offset[1]),
            (self.pos[0] + math.cos(self.angle - math.pi * 0.5) * self.speed * 0.5 - offset[0], self.pos[1] + math.sin(self.angle - math.pi * 0.5) * self.speed * 0.5 - offset[1]),
        ]
        pygame.draw.polygon(surf, color, render_points)
        

class EffectGenerator:
    def __init__(self, game, assets, transition):
        self.game = game
        self.assets = assets
        self.transition = transition

    def create_explosion(self, entity):
        for i in range(30):
                        angle = random.random() * math.pi * 2
                        speed = random.random() * 5
                        self.game.sparks.append(Spark(entity.rect().center, angle, 2 + random.random()))
                        self.game.particles.append(Particle(self, 'particle', 
                                                            entity.rect().center,
                                                            velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5],
                                                            frame=random.randint(0, 7)))
    
    def create_leaf(self, rect):
        if random.random() * 49999 < rect.width * rect.height:
                    pos = (rect.x + random.random() * rect.width, 
                           rect.y + random.random() * rect.height)
                    self.game.particles.append(Particle(self, 'leaf', pos, velocity=[-0.1, 0.3], frame=random.randint(0, 20)))
    
    def create_shooting_spark(self, projectile, is_flip = 0):
        pi = math.pi if is_flip else 0
        for i in range(4):
            self.game.sparks.append(Spark(projectile[-1][0], random.random() - 0.5 + pi, 2 + random.random()))       

    def create_collision_spark(self, projectile):
        for i in range(4):
            #shooting sparks left if projectile is going right and vice versa                                                           
            self.game.sparks.append(Spark(projectile[0], random.random() - 0.5 + (math.pi if projectile[1] > 0 else 0), 2 + random.random()))
    
    def create_transition(self, transition):
        pass
    
    def update_transition(self):
        pass
    
    def create_ball(self, entity):
        for i in range(20):
            angle = random.random() * math.pi * 2 #random angle within 360 deg
            speed = random.random() * 0.5 + 0.5 #random speed
            pvelocity = [math.cos(angle) * speed, math.sin(angle) * speed] #calculating based on speed and angle of particle
            self.game.particles.append(Particle(self.game, 'particle', entity.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))
            
    def create_damage(self, entity, amount = 1):
            for i in range(20 * amount):
                angle = random.random() * math.pi * 2 #random angle within 360 deg
                speed = (random.random() * 0.5 + 0.5)*2 #random speed
                pvelocity = [math.cos(angle) * speed, math.sin(angle) * speed] #calculating based on speed and angle of particle
                self.game.particles.append(Particle(self.game, 'blood', entity.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))
                
    def create_dead(self, entity):
        for i in range(50):
            angle = random.random() * math.pi * 2
            speed = random.random() * 8
            self.game.particles.append(Particle(self, 'blood', 
                                                entity.rect().center,
                                                velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5],
                                                frame=random.randint(0, 7)))
            self.game.particles.append(Particle(self, 'particle', 
                                                entity.rect().center,
                                                velocity=[math.cos(angle + math.pi) * speed * 0.5, math.sin(angle + math.pi) * speed * 0.5],
                                                frame=random.randint(0, 7)))
               
    def create_pickup(self, entity):
        for i in range(20):
            angle = random.random() * math.pi * 2 #random angle within 360 deg
            speed = (random.random() + 0.5) #random speed
            pvelocity = [math.cos(angle) * speed, math.sin(angle) * speed] #calculating based on speed and angle of particle
            self.game.particles.append(Particle(self.game, 'particle', entity.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))
        pass
    
    def create_pickup(self, entity):
        for i in range(20):
            angle = random.random() * math.pi * 2 #random angle within 360 deg
            speed = (random.random() + 0.5) #random speed
            pvelocity = [math.cos(angle) * speed, math.sin(angle) * speed] #calculating based on speed and angle of particle
            self.game.particles.append(Particle(self.game, 'particle', entity.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))
        pass
    
    def create_respawn(self, entity):
        for i in range(20):
            angle = random.random() * math.pi * 2 #random angle within 360 deg
            speed = random.random() * 0.5 + 0.5 #random speed
            pvelocity = [math.cos(angle) * speed, math.sin(angle) * speed] #calculating based on speed and angle of particle
            self.game.sparks.append(Spark(entity.rect().center, angle, 2 + random.random()))
            self.game.particles.append(Particle(self.game, 'particle', entity.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))
            
    def create_dash_stream(self, entity):
        pvelocity = [abs(entity.dashing) / entity.dashing * random.random() * 3, 0]
        self.game.particles.append(Particle(self.game, 'particle', entity.rect().center, velocity=pvelocity, frame=random.randint(0, 7)))
