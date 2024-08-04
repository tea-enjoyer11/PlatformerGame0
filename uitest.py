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
btn2 = Button(Rect(210, 10, 100, 100), image=make_icon_from_letter("G", (100, 100), (0, 0, 0), (125, 52, 217)))

lbl = Label(Rect(10, 10, 100, 30), text="ich bin ein label")
lbl.clip_text = True


while is_running:
    screen.fill((124, 42, 27))

    dt = clock.tick(30) * .001
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            is_running = False

        if event.type == UI_CLICK:
            if event.ui_element == btn1:
                print("btn1 clicked")
            if event.ui_element == btn2:
                print("btn2 clicked")
            # print("click  ", event)

        if event.type == UI_RELEASE:
            if event.ui_element == btn1:
                print("btn1 released")
            if event.ui_element == btn2:
                print("btn2 released")
            # print("release", event)

        # if event.type == pygame_gui.UI_BUTTON_PRESSED:
        #     if event.ui_element == hello_button:
        #         print('Hello World!')

        # if event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
        #     if event.ui_element == slider:
        #         print('current slider value:', event.value)
        #         textbox.set_text(str(event.value))

        # if event.type == pygame_gui.UI_TEXT_ENTRY_CHANGED:
        #     if event.ui_element == textbox:
        #         print("Changed text:", event.text)
        #         val = slider.get_current_value()
        #         try:
        #             val = max(100, min(int(event.text), 1000))
        #         except ValueError:
        #             print(f"Converting error: {event.text=}")
        #         slider.set_current_value(val)

        # manager.process_events(event)

    manager.update(dt)

    # manager.draw_ui(screen)
    manager.render_ui(screen)

    pygame.display.update()
