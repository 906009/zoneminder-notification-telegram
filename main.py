import os
import sys
import time
import telebot
import shutil
import zipfile
import threading
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler
#INIT
ver = "Неизвестно"
file_check = 0
root_path_bot = os.getcwd()+"/"
root_path_bot_config = root_path_bot + "config/"
if os.path.isdir(root_path_bot + "config")==False:
    os.makedirs(root_path_bot + "config", exist_ok=True)
    file_check = 1
if os.path.exists(root_path_bot_config + "cam_location.txt")==False:
    file = open(root_path_bot_config + "cam_location.txt", "w+")
    file.write("/locate/cam/events")
    file.close()
    file_check = 1
if os.path.exists(root_path_bot_config + "admin_list.txt")==False:
    file = open(root_path_bot_config + "admin_list.txt", "w+")
    file.write("id\ntelegram")
    file.close()
    file_check = 1
if os.path.exists(root_path_bot_config + "token.txt")==False:
    file = open(root_path_bot_config + "token.txt", "w+")
    file.write("token:telegram")
    file.close()
    file_check = 1
if (file_check == 1):
    quit()
if os.path.exists(root_path_bot + "ver.txt")==True:
    file = open(root_path_bot + "ver.txt", "r")
    ver = file.read()
    file.close()
with open(r"" + root_path_bot_config + "cam_location.txt", mode="r") as file:
    root_path_cam = file.read()
with open(r"" + root_path_bot_config + "admin_list.txt", mode="r") as file:
    admin_list = file.readlines()
with open(r"" + root_path_bot_config + "token.txt", mode="r") as file:
    token = file.read()
bot = telebot.TeleBot(token, threaded=False, skip_pending=True)
#Sender
def sender(event_line):
    if (event_line.find("snapshot.jpg")) > 0:
        if (event_line.find(root_path_cam + "/4")) > 0:
            img = event_line[event_line.find("'") + 1:event_line.find("jpg") + 3]
            time.sleep(5)
            for user_id in list(admin_list):
                try:
                    bot.send_photo(user_id, photo=open(img, 'rb'), caption="Активность на 4 камере!")
                except:
                    bot.send_message(user_id, "Активность на 4 камере!")
        if (event_line.find(root_path_cam + "/5")) > 0:
            img = event_line[event_line.find("'") + 1:event_line.find("jpg") + 3]
            time.sleep(5)
            for user_id in list(admin_list):
                try:
                    bot.send_photo(user_id, photo=open(img, 'rb'), caption="Активность на 5 камере!")
                except:
                    bot.send_message(user_id, "Активность на 5 камере!")
#Updater
@bot.message_handler(content_types=['document'])
def get_document(message):
    if str(message.from_user.id) in admin_list:
        file_info = bot.get_file(message.document.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        temp_folder = root_path_bot + "temp_update_folder"
        os.makedirs(temp_folder, exist_ok=True)
        file_path = os.path.join(temp_folder, message.document.file_name)
        with open(file_path, 'wb') as new_file:
            new_file.write(downloaded_file)
        version = get_version_from_archive(file_path)
        if version is None:
            bot.send_message(message.chat.id, "Не является обновлением")
            shutil.rmtree(os.path.dirname(file_path))
            return
        keyboard = InlineKeyboardMarkup()
        keyboard.row(InlineKeyboardButton("Установить", callback_data='install_update'))
        keyboard.row(InlineKeyboardButton("Отмена", callback_data='cancel_update'))
        bot.send_message(message.chat.id, f"Обновление готово к установке.\n{ver} ==> {version}\nУстановить сейчас?", reply_markup=keyboard)
        global file_to_update
        file_to_update = file_path
def get_version_from_archive(file_path):
    with zipfile.ZipFile(file_path, 'r') as zip_ref:
        if 'ver.txt' in zip_ref.namelist():
            with zip_ref.open('ver.txt') as ver_file:
                version = ver_file.read().decode('utf-8').strip()
            return version
        else:
            return None
@bot.callback_query_handler(func=lambda call: call.data == 'install_update')
def callback_install_update(call):
    bot.send_chat_action(call.message.chat.id, 'typing')
    global file_to_update
    bot_folder_path = root_path_bot
    update_bot_from_zip(file_to_update, bot_folder_path)
    shutil.rmtree(os.path.dirname(file_to_update))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Бот успешно обновлен.")
    os.execv(sys.executable, [sys.executable] + sys.argv)
@bot.callback_query_handler(func=lambda call: call.data == 'cancel_update')
def callback_cancel_update(call):
    bot.send_chat_action(call.message.chat.id, 'typing')
    global file_to_update
    shutil.rmtree(os.path.dirname(file_to_update))
    bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.message_id, text="Обновление отменено.")
def update_bot_from_zip(zip_file_path, bot_folder_path):
    for root, dirs, files in os.walk(bot_folder_path, topdown=False):
        for file in files:
            file_path = os.path.join(root, file)
            if file_path != zip_file_path:
                os.remove(file_path)
        for dir in dirs:
            dir_path = os.path.join(root, dir)
            if dir_path != os.path.dirname(zip_file_path):
                os.rmdir(dir_path)
    with zipfile.ZipFile(zip_file_path, 'r') as zip_ref:
        zip_ref.extractall(bot_folder_path)
@bot.message_handler(commands=['status'])
def status_message(message):
    stream = os.popen("systemctl status sshd")
    if str(message.from_user.id) in admin_list:
        bot.send_message(message.chat.id, f"Версия: {ver}\n\n" + stream.read())
#Polling
def polling_thread():
    while True:
        try:
            bot.polling(none_stop=True)
        except Exception as e:
            print(e)
            time.sleep(15)
polling_thread = threading.Thread(target=polling_thread)
polling_thread.start()
#Checker
class Handler(FileSystemEventHandler):
    def on_created(self, event):
        event_line = str(event)
        sender(event_line)
    #def on_deleted(self, event):
    #    print(event)
    #def on_moved(self, event):
    #    print(event)
observer = Observer()
observer.schedule(Handler(), path=root_path_cam, recursive=True)
observer.start()
try:
    while True:
        time.sleep(0.1)
except KeyboardInterrupt:
    observer.stop()
observer.join()


