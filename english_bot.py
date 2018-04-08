from telegram.ext import Updater, MessageHandler, CommandHandler, Filters, ConversationHandler
from telegram import ReplyKeyboardMarkup, ChatAction
from translating_api import translator, detect_lang, ogg_to_text, text_to_ogg
from database import *
import logging
import random
import sys
import os


logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


try:
    with open("tokens.txt", 'r', encoding="utf8") as infile:
        TOKEN, API_KEY = (line.strip() for line in infile.readlines()[:2])
except FileNotFoundError:
    print("Для работы нужен Telegram Token и Yandex Translate Key")
    sys.exit(1)


START_DIALOGUE, TRANSLATE, DICT_ADDING, CHANGE_LANG, TRAIN, ANSWER = range(6)

lang_keyboard = [["русский", "английский"]]
markup = ReplyKeyboardMarkup(lang_keyboard, one_time_keyboard=True)

trainings_keyboard = [["слово-перевод", "перевод-слово"],
                      ["аудирование", "собери слово"],
                      ["выход из раздела"]]
train_markup = ReplyKeyboardMarkup(trainings_keyboard, one_time_keyboard=True)


def error(bot, update, error):
    logger.warning('Update "%s" caused error "%s"', update, error)
    bot.send_message(chat_id=590585095, text='Update "%s" caused error "%s"' % (update, error))


def setting_up(bot, update):
    data_base = DataBase(update.message.from_user.id)
    data_base.create_table()
    update.message.reply_text(
        "Выберите язык, на котором я буду с вами говорить."
        "\n\n"
        "Choose the language I will speak.",
        reply_markup=markup
    )
    data_base.close()
    bot.send_message(chat_id=590585095, text="User %s %s started using the bot."
                                             % (update.message.from_user.first_name, update.message.from_user.last_name))

    return START_DIALOGUE


def start_dialogue(bot, update, user_data):
    if update.message.text == "русский":
        user_data["lang_spoken"] = "ru"
        update.message.reply_text(
            "Здравствуй! Я бот, который помогает учить английский. Я могу переводить для вас любые слова и фразы, "
            "а позже вы можете добавлять их в свой личный словарь, после чего тренировать с помощью "
            "различных упражнений.\n"
            "Список и описание упражнений можно посмотреть, вызвав команду /train_list. "
            "Вы можете все стереть и начать заново с помощью команды /reset.\n"
            "Давайте начнем!"
        )
        update.message.reply_text(
            'Чтобы передать мне слово или фразу на перевод, напишите мне "переведи (мне) / translate %слово%" '
            'либо же просто "%слово%". Также вы можете прислать мне голосовое сообщение со словом. '
            'После этого вы сможете выбрать, добавлять ли слово в ваш словарь. '
            'Чтобы посмотреть последние добавленные слова, введите /show_dict.'
        )

        return TRANSLATE

    elif update.message.text == "английский":
        user_data["lang_spoken"] = "en"
        update.message.reply_text(
            "Hello! I'm a bot that is constructed for learning English. I can translate any word or phrase for you, "
            "and after that you can add it to your dictionary and learn with several types of trainings "
            "whenever you want.\n"
            "You can look up the list of trainings via /train_list command. "
            "Also, you can reset all your data and start from the beginning using /reset command.\n"
            "Let's get started!"
        )
        update.message.reply_text(
            'To transfer a word for translation, write "переведи (мне) / translate %word%" or just "%word%". '
            'In addition, you can send me a voice message with the word. '
            'Afterwards, you can decide whether you want to add it to your dictionary or not. '
            'To overview last added words, you can type /show_dict.'
        )

        return TRANSLATE

    else:
        update.message.reply_text(
            "Вы еще не выбрали язык, на котором я буду говорить."
            "\n\n"
            "You haven't chosen the language I'll be speaking.",
            reply_markup=markup
        )


def translate_handling(bot, update, user_data):
    bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)

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
    get_translate = text_to_ogg(user_data["current_word"], 'ru' if user_data["lang_spoken"] == 'en' else 'en')
    bot.send_voice(chat_id=update.message.chat_id, voice=open(get_translate, 'rb'))

    return DICT_ADDING


def voice_translate_handling(bot, update, user_data):
    bot.send_chat_action(chat_id=update.message.chat_id, action=ChatAction.TYPING)

    file_id = update.message.voice.file_id
    new_file = bot.get_file(file_id)
    new_file.download('input_voice.ogg')
    text_to_translate = ogg_to_text('input_voice.ogg')
    if not text_to_translate:
        if user_data["lang_spoken"] == "ru":
            update.message.reply_text(
                "Извините, не могу понять, что вы говорите."
            )
        elif user_data["lang_spoken"] == "en":
            update.message.reply_text(
                "Sorry, I can't conceive what you are saying."
            )
    else:
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
        get_translate = text_to_ogg(user_data["current_word"], 'ru' if user_data["lang_spoken"] == 'en' else 'en')
        bot.send_voice(chat_id=update.message.chat_id, voice=open(get_translate, 'rb'))

        return DICT_ADDING

    os.remove('input_voice.ogg')


def show_dict(bot, update, user_data):
    data_base = DataBase(update.message.from_user.id)
    data_base.create_table()
    dictionary = data_base.read_dict()
    if not dictionary:
        if user_data["lang_spoken"] == "ru":
            update.message.reply_text(
                "Извините, похоже, вы еще ничего не добавили в словарь."
            )
        elif user_data["lang_spoken"] == "en":
            update.message.reply_text(
                "Sorry, seems like you haven't added anything to your dictionary yet."
            )
    elif user_data["lang_spoken"] == "ru":
        update.message.reply_text(
            "Последние добавленные слова:"
        )
        update.message.reply_text(
            "\n".join(["{} - {}".format(word, translation)
                       for word, translation, completion in dictionary[:100][::-1]])
        )
    elif user_data["lang_spoken"] == "en":
        update.message.reply_text(
            "Last added words:"
        )
        update.message.reply_text(
            "\n".join(["{} - {}".format(word, translation)
                       for word, translation, completion in dictionary[:100][::-1]])
        )

    data_base.close()


