import vk_api
from vk_api.longpoll import VkLongPoll, VkEventType
from vk_api.utils import get_random_id
from vk_api.exceptions import ApiError

import vk_tools, database_tools
from config import community_token, developer_id, access_token, count, DSN
from pprint import pprint


class BotInterface():

    def __init__(self, community_token, access_token):
        self.vk = vk_api.VkApi(token=community_token)
        self.api = vk_tools.VkTools(access_token)
        self.engine = database_tools.create_engine(DSN)
        self.info = {}  # информация о профиле пользователя
        self.profiles = []
        self.offset = 0
        self.data = None  # флаг для ввода данных

    def _profiles_proc_2(self, user_id, profile):  # обработка профиля, получить из него фотографии
        photostr = ''
        while not database_tools.check_user(self.engine, user_id, profile["id"]):
            photos = self.api.get_photos(profile['id'])
            for photo in photos:
                photostr += f'photo{photo["owner_id"]}_{photo["id"]},'

            self.msg_send(user_id, f'Имя "{profile["name"]}, ссылка: vk.com/id{profile["id"]}', attachment=photostr)
            database_tools.add_user(self.engine, user_id, profile["id"])  # внесем этот профиль в просмотренные
            return True
        else:
            return False

    def _check_user(self, user_id):  # проверка полноты информации о пользователе
        if self.info['age'] is None:
            self.msg_send(user_id,
                          f'Введите Ваш возраст')
            self.data = 'age'

        elif self.info['sex'] is None:
            self.msg_send(user_id,
                          f'Вы мужчина или женщина? (М/Ж):')
            self.data = 'sex'
        else:
            return True

    def _profiles_proc(self, user_id):  # обработка профиля, получить из него фотографии
        photostr = ''
        while self.profiles:
            profile = self.profiles.pop()  # вытащим очередной и проверим был ли он в просмотренных
            if not database_tools.check_user(self.engine, user_id, profile['id']):
                photos = self.api.get_photos(profile['id'])
                for photo in photos:
                    photostr += f'photo{photo["owner_id"]}_{photo["id"]},'

                self.msg_send(user_id, f'Имя "{profile["name"]}, ссылка: vk.com/id{profile["id"]}', attachment=photostr)
                database_tools.add_user(self.engine, user_id, profile["id"])  # внесем этот профиль в просмотренные
                # print(f'Обработан профиль id= {profile["id"]} имя= {profile["name"]}')
                break
            else:
                pass
                # print(f'Пропущен профиль id= {profile["id"]} имя= {profile["name"]}')

    # отправка сообщения для пользователя
    def msg_send(self, user_id, message, attachment=None):
        self.vk.method('messages.send', {'user_id': user_id,
                                         'message': message,
                                         'attachment': attachment,
                                         'random_id': get_random_id()
                                         })

    # прием сообщений в чате и обработка по ключевым словам
    def msg_handler(self):
        longpoll = VkLongPoll(self.vk)

        # В рамках данного проекта реализован диалог только с одним пользователем
        for event in longpoll.listen():
            if event.type == VkEventType.MESSAGE_NEW and event.to_me:
                msg = event.text.lower()

                if self.data is None:  # ожидаем ввод команды
                    if msg == 'привет' or msg == 'hi':
                        # получить инфо о написавшем пользователе
                        self.info = self.api.get_profile_info(event.user_id)
                        self.msg_send(event.user_id, f'Привет, {self.info["name"]}')

                    elif msg == 'поиск' or msg == 'fi':
                        if self.info:
                            if (self.info['age'] is not None) and (self.info['sex'] is not None):

                                self.msg_send(event.user_id, f'Ищем... ')
                                while not self.profiles:  # запросить с сервера очередную порцию анкет? если не были загружены
                                    self.profiles = self.api.find_users(self.info, self.offset)
                                    self._profiles_proc(event.user_id)  # обработать очередной профиль
                                    self.offset += count
                                    break
                                else:  # если анкеты уже загружены в память
                                    self._profiles_proc(event.user_id)  # обработать очередной профиль
                            else:
                                self._check_user(event.user_id)  # проверить пользователя на полноту данных о себе
                        else:
                            self.msg_send(event.user_id, f'Давайте познакомимся, введите команду Привет(/Hi)')

                    elif msg == 'пока' or msg == 'bye':
                        self.msg_send(event.user_id, f'До свидания, {self.info["name"]} !')
                        self.info = None
                        self.profiles = None
                    else:
                        self.msg_send(event.user_id, f'Неизвестная команда "{msg}" !')
                        self.msg_send(event.user_id, 'Поддерживаются команды: Привет(Hi), Поиск(Fi), Пока(Bye)')

                else:  # ожидаем ввод данных

                    if 'age' in self.data:
                        self.info['age'] = int(msg)
                        self.data = None
                    elif 'sex' in self.data:
                        self.info['sex'] = 2 if (msg == 'м' or msg == 'm') else 1
                        self.data = None
                    else:
                        pass

if __name__ == '__main__':
    try:
        bot = BotInterface(community_token, access_token)
        bot.msg_handler()
    except ApiError as err:
        print(f' Ошибка {err}')
