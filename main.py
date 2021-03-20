# -*- coding: utf-8 -*-
import json

import vk_api
import vk_api.exceptions
import vk_api.tools

from mover import Mover


def captcha_handler(captcha):
    """ При возникновении капчи вызывается эта функция и ей передается объект
        капчи. Через метод get_url можно получить ссылку на изображение.
        Через метод try_again можно попытаться отправить запрос с кодом капчи
    """

    key = input("Enter captcha code {0}: ".format(captcha.get_url())).strip()

    # Пробуем снова отправить запрос с капчей
    return captcha.try_again(key)


def auth_handler():
    """ При двухфакторной аутентификации вызывается эта функция."""

    # Код двухфакторной аутентификации
    key = input("Enter authentication code: ")
    # Если: True - сохранить, False - не сохранять.
    remember_device = True

    return key, remember_device


def vk_auth(login, password, token):
    vk = vk_api.VkApi(login, password,
                      token=token,
                      # функция для обработки двухфакторной аутентификации
                      auth_handler=auth_handler,
                      captcha_handler=captcha_handler)

    try:
        # Авторизируемся
        vk.auth()
    except vk_api.AuthError as e:
        print(e)  # В случае ошибки выведем сообщение
        quit()

    return vk


def main():
    """Основная логика работы скрипта"""
    with open("config.json", "r", encoding="utf-8") as file:
        config = json.load(file)

    login = config['login']
    password = config['password']
    token = config['token']
    group_id = config['group_id']

    vk_session = vk_auth(login, password, token)

    move = Mover(vk_session, group_id)
    # logging.debug('Перенос завершен')


# if __name__ == '__main__':
main()
input('Нажмиты любую клавишу, чтобы выйти...')

