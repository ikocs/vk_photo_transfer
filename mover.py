import re


class Mover:
    def __init__(self, vk, group_id):
        self.vk = vk
        self.group_id = group_id
        self.albums = self.get_albums()
        self.photos = self.get_photos()
        self.photos_id = self.get_photos_id()
        self.select_photos = self.find_select_photo()

        self.move()

    def get_albums(self):
        """Отдает словарь со всеми альбомами группы"""
        albums = self.vk.method('photos.getAlbums', {
            'owner_id': self.group_id
        })

        return albums['items']

    def get_sort_album(self):
        """Ищет альбом для отбора фотографий для переноса"""
        album_id = int()
        for item in self.albums:
            if 'Приём работ подписчиков' in item['title']:
                album_id = item['id']

        return album_id

    def get_photos(self):
        """Получает словарь с данными фото в сортируемом альбом"""
        album_id = self.get_sort_album()
        photos = self.vk.method('photos.get', {
            'owner_id': self.group_id,
            'album_id': album_id
        })

        return photos

    def get_photos_id(self):
        """Получает id фотографйи в сортируемом альбоме"""
        ids = []
        for ph in self.photos['items']:
            ids.append(ph['id'])

        return ids

    def photo_check(self, ph_comments):
        """
        Выбирает фото для переноса по комментариям
        :param ph_comments: комментарии к фото
        :return:
            True, текст комментария - если фото подходит
            False, None - если не подходит
        """
        for com in ph_comments['items']:
            if com['from_id'] == self.group_id:
                return True, com['text']
        return False, None

    def find_select_photo(self):
        """
        Ищет выбранных фото
        :return: словарь:
            id - уникальный номер фотографии
            comment - текст комментария от сообщества
            trans_album - название альбома, в который перенести фото
        """
        select_photos = []
        for id in self.photos_id:
            ph_comments = self.vk.method('photos.getComments',
                                    {
                                        'owner_id': self.group_id,
                                        'photo_id': id,
                                        'sort': 'desc'  # от старых к новым
                                    })
            status, text = self.photo_check(ph_comments)
            if status:
                trans_album = re.findall(r'«(.*)»', text)
                select_photos.append(dict(
                    id=id,
                    comment=text,
                    # Достает из комментария названия альбома в кавычках
                    trans_album=trans_album[0])
                )

        return select_photos

    def move(self):
        moved_qty = 0
        not_moved_qty = 0
        for photo in self.select_photos:
            move_status = False
            for album in self.albums:
                if photo['trans_album'] == album['title']:
                    status_dict = self.vk.method('photos.move', {
                        'owner_id': self.group_id,
                        'target_album_id': album['id'],
                        'photo_id': photo['id']
                    })
                    move_status = bool(status_dict)
                    break

            if not move_status:
                print('Не найден альбом для переноса для фото id: '
                      'https://vk.com/photo{}_{}'.format(self.group_id, photo['id']))
                not_moved_qty += 1
            else:
                moved_qty += 1

        print('Перенесено фотографий: {} шт. \n'
              'Не перенесено фотографий: {} шт.'
              .format(moved_qty, not_moved_qty))
