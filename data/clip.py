import pygame

def clip(surf,x,y,x_size,y_size):
    clipR = pygame.Rect(x,y,x_size,y_size)
    surf.set_clip(clipR)
    image = surf.subsurface(surf.get_clip())
    return image.copy()