def adding_to_dict(bot, update, user_data):
    if update.message.text.lower() == "да" or update.message.text.lower() == "yes":

        data_base = DataBase(update.message.from_user.id)
        data_base.create_table()
        data_base.insert_word(user_data["current_word"], user_data["current_translation"])

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


def change_lang(bot, update):
    update.message.reply_text(
        "Выберите язык, на котором я буду с вами говорить."
        "\n\n"
        "Choose the language I will speak.",
        reply_markup=markup
    )

    return CHANGE_LANG


def lang_changed(bot, update, user_data):
    if update.message.text == "русский":
        user_data["lang_spoken"] = "ru"
        update.message.reply_text(
            "Язык был сменен на русский."
        )
    elif update.message.text == "английский":
        user_data["lang_spoken"] = "en"
        update.message.reply_text(
            "The language has been changed to English."
        )

    return TRANSLATE


def trainings_list(bot, update, user_data):
    if user_data["lang_spoken"] == "ru":
        update.message.reply_text(
            "Выберите тренировку.",
            reply_markup=train_markup
        )

        return TRAIN

    elif user_data["lang_spoken"] == "en":
        update.message.reply_text(
            "Choose the training.",
            reply_markup=train_markup
        )

        return TRAIN


def choose_training(bot, update, user_data):
    if update.message.text.lower() == "слово-перевод":
        word_translation_training(bot, update)
    elif update.message.text.lower() == "перевод-слово":
        translation_word_training(bot, update)
    elif update.message.text.lower() == "аудирование":
        audio_training(bot, update)
    elif update.message.text.lower() == "собери слово":
        construct_word_training(bot, update)
    elif update.message.text.lower() == "выход из раздела":
        return TRANSLATE
    else:
        if user_data["lang_spoken"] == "ru":
            update.message.reply_text(
                "Извините, такой тренировки не существует."
            )
        elif user_data["lang_spoken"] == "en":
            update.message.reply_text(
                "Sorry, I don't have such a training."
            )

        return TRAIN


def delete_word(bot, update, args, user_data):
    data_base = DataBase(update.message.from_user.id)
    data_base.create_table()
    if not args:
        if user_data["lang_spoken"] == "ru":
            update.message.reply_text(
                "Вы не передали слово для удаления.\n"
                "Если вы хотите удалить весь словарь, введите /reset."
            )
        elif user_data["lang_spoken"] == "en":
            update.message.reply_text(
                "You haven't transferred the word for deletion.\n"
                "If you want to delete all the words from dictionary, use /reset."
            )
    elif not any(''.join(args) == row[0] for row in data_base.read_dict()):
        if user_data["lang_spoken"] == "ru":
            update.message.reply_text(
                "Этого слова нет в вашем словаре."
            )
        elif user_data["lang_spoken"] == "en":
            update.message.reply_text(
                "You don't have this word in your dictionary."
            )
    else:
        data_base.delete_word(args)
        if user_data["lang_spoken"] == "ru":
            update.message.reply_text(
                "Слово было удалено из вашего словаря."
            )
        elif user_data["lang_spoken"] == "en":
            update.message.reply_text(
                "The word has been deleted from your dictionary."
            )

    data_base.close()

    return TRANSLATE


def word_translation_training(bot, update):
    pass
    # data_base = DataBase(update.message.from_user.id)
    # data_base.create_table()
    # word = random.choice([item[0] for item in data_base.select_uncompleted_words()])
    # update.message.reply_text(word)


def translation_word_training(bot, update):
    pass


def audio_training(bot, update):
    pass


def construct_word_training(bot, update):
    pass


def check_answer(bot, update):
    pass


def reset(bot, update, user_data):
    data_base = DataBase(update.message.from_user.id)
    data_base.delete_dict()
    if user_data["lang_spoken"] == "ru":
        update.message.reply_text(
            "Ваш словарь был удален. Вы можете начать заново с помощью команды /start."
        )
    elif user_data["lang_spoken"] == "en":
        update.message.reply_text(
            "Your dictionary has been erased. You can start again using /start command."
        )

    return ConversationHandler.END


def main():
    updater = Updater(TOKEN)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler('start', setting_up)],
        states={
            START_DIALOGUE: [MessageHandler(Filters.text, start_dialogue, pass_user_data=True)],

            TRANSLATE: [MessageHandler(Filters.text, translate_handling, pass_user_data=True),
                        MessageHandler(Filters.voice, voice_translate_handling, pass_user_data=True),
                        CommandHandler("show_dict", show_dict, pass_user_data=True),
                        CommandHandler("change_lang", change_lang),
                        CommandHandler("delete", delete_word, pass_args=True, pass_user_data=True),
                        CommandHandler("train_list", trainings_list, pass_user_data=True)],

            DICT_ADDING: [MessageHandler(Filters.text, adding_to_dict, pass_user_data=True)],

            CHANGE_LANG: [MessageHandler(Filters.text, lang_changed, pass_user_data=True)],

            TRAIN: [MessageHandler(Filters.text, choose_training, pass_user_data=True)],

            ANSWER: [MessageHandler(Filters.text, check_answer)]
        },
        fallbacks=[CommandHandler('reset', reset, pass_user_data=True)]
    )

    dp.add_handler(conv_handler)
    dp.add_error_handler(error)

    updater.start_polling()
    updater.idle()


if __name__ == '__main__':
    main()
