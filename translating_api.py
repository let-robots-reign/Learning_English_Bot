import requests
import sys
import xml.etree.ElementTree as ET


try:
    with open("tokens.txt", 'r', encoding="utf8") as infile:
        API_KEY, SPEECHKIT_KEY, UUID, DISK_TOKEN = (line.strip() for line in infile.readlines()[1:])
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
    #print(response.content)
    root = ET.fromstring(response.content)
    return root[0].text


def text_to_ogg(text, lang):
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
    voice_file = "output_voice.ogg"
    with open(voice_file, "wb") as file:
        file.write(response.content)
    return voice_file

def upload_file(filename, disk_path):
    host_name = 'https://cloud-api.yandex.net/v1/disk/resources/upload?path={}&overwrite=true'.format(disk_path)
    headers = {'Authorization':'OAuth AQAAAAAZQEWDAATv8dNapIbiAUA6l-vaZFXrR8g'.format(DISK_TOKEN)}
    x = requests.get(host_name, headers=headers)
    href = x.json()['href']
    x = requests.put(href, files={'file':open(filename, 'rb')})
    return bool(x)

def get_file(filename):
    host_name = 'https://cloud-api.yandex.net/v1/disk/resources/download?path={}'.format(filename)
    headers = {'Authorization': 'OAuth {}'.format(DISK_TOKEN)}
    x = requests.get(host_name, headers=headers)
    print(x.content)
    print(x.text)
    href = x.json()['href']
    x = requests.get(href)
    return x.text

def delete(filename):
    host_name = 'https://cloud-api.yandex.net/v1/disk/resources?path='.format(filename)
    headers = {'Authorization': 'OAuth {}'.format(DISK_TOKEN)}
    x = requests.delete(host_name, headers=headers)
    return bool(x)