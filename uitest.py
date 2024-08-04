import pygame
from Scripts.Ui import *
from pygame import Rect


def p(a, b, c): print("hello", a, b, c)
def p1(a, b, c): print("bye", a, b, c)


pygame.init()

pygame.display.set_caption('Quick Start')
screen = pygame.display.set_mode((800, 600))

clock = pygame.time.Clock()
is_running = True

manager = get_ui_manager()

icon = make_icon_from_letter("R", (100, 100), (0, 0, 0), (125, 52, 217))
btn1 = Button(Rect(100, 10, 100, 100), image=icon)
btn2 = Button(Rect(210, 10, 100, 100), image=make_icon_from_text("btn2", (100, 100), (0, 0, 0), (125, 52, 217)))

lbl = Label(Rect(10, 10, 100, 30), text="ich bin ein label", z_index=1)
lbl.clip_text = True

slider1 = SliderHorizontal(Rect(20, 250, 300, 25), 0, 100)
slider2 = SliderVertical(Rect(500, 50, 30, 450), 0, 200)


while is_running:
    screen.fill((124, 42, 27))

    dt = clock.tick(30) * .001
    for event in pygame.event.get():
        if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
            is_running = False

        if event.type == UI_CLICK:
            if event.ui_element == btn1:
                print("btn1 clicked")
            if event.ui_element == btn2:
                print("btn2 clicked")

        if event.type == UI_RELEASE:
            if event.ui_element == btn1:
                print("btn1 released")
            if event.ui_element == btn2:
                print("btn2 released")

        if event.type in {UI_CLICK, UI_RELEASE, UI_HOVER_ENTER, UI_HOVER, UI_HOVER_EXIT, UI_SLIDER_HORIZONTAL_MOVED, UI_SLIDER_VERTICAL_MOVED}:
            print(event)

        manager.process_event(event)

    manager.update(dt)

    manager.render_ui(screen)
    manager.render_debug(screen)

    pygame.display.update()
