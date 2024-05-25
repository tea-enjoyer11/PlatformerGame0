from pygame import Vector2, Surface, Color
import pygame
import os
import pickle
import gzip
import random

BASE_SOUND_PATH = ""

if not pygame.mixer.get_init():
    pygame.mixer.init()


def load_image(path: str) -> Surface:
    i = pygame.image.load(path).convert()
    i.set_colorkey("black")
    return i


def lerp(start: float, end: float, time: float) -> float:
    return start + (end - start) * time


def Vector2Lerp(start: Vector2, end: Vector2, time: float) -> Vector2:
    return start + (end - start) * time


def dist(p1: Vector2, p2: Vector2) -> float:
    return ((p2[0] - p1[0]) ** 2 + (p2[1] - p1[1])) ** 0.5


def clamp(minimum, x, maximum):
    return max(minimum, min(x, maximum))


def clamp_bottom(minimun, x):
    return max(minimun, x)


def clamp_top(maximun, x):
    return min(maximun, x)


def random_color(step=1):
    return (random.randrange(0, 255, step), random.randrange(0, 255, step), random.randrange(0, 255, step))


sysFont = pygame.font.SysFont("arial", 24)


def drawText(screen: pygame.Surface, text: str, pos: tuple, font: pygame.Font = None,
             antialias: bool = True, color: tuple = (255, 255, 255), background_color: tuple = None):
    if not font:
        font = sysFont

    s = font.render(text, antialias, color, background_color)
    screen.blit(s, pos)


def hide_mouse(): pygame.mouse.set_visible(False)
def show_mouse(): pygame.mouse.set_visible(True)


def make_surface(size: tuple, color: tuple = None, color_key: tuple = None) -> pygame.Surface:
    s = pygame.Surface(size)
    if color:
        s.fill(color)
    if color_key:
        s.set_colorkey(color)
    return s


def cycle_sequence(arr: list | tuple) -> list | tuple:
    first = arr[0]
    arr[0] = arr[-1]
    arr[-1] = first
    return arr


def flatten_list(l: list):
    l_ = []
    if not isinstance(l, list | tuple):
        return []
    else:
        for i in l:
            if isinstance(i, list | tuple):  # Check if element is a list
                l_ += flatten_list(i)  # Recursively flatten nested list
            else:
                l_.append(i)
    return l_


def loadSound(path, volume=1):
    s = pygame.mixer.Sound(BASE_SOUND_PATH + path)
    s.set_volume(volume)
    return s


def loadSounds(path):
    sounds = []
    for soundName in sorted(os.listdir(BASE_SOUND_PATH + path)):
        sounds.append(loadSound(path + "/" + soundName))
    return sounds


def combineImages(images: list[Surface], pathToOverLayImage: str):
    overLayImage = load_image(pathToOverLayImage).convert_alpha()
    newImages = []
    for img in images:
        newImg = img.copy()
        newImg.blit(overLayImage, (0, 0))
        newImages.append(newImg)

    return newImages


def recolorImages(imgList: Surface, oldColor: Color, newColor: Color, blackKey: bool = False) -> list[Surface]:
    """Only recolors one color at a time! removes any previous .set_colorkey() calls"""
    recoloredImages = []
    for img in imgList:
        imgCopy = img.copy()
        imgCopy.fill(newColor)
        img.set_colorkey(oldColor)
        imgCopy.blit(img, (0, 0))
        if blackKey:
            imgCopy.set_colorkey((0, 0, 0))
        recoloredImages.append(imgCopy)

    return recoloredImages


def fillImgWithColor(surface: Surface, color: Color) -> Surface:
    """Fill all pixels of the surface with color, preserve transparency."""
    r, g, b = color
    pixel_array = pygame.PixelArray(surface)
    for x in range(surface.get_width()):
        for y in range(surface.get_height()):
            a = surface.get_at((x, y)).a  # Get the alpha value
            pixel_array[x, y] = (r, g, b, a)
    return pixel_array.make_surface()


def recolorSurface(img: Surface, newColor: Color) -> Surface:
    """Recolors all colors except black!"""
    img_copy = img.copy()
    pixel_array = pygame.PixelArray(img_copy)
    new_color_mapped = img_copy.map_rgb(newColor)

    # Iterate over pixels
    for x in range(img_copy.get_width()):
        for y in range(img_copy.get_height()):
            # Only change color if it's not black
            if pixel_array[x, y] != img_copy.map_rgb((0, 0, 0)):
                pixel_array[x, y] = new_color_mapped

    img_copy.set_colorkey((0, 0, 0))
    return img_copy


def reverseInts(list_: list) -> list:
    listCopy = []
    for pos in list_:
        if pos > 0:
            listCopy.append(-pos)
        else:
            listCopy.append(pos * -1)

    return listCopy


def circle_surf(radius: float, color: Color) -> Surface:
    surf = pygame.Surface((radius * 2, radius * 2))
    pygame.draw.circle(surf, color, (radius, radius), radius)
    surf.set_colorkey((0, 0, 0))
    return surf


def save_picke(obj: object) -> bytes:
    return pickle.dumps(obj)


def load_pickle(obj: bytes) -> object:
    return pickle.loads(obj)


def save_compressed_pickle(obj: object, compresslevel: int = 9) -> bytes:
    return gzip.compress(pickle.dumps(obj), compresslevel=compresslevel)


def load_compressed_pickle(obj: bytes) -> object:
    return pickle.loads(gzip.decompress(obj))
