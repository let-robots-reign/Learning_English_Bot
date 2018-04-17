import requests
import sys
import xml.etree.ElementTree as ET


try:
    with open("tokens.txt", 'r', encoding="utf8") as infile:
        API_KEY, SPEECHKIT_KEY, UUID, DISK_TOKEN, OED_APP_ID, OED_KEY = (line.strip() for line in infile.readlines()[1:])
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
            "speaker": "oksana",
            "speed": 0.8,
            "emotion": "good"
        }
    )
    voice_file = "output_voice.ogg"
    with open(voice_file, "wb") as file:
        file.write(response.content)
    return voice_file


def upload_file(filename, disk_path):
    host_name = 'https://cloud-api.yandex.net/v1/disk/resources/upload?path={}&overwrite=true'.format(disk_path)
    headers = {'Authorization': 'OAuth {}'.format(DISK_TOKEN)}
    href = requests.get(host_name, headers=headers).json()['href']
    return bool(requests.put(href, files={'file': open(filename, 'rb')}))


def get_file(filename):
    host_name = 'https://cloud-api.yandex.net/v1/disk/resources/download?path={}'.format(filename)
    headers = {'Authorization': 'OAuth {}'.format(DISK_TOKEN)}
    href = requests.get(host_name, headers=headers).json()['href']
    return requests.get(href).content


def delete(filename):
    host_name = 'https://cloud-api.yandex.net/v1/disk/resources?path='.format(filename)
    headers = {'Authorization': 'OAuth {}'.format(DISK_TOKEN)}
    return bool(requests.delete(host_name, headers=headers))


def get_files_list():
    host_name = 'https://cloud-api.yandex.net/v1/disk/resources/files'
    headers = {'Authorization': 'OAuth {}'.format(DISK_TOKEN)}
    return requests.get(host_name, headers=headers).json()


def get_definition(word, lang):
    oxford_template = 'https://od-api.oxforddictionaries.com/api/v1/entries/{}/{}'.format(lang, word)
    headers = {
        "Accept": "application/json",
        "app_id": OED_APP_ID,
        "app_key": OED_KEY
    }
    res = requests.get(oxford_template, headers=headers)
    if not res:
        return None
    res = res.json()
    return res['results'][0]['lexicalEntries'][0]['entries'][0]['senses'][0]['definitions'][0]
