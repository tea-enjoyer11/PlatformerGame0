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
btn1 = Button(Rect(20, 20, 100, 100))
btn1.on_click = p
btn1.on_click_params = (23.1, 2.321, 0.01)
btn1.on_release = p1
btn1.on_release_params = (32, 223.1, 2.321)

lbl = Label(Rect(10, 10, 100, 30), text="ich bin ein label")
lbl.clip_text = True


icon = make_icon_from_letter("R", (200, 100), (0, 0, 0), (125, 52, 217))


while is_running:
    dt = clock.tick(60) * .001
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            is_running = False

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

    screen.fill((124, 42, 27))
    # manager.draw_ui(screen)

    manager.render(screen)

    screen.blit(icon, (200, 100))

    pygame.display.update()
