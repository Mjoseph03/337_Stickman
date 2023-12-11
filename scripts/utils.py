import os
import fnmatch
import pygame

BASE_IMG_PATH = 'data/images/'

#helper methods that load in image assets 
def load_image(path):
    try:
        image = pygame.image.load(BASE_IMG_PATH + path).convert()
        #im not happy with this.. but were running out of time...
        #accidentally used a different background color for the idle player 2 sprite
        if fnmatch.fnmatch(path, 'entities/player2/idle/*'):
            image.set_colorkey((255,255,255))
        else:
            image.set_colorkey((0, 0, 0))
    except Exception as e:
        print(f"Failed to load {path}") 
    return image

def load_images(path):
    images = []
    try:
        for img_name in sorted(os.listdir(BASE_IMG_PATH + path)):
            images.append(load_image(path + '/' + img_name))
    except Exception as e:
        print(f"Failed to load {BASE_IMG_PATH + path}") 
    return images


class Animation:
    def __init__(self, images, img_dur=5, loop=True):
        self.images = images
        self.loop = loop
        self.img_duration = img_dur
        self.done = False
        self.frame = 0
    
    def copy(self):
        return Animation(self.images, self.img_duration, self.loop)
    
    def update(self):
        if self.loop:
            self.frame = (self.frame + 1) % (self.img_duration * len(self.images))
        else:
            self.frame = min(self.frame + 1, self.img_duration * len(self.images) - 1)
            if self.frame >= self.img_duration * len(self.images) - 1:
                self.done = True
    
    def img(self):
        return self.images[int(self.frame / self.img_duration)]