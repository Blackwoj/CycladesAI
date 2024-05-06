import pygame

from ....DataCache import DataCache
from ....static.EventConfig import EventConfig
from .AbstractMessageBox import AbstractMessageBox


class MessageBox(AbstractMessageBox):

    def __init__(self, screen: pygame.Surface):
        super().__init__(screen)

    def build_box(self, message):
        box_size = (500, 300)
        windows_size = pygame.display.get_window_size()
        window_center_setoff_box_size = [
            windows_size[0] // 2 - box_size[0] // 2,
            windows_size[1] // 2 - box_size[1] // 2
        ]
        self._screen.blit(self._loaded_bg[box_size], window_center_setoff_box_size)
        self.write_text(message, [windows_size[0] // 2, windows_size[1] // 2])
        warrior_config = DataCache.get_value("new_warrior_location")
        warriors_id = list(warrior_config.keys())[0]
        num_of_av_war = warrior_config[warriors_id]["num_of_entities"]
        self.build_button(num_of_av_war, self.locations(num_of_av_war, [80, 80], [windows_size[0] // 2, windows_size[1] // 2], box_size))

    def write_text(self, message, message_box_center):
        text = self.font.render(message, True, (0, 255, 0))
        text_rect = text.get_rect()
        text_rect.left = message_box_center[0] - text_rect.width // 2
        text_rect.top = message_box_center[1] - 100 - text_rect.height // 2
        self._screen.blit(text, text_rect)

    def build_button(self, num_of_ans, locations):
        for i in range(1, num_of_ans + 1):
            rect = pygame.rect.Rect(locations[i - 1][0], locations[i - 1][1], 80, 80)
            self._screen.blit(self._multiplayer_icon[i], rect)
            pos = pygame.mouse.get_pos()
            hit = rect.collidepoint(pos)
            if pygame.mouse.get_pressed()[0] == 1 and hit:
                warriors_data = DataCache.get_value("new_warrior_location")
                for key, data in warriors_data.items():
                    warriors_data[key]["num_of_entities"] = i
                DataCache.set_value("new_warrior_location", warriors_data)
                pygame.event.post(pygame.event.Event(EventConfig.UPDATE_WARRIOR_POS))

    def locations(self, num_of_icons, base_size, win_placing, win_size):
        offset = (win_size[1] // 2 // 3) * 1
        move_v = 15
        move_h = 15
        _locations = {
            1: [
                [
                    win_placing[0] - base_size[0] * 0.5,
                    win_placing[1] + offset
                ]
            ],
            2: [
                [
                    win_placing[0] - base_size[0] * 1.0 - 0.5 * move_v,
                    win_placing[1] + offset
                ],
                [
                    win_placing[0] + 0.5 * move_v,
                    win_placing[1] + offset
                ],
            ],
            3: [
                [
                    win_placing[0] - base_size[0] * 1.5 - move_v,
                    win_placing[1] + offset
                ],
                [
                    win_placing[0] - base_size[0] * 0.5,
                    win_placing[1] + offset
                ],
                [
                    win_placing[0] + base_size[0] * 0.5 + move_v,
                    win_placing[1] + offset
                ]
            ],
            4: [
                [
                    win_placing[0] - base_size[0] * 1.0 - 0.5 * move_v,
                    win_placing[1] - base_size[1] - move_h + offset
                ],
                [
                    win_placing[0] + 0.5 * move_v,
                    win_placing[1] - base_size[1] - move_h + offset
                ],
                [
                    win_placing[0] - base_size[0] * 1.0 - 0.5 * move_v,
                    win_placing[1] + offset
                ],
                [
                    win_placing[0] + 0.5 * move_v,
                    win_placing[1] + offset
                ],
            ],
            5: [
                [
                    win_placing[0] - base_size[0] * 1.0 - 0.5 * move_v,
                    win_placing[1] - base_size[1] - move_h + offset
                ],
                [
                    win_placing[0] + 0.5 * move_v,
                    win_placing[1] - base_size[1] - move_h + offset
                ],
                [
                    win_placing[0] - base_size[0] * 1.5 - move_v,
                    win_placing[1] + offset
                ],
                [
                    win_placing[0] - base_size[0] * 0.5,
                    win_placing[1] + offset
                ],
                [
                    win_placing[0] + base_size[0] * 0.5 + move_v,
                    win_placing[1] + offset
                ]
            ],
            6: [
                [
                    win_placing[0] - base_size[0] * 1.5 - move_v,
                    win_placing[1] - base_size[1] - move_h + offset
                ],
                [
                    win_placing[0] - base_size[0] * 0.5,
                    win_placing[1] - base_size[1] - move_h + offset
                ],
                [
                    win_placing[0] + base_size[0] * 0.5 + move_v,
                    win_placing[1] - base_size[1] - move_h + offset
                ],
                [
                    win_placing[0] - base_size[0] * 1.5 - move_v,
                    win_placing[1] + offset
                ],
                [
                    win_placing[0] - base_size[0] * 0.5,
                    win_placing[1] + offset
                ],
                [
                    win_placing[0] + base_size[0] * 0.5 + move_v,
                    win_placing[1] + offset
                ]
            ]
        }
        return _locations[num_of_icons]
