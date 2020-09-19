import re
import logging
import vk_api.exceptions
from vk_api.tools import VkTools
from datetime import datetime as dt


def config_logger(logger):
    logger.setLevel(logging.DEBUG)
    f_handler = logging.StreamHandler()

    formatter = logging.Formatter('%(asctime)s - %(filename)s - %(levelname)s - %(message)s')
    f_handler.setFormatter(formatter)

    logger.addHandler(f_handler)


class Mover:
    def __init__(self, vk, group_id):
        self.vk = vk
        self.group_id = group_id

        self.albums = self.get_albums()
        self.id_albums_dict = self.make_id_albums_dict()
        self.select_album = self.get_sort_album()

        self.album_comments = self.load_album_comments()

        self.transfer_data = self.find_select_photo()

        self.logger = logging.getLogger('__name__')
        config_logger(self.logger)

        self.move()
        self.creat_new_album()
        
    def get_albums(self):
        """Отдает словарь со всеми альбомами группы"""
        albums = self.vk.method('photos.getAlbums', {
            'owner_id': self.group_id
        })

        return albums['items']

    def make_id_albums_dict(self):
        """Составляет словарь {название альбома:id альбома}"""
        ids_dict = dict()
        for album in self.albums:
            ids_dict.setdefault(album['title'], album['id'])

        return ids_dict

    def get_sort_album(self):
        """Ищет альбом для отбора фотографий для переноса"""
        album_id = int()
        for item in self.albums:
            if 'Приём работ подписчиков' in item['title']:
                album_id = item['id']

        return album_id

    def load_album_comments(self):
        """Функци получения всех комментариев к альбому"""
        tools = VkTools(self.vk)
        params = {
            'owner_id': self.group_id,
            'album_id': self.select_album
        }
        comments = tools.get_all(method='photos.getAllComments',
                                 max_count=100,
                                 values=params)

        return comments['items']

    def find_select_photo(self):
        transfer_data = list()
        for com in self.album_comments:
            if com['from_id'] == self.group_id:
                transfer_data.append({
                    'photo_id': com['pid'],
                    'album': re.findall(r'«(.*)»', com['text'])[0]
                })

        return transfer_data

    def move(self):
        moved_qty = 0
        not_moved_qty = 0
        move_status = False

        # TODO Из-за изменения данных код ниже не работает
        for photo in self.transfer_data:
            target_album = photo['album']
            try:
                vk_response = self.vk.method('photos.move', {
                    'owner_id': self.group_id,
                    'target_album_id': self.id_albums_dict[target_album],
                    'photo_id': photo['photo_id']
                })
                move_status = bool(vk_response)
            except KeyError:
                logging.error('Не найден альбом с названием '
                              '"{name}"'.format(name=target_album))
            except vk_api.exceptions.ApiError:
                logging.error('API VK ERROR')

            if not move_status:
                self.logger.error('Не найден альбом для переноса для фото id: '
                                  'https://vk.com/photo{}_{}'.format(self.group_id, photo['id']))
                not_moved_qty += 1
            else:
                moved_qty += 1

        self.logger.debug('Перенесено фотографий: {} шт.'.format(moved_qty))
        self.logger.debug('Не перенесено фотографий: {} шт.'.format(not_moved_qty))
        
    def creat_new_album(self):
        now = dt.now()
        month_dict = {
            1: 'января',
            2: 'февраля',
            3: 'марта',
            4: 'апреля',
            5: 'мая',
            6: 'июня',
            7: 'июля',
            8: 'августа',
            9: 'сентября',
            10: 'Октября',
            11: 'ноября',
            12: 'декабря',
        }
        current_month: int = now.month
        current_day: str = str(now.day)
        
        new_album_id = self.vk.method('photos.createAlbum', {
            'title': 'Test', #.format(
            #     day='1',
            #     month=month_dict[current_month]),
            'group_id': -15146996
        })
        
        self.logger.debug('Создан альбом: {}'.format(new_album_id['id']))
