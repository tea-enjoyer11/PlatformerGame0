import pygame
import pygame_gui
import pygame_gui.elements.ui_label
import pygame_gui.elements.ui_text_box
import pygame_gui.elements.ui_text_entry_box
# https://pygame-gui.readthedocs.io/en/latest/index.html

pygame.init()

pygame.display.set_caption('Quick Start')
window_surface = pygame.display.set_mode((800, 600))

background = pygame.Surface((800, 600))
background.fill(pygame.Color('#000000'))

manager = pygame_gui.UIManager((800, 600))

hello_button = pygame_gui.elements.UIButton(relative_rect=pygame.Rect((350, 275), (100, 50)),
                                            text='Say Hello',
                                            manager=manager)
slider = pygame_gui.elements.UIHorizontalSlider(relative_rect=pygame.Rect(110, 10, 500, 30),
                                                start_value=50,
                                                value_range=(100, 1000),
                                                manager=manager)
textbox = pygame_gui.elements.ui_text_entry_box.UITextEntryBox(pygame.Rect(10, 10, 90, 30),
                                                               "...",
                                                               manager)
lbl = pygame_gui.elements.ui_label.UILabel(pygame.Rect(10, 100, 90, 30),
                                           "label!",
                                           manager)
clock = pygame.time.Clock()
is_running = True

while is_running:
    time_delta = clock.tick(60) / 1000.0
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            is_running = False

        if event.type == pygame_gui.UI_BUTTON_PRESSED:
            if event.ui_element == hello_button:
                print('Hello World!')

        if event.type == pygame_gui.UI_HORIZONTAL_SLIDER_MOVED:
            if event.ui_element == slider:
                print('current slider value:', event.value)
                textbox.set_text(str(event.value))

        if event.type == pygame_gui.UI_TEXT_ENTRY_CHANGED:
            if event.ui_element == textbox:
                print("Changed text:", event.text)
                val = slider.get_current_value()
                try:
                    val = max(100, min(int(event.text), 1000))
                except ValueError:
                    print(f"Converting error: {event.text=}")
                slider.set_current_value(val)

        manager.process_events(event)

    manager.update(time_delta)

    window_surface.blit(background, (0, 0))
    manager.draw_ui(window_surface)

    pygame.display.update()
