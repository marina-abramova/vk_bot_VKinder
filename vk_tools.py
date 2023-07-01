from datetime import datetime
import vk_api
from vk_api.exceptions import ApiError

import bot_interface
from config import access_token, developer_id, count
from pprint import pprint


class VkTools():
    def __init__(self, access_token):
        self.api = vk_api.VkApi(token=access_token)

    def _ages_calculate(self, bdate):    # вычисляем возраст пользователя
        user_year = int(bdate.split('.')[2])
        now = datetime.now().year
        return now - user_year

    def get_profile_info(self, user_id): # запросить с сервера данные о пользователе
        try:
            info = self.api.method('users.get',
                                   {'user_id': user_id,
                                    'fields': 'city, bdate, sex,'
                                    }
                                   )[0]
        except ApiError as err: # обработчик ошибок
            info = {}
            print(f' Ошибка ApiError: {err}')
            return None

        user_info = {'name': (info['first_name'] + ' ' + info[
            'last_name']) if 'first_name' in info and 'last_name' in info else None,
                     'id': info['id'],
                     'age': self._ages_calculate(info['bdate']) if 'bdate' in info else None,
                     'sex': info.get('sex'),
                     'city': info.get('city')['id'] if info.get('city') is not None else None
                     }
        return user_info

    def find_users(self, info, offset): #поиск профилей пользователей
        try:
            users = self.api.method('users.search',
                                    {'count': count,
                                     'offset': offset,
                                     # 'age_from': 25,
                                     # 'age_to': 35,
                                     'age_from': info['age'] - 5,
                                     'age_to': info['age'] + 5,
                                     'sex': 1 if info['sex'] == 2 else 2,
                                     'city': info['city'],  # ищем не в "Родном городе", а в том, который указан в контакте
                                     # 'status': 6,   # я хочу искать всех, а не только в активном поиске
                                     'is_closed': False
                                     }
                                    )
        except ApiError as err: # обработчик ошибок
            users = []
            print(f' Ошибка ApiError: {err}')
            return None

        res = []
        for user in users['items']:
            if user['is_closed'] == False:
                res.append({'id': user['id'],
                            'name': user['first_name'] + ' ' + user['last_name']
                            }
                           )
        return res

    def get_photos(self, id): # получить топ-фото из профиля
        try:
            photos = self.api.method('photos.get',
                                     {'owner_id': id,
                                      'album_id': 'profile',
                                      'extended': 1
                                      }
                                     )
        # обработчик ошибок
        except ApiError as err:
            photos = {}
            print(f' Ошибка ApiError: {err}')
            return None

        res = []

        for photo in photos['items']:
            res.append({'owner_id': photo['owner_id'],
                        'id': photo['id'],
                        'likes': photo['likes']['count'],
                        'comments': photo['comments']['count'],
                        }
            )
        # для определения популярности посчитаем лайки и каменты на фото
        res.sort(key=lambda x: x['likes'] + x['comments'], reverse=True)
        return res[0:3]

if __name__ == '__main__':
    bot = VkTools(access_token)

    info = bot.get_profile_info(developer_id)
    pprint(info)

    users = bot.find_users(info, offset=0)
    pprint(users)

    user = users.pop()

    photos = bot.get_photos(users[1]['id'])
    pprint(photos)

