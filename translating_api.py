import requests
import sys
import xml.etree.ElementTree as ET


try:
    with open("tokens.txt", 'r', encoding="utf8") as infile:
        API_KEY, SPEECHKIT_KEY, UUID = (line.strip() for line in infile.readlines()[1:])
except FileNotFoundError:
    print("Отсутствует Yandex Translate Key или Yandex SpeechKit Key")
    sys.exit(1)


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


def ogg_to_text(file):
    headers = {'Content-Type': 'audio/ogg;codecs=opus'}
    speech_url = "http://asr.yandex.net/asr_xml"
    data = open(file, 'rb')
    response = requests.post(
        speech_url,
        params={
            "key": SPEECHKIT_KEY,
            "uuid": UUID,
            "topic": "queries"
        },
        headers=headers,
        data=data
    )
    print(response.content)
    root = ET.fromstring(response.content)
    return root[0].text


def text_to_ogg(text, lang, id):
    synthesis_template = "https://tts.voicetech.yandex.net/generate"
    response = requests.get(
        synthesis_template,
        params={
            "key": SPEECHKIT_KEY,
            "text": text,
            "format": "opus",
            "lang": lang,
            "speaker": "oksana"
        }
    )

    voice_file = "voice%s.ogg" % id
    with open(voice_file, "wb") as file:
        file.write(response.content)


#text_to_ogg("привет, я бот, который синтезирует речь", "ru-RU", 590585095)
#ogg_to_text('voice590585095.ogg')
