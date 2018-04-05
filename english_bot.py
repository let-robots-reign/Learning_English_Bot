from telegram.ext import Updater, MessageHandler, CommandHandler, Filters, ConversationHandler
from telegram import ReplyKeyboardMarkup
from database import *
import requests
import sys

try:
    with open("tokens.txt", 'r', encoding="utf8") as infile:
        TOKEN, API_KEY = (line.strip() for line in infile.readlines())
except FileNotFoundError:
    print("Для работы нужен Telegram Token и Yandex Translate Key")
    sys.exit(1)


START_DIALOGUE, TRANSLATE, DICT_ADDING = range(3)

lang_keyboard = [["русский", "английский"]]
markup = ReplyKeyboardMarkup(lang_keyboard, one_time_keyboard=True)


def setting_up(bot, update):
    data_base = DataBase()
    data_base.create_table(update.message.from_user.first_name, update.message.from_user.last_name)
    update.message.reply_text(
        "Выберите язык, на котором я буду с вами говорить."
        "\n\n"
        "Choose the language I will speak.",
        reply_markup=markup
    )
    data_base.close()
    return START_DIALOGUE


def start_dialogue(bot, update, user_data):
    if update.message.text == "русский":
        user_data["lang_spoken"] = "ru"
        update.message.reply_text(
            "Здравствуй! Я бот, который помогает учить английский. Я могу переводить для вас любые слова и фразы, "
            "а позже вы можете добавлять их в свой личный словарь, после чего тренировать с помощью "
            "различных упражнений.\n"
            "Список и описание упражнений можно посмотреть, вызвав команду /rules. "
            "Также вы можете все стереть и начать заново с помощью команды /reset.\n"
            "Давайте начнем!"
        )
        update.message.reply_text(
            'Чтобы передать мне слово или фразу на перевод, напишите мне "переведи (мне) / translate %слово%" '
            'либо же просто "%слово%". '
            'После этого вы сможете выбрать, добавлять ли слово в ваш словарь.'
        )

        user_data["words_num"] = 0

        return TRANSLATE

    elif update.message.text == "английский":
        user_data["lang_spoken"] = "en"
        update.message.reply_text(
            "Hello! I'm a bot that is constructed for learning English. I can translate any word or phrase for you, "
            "and after that you can add it to your dictionary and learn with several types of trainings "
            "whenever you want.\n"
            "You can look up the list of trainings via /rules command. "
            "Also, you can reset all your data and start from the beginning using /reset command.\n"
            "Let's get started!"
        )
        update.message.reply_text(
            'To transfer a word for translation, write "переведи (мне) / translate %word%" or just "%word%". '
            'Afterwards, you can decide whether you want to add it to your dictionary or not.'
        )

        user_data["words_num"] = 0

        return TRANSLATE

    else:
        update.message.reply_text(
            "Вы еще не выбрали язык, на котором я буду говорить."
            "\n\n"
            "You haven't chosen the language I'll be speaking.",
            reply_markup=markup
        )


def translate_handling(bot, update, user_data):
    if "translate" == update.message.text.lower().split()[0]:
        text_to_translate = ' '.join(update.message.text.split()[1:])
        lang = detect_lang(text_to_translate)
        translation = translator(text_to_translate, lang)
        update.message.reply_text(translation)

    elif "переведи" == update.message.text.lower().split()[0]:
        if "переведи мне" in update.message.text.lower():
            text_to_translate = ' '.join(update.message.text.split()[2:])
            lang = detect_lang(text_to_translate)
            translation = translator(text_to_translate, lang)
            update.message.reply_text(translation)
        else:
            text_to_translate = ' '.join(update.message.text.split()[1:])
            lang = detect_lang(text_to_translate)
            translation = translator(text_to_translate, lang)
            update.message.reply_text(translation)

    else:
        text_to_translate = ''.join(update.message.text)
        lang = detect_lang(text_to_translate)
        translation = translator(text_to_translate, lang)
        update.message.reply_text(translation)

    if lang == "ru-en":
        user_data["current_word"] = translation.split("\n\n")[0]
        user_data["current_translation"] = text_to_translate
    elif lang == "en-ru":
        user_data["current_word"] = text_to_translate
        user_data["current_translation"] = translation.split("\n\n")[0]

    if user_data["lang_spoken"] == "ru":
        update.message.reply_text(
            "Добавить это слово в словарь?"
        )
    elif user_data["lang_spoken"] == "en":
        update.message.reply_text(
            "Do you want to add this to your dictionary?"
        )

    return DICT_ADDING


def translator(text, lang):
    accompanying_text = "Переведено сервисом «Яндекс.Переводчик» http://translate.yandex.ru/."
    translator_url = "https://translate.yandex.net/api/v1.5/tr.json/translate"
    response = requests.get(
        translator_url,
        params={
            "key": API_KEY,
            "lang": lang,
            "text": text
        })
    return "\n\n".join([response.json()["text"][0], accompanying_text])


def detect_lang(text):
    detector_url = "https://translate.yandex.net/api/v1.5/tr.json/detect"
    response = requests.get(
        detector_url,
        params={
            "key": API_KEY,
            "text": text,
            "hint": "ru,en"
        })
    result = response.json()["lang"]
    return result + "-ru" if result == "en" else result + "-en"


def adding_to_dict(bot, update, user_data):
    if update.message.text.lower() == "да" or update.message.text.lower() == "yes":

        data_base = DataBase()
        data_base.create_table(update.message.from_user.first_name, update.message.from_user.last_name)
        data_base.inserting(user_data["words_num"], user_data["current_word"], user_data["current_translation"])
        user_data["words_num"] += 1

        if user_data["lang_spoken"] == "ru":
            update.message.reply_text(
                "Отлично! Слово добавлено в словарь."
            )
        elif user_data["lang_spoken"] == "en":
            update.message.reply_text(
                "Great! The word's been added to your dictionary."
            )

        data_base.close()

        return TRANSLATE

    elif update.message.text.lower() == "нет" or update.message.text.lower() == "no":
        if user_data["lang_spoken"] == "ru":
            update.message.reply_text(
                "Хорошо, не будем добавлять это в словарь."
            )
        elif user_data["lang_spoken"] == "en":
            update.message.reply_text(
                "Ok, not gonna add it to your dictionary."
            )

        return TRANSLATE

    else:
        if user_data["lang_spoken"] == "ru":
            update.message.reply_text(
                "Извините, не могу понять ваш ответ. Ответьте, пожалуйста, более однозначно."
            )
        elif user_data["lang_spoken"] == "en":
            update.message.reply_text(
                "Sorry, I can't conceive your answer. Please, try answering more unambiguously."
            )

        return DICT_ADDING


def reset(bot, update):
    pass


def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', setting_up)],
        states={
            START_DIALOGUE: [MessageHandler(Filters.text, start_dialogue, pass_user_data=True)],
            TRANSLATE: [MessageHandler(Filters.text, translate_handling, pass_user_data=True)],
            DICT_ADDING: [MessageHandler(Filters.text, adding_to_dict, pass_user_data=True)]
        },
        fallbacks=[CommandHandler('reset', reset)]
    )

    dp.add_handler(conv_handler)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
