#!/usr/bin/env python3
"""Generate VKR/fixtures/tasks.json with 280 tasks."""
import json, random

tasks = []

# ── LETTERS ────────────────────────────────────────────────────────────────

LETTERS = ['А','О','У','И','Э','Ы','М','П','Б','Д','Т','К','Г','В','Ф','С','З','Ш','Ж','Ч','Щ','Н','Л','Р','Й','Е','Ё','Ю','Я','Х']

LETTER_HINTS = {
    'А':'Буква А — как в слове АРБУЗ 🍉',
    'О':'Буква О — как в слове ОСЁЛ 🫏',
    'У':'Буква У — как в слове УТКА 🦆',
    'И':'Буква И — как в слове ИГЛА 🪡',
    'Э':'Буква Э — как в слове ЭХО 📢',
    'Ы':'Буква Ы — в словах рыба, дым. Никогда не стоит в начале!',
    'М':'Буква М — как в слове МАМА 👩',
    'П':'Буква П — как в слове ПАПА 👨',
    'Б':'Буква Б — как в слове БАБОЧКА 🦋',
    'Д':'Буква Д — как в слове ДОМ 🏠',
    'Т':'Буква Т — как в слове ТИГР 🐯',
    'К':'Буква К — как в слове КОТ 🐱',
    'Г':'Буква Г — как в слове ГУСЬ 🦢',
    'В':'Буква В — как в слове ВОЛК 🐺',
    'Ф':'Буква Ф — как в слове ФЛАМИНГО 🦩',
    'С':'Буква С — как в слове СЛОН 🐘',
    'З':'Буква З — как в слове ЗЕБРА 🦓',
    'Ш':'Буква Ш — как в слове ШАПКА 🎩',
    'Ж':'Буква Ж — как в слове ЖУК 🐞',
    'Ч':'Буква Ч — как в слове ЧАШКА ☕',
    'Щ':'Буква Щ — похожа на Ш, но с хвостиком!',
    'Н':'Буква Н — как в слове НОС 👃',
    'Л':'Буква Л — как в слове ЛИСА 🦊',
    'Р':'Буква Р — как в слове РЫБА 🐟',
    'Й':'Буква Й — это короткая И! Как в слове МАЙ ☀️',
    'Е':'Буква Е — как в слове ЕЖ 🦔',
    'Ё':'Буква Ё — как в слове ЁЖИК 🦔. Не путай с Е!',
    'Ю':'Буква Ю — как в слове ЮЛА 🪀',
    'Я':'Буква Я — как в слове ЯБЛОКО 🍎',
    'Х':'Буква Х — как в слове ХОМЯК 🐹',
}

LETTER_DIST = {
    'А':['О','У','Я'], 'О':['А','Э','У'], 'У':['О','И','А'],
    'И':['Й','Н','Ы'], 'Э':['Е','О','Ё'], 'Ы':['И','У','Й'],
    'М':['Н','П','Л'], 'П':['Т','Н','Г'], 'Б':['В','Д','П'],
    'Д':['Б','Г','Л'], 'Т':['П','Н','К'], 'К':['Х','Г','Ж'],
    'Г':['Д','Т','К'], 'В':['Б','Г','Д'], 'Ф':['Т','О','Х'],
    'С':['З','О','Э'], 'З':['С','Э','Е'], 'Ш':['Щ','М','Ж'],
    'Ж':['Ш','Х','З'], 'Ч':['Щ','Ц','Х'], 'Щ':['Ш','Ц','Ч'],
    'Н':['М','П','И'], 'Л':['Д','П','Г'], 'Р':['В','Б','К'],
    'Й':['И','Н','Г'], 'Е':['Ё','З','Э'], 'Ё':['Е','О','Ю'],
    'Ю':['У','О','Ё'], 'Я':['Р','В','К'], 'Х':['К','Ж','Ц'],
}

def letter_options(letter):
    opts = [letter] + LETTER_DIST[letter]
    random.shuffle(opts)
    return opts

pk = 100
for lesson_num, letter in enumerate(LETTERS, 1):
    opts = letter_options(letter)
    hint = LETTER_HINTS[letter]

    # Task 1: audio_choice — hear and pick
    pk += 1
    tasks.append({"model":"learning.task","pk":pk,"fields":{
        "title": f"Слушай букву {letter}",
        "task_type": "letter", "task_subtype": "audio_choice",
        "lesson_number": lesson_num, "order_num": 1,
        "question_text": f"Послушай и выбери букву",
        "content_text": letter, "correct_answer": letter,
        "options": opts, "level": 1, "difficulty": 1,
        "is_placement_test": False, "hint_text": hint,
        "image_url": "", "audio_url": "",
    }})

    # Task 2: keyboard — type it
    pk += 1
    tasks.append({"model":"learning.task","pk":pk,"fields":{
        "title": f"Напечатай букву {letter}",
        "task_type": "letter", "task_subtype": "keyboard",
        "lesson_number": lesson_num, "order_num": 2,
        "question_text": "Напечатай эту букву",
        "content_text": letter, "correct_answer": letter,
        "options": [], "level": 1, "difficulty": 2,
        "is_placement_test": False, "hint_text": hint,
        "image_url": "", "audio_url": "",
    }})

    # Task 3: find_no_audio — find without audio cue
    pk += 1
    tasks.append({"model":"learning.task","pk":pk,"fields":{
        "title": f"Найди букву {letter}",
        "task_type": "letter", "task_subtype": "find_no_audio",
        "lesson_number": lesson_num, "order_num": 3,
        "question_text": "Найди эту букву среди других",
        "content_text": letter, "correct_answer": letter,
        "options": opts, "level": 1, "difficulty": 2,
        "is_placement_test": False, "hint_text": hint,
        "image_url": "", "audio_url": "",
    }})

# ── SYLLABLES ──────────────────────────────────────────────────────────────

SYLLABLES = ['МА','МО','МУ','МИ','МЕ','ПА','ПО','ПУ','ПИ','ПЕ',
             'БА','БО','БУ','ДА','ДО','ТА','ТО','СА','СО','ЛА',
             'ЛО','ЛУ','РА','РО','РУ','НА','НО','ВА','ВО','КА']

# Example words for image_choice: (word+emoji, first syllable distractors)
SYLLABLE_WORDS = {
    'МА': ('МАМА 👩',  ['НА','ПА','ДА']),
    'МО': ('МОРЕ 🌊',  ['НО','ПО','ДО']),
    'МУ': ('МУХА 🦟',  ['НУ','ПУ','БУ']),
    'МИ': ('МИШКА 🐻', ['НИ','ПИ','БИ']),
    'МЕ': ('МЕДВЕДЬ 🐻',['НЕ','ПЕ','ДЕ']),
    'ПА': ('ПАПА 👨',  ['МА','НА','ДА']),
    'ПО': ('ПОЛЕ 🌾',  ['МО','НО','ДО']),
    'ПУ': ('ПУЛЯ 💥',  ['МУ','НУ','БУ']),
    'ПИ': ('ПИЛА 🪚',  ['МИ','НИ','ДИ']),
    'ПЕ': ('ПЕТУХ 🐓', ['МЕ','НЕ','ДЕ']),
    'БА': ('БАБА 👵',  ['МА','НА','ПА']),
    'БО': ('БОЧКА 🪣', ['МО','НО','ПО']),
    'БУ': ('БУЛКА 🥖', ['МУ','НУ','ПУ']),
    'ДА': ('ДАЧА 🏡',  ['МА','НА','БА']),
    'ДО': ('ДОРОГА 🛣️',['МО','НО','БО']),
    'ТА': ('ТАРЕЛКА 🍽️',['МА','НА','ДА']),
    'ТО': ('ТОРТ 🎂',  ['МО','НО','ДО']),
    'СА': ('САНИ 🛷',  ['МА','НА','ДА']),
    'СО': ('СОВА 🦉',  ['МО','НО','ДО']),
    'ЛА': ('ЛАПА 🐾',  ['МА','НА','ДА']),
    'ЛО': ('ЛОЖКА 🥄', ['МО','НО','ДО']),
    'ЛУ': ('ЛУНА 🌙',  ['МУ','НУ','БУ']),
    'РА': ('РАМА 🖼️',  ['МА','НА','ДА']),
    'РО': ('РОЗА 🌹',  ['МО','НО','ДО']),
    'РУ': ('РУКА 🤚',  ['МУ','НУ','ЛУ']),
    'НА': ('НОРА 🕳️',  ['МА','ДА','ПА']),
    'НО': ('НОЧЬ 🌙',  ['МО','ДО','ПО']),
    'ВА': ('ВАЗА 💐',  ['МА','НА','ДА']),
    'ВО': ('ВОЛК 🐺',  ['МО','НО','ДО']),
    'КА': ('КАША 🥣',  ['МА','НА','ДА']),
}

SYLLABLE_DIST = {
    'МА':['НА','ПА','ДА'], 'МО':['НО','ПО','ДО'], 'МУ':['НУ','ПУ','БУ'],
    'МИ':['НИ','ПИ','ДИ'], 'МЕ':['НЕ','ПЕ','ДЕ'], 'ПА':['МА','НА','БА'],
    'ПО':['МО','НО','БО'], 'ПУ':['МУ','НУ','БУ'], 'ПИ':['МИ','НИ','БИ'],
    'ПЕ':['МЕ','НЕ','БЕ'], 'БА':['МА','НА','ПА'], 'БО':['МО','НО','ПО'],
    'БУ':['МУ','НУ','ПУ'], 'ДА':['МА','НА','БА'], 'ДО':['МО','НО','БО'],
    'ТА':['ДА','НА','МА'], 'ТО':['ДО','НО','МО'], 'СА':['ДА','НА','МА'],
    'СО':['ДО','НО','МО'], 'ЛА':['МА','НА','ДА'], 'ЛО':['МО','НО','ДО'],
    'ЛУ':['МУ','НУ','РУ'], 'РА':['МА','НА','ДА'], 'РО':['МО','НО','ДО'],
    'РУ':['МУ','НУ','ЛУ'], 'НА':['МА','ПА','ДА'], 'НО':['МО','ПО','ДО'],
    'ВА':['МА','НА','ДА'], 'ВО':['МО','НО','ДО'], 'КА':['МА','НА','ДА'],
}

SYLLABLE_HINTS = {s: f'Прочитай по буквам: {s[0]} + {s[1]} = {s}' for s in SYLLABLES}
SYLLABLE_HINTS['МА'] = 'М + А = МА, как в слове МАМА 👩'
SYLLABLE_HINTS['ПА'] = 'П + А = ПА, как в слове ПАПА 👨'
SYLLABLE_HINTS['ДО'] = 'Д + О = ДО, как в слове ДОМ 🏠'
SYLLABLE_HINTS['КА'] = 'К + А = КА, как в слове КАША 🥣'

def syllable_options(syl):
    opts = [syl] + SYLLABLE_DIST[syl]
    random.shuffle(opts)
    return opts

def compose_options(word):
    """Letters of word + 1-2 distractors, shuffled."""
    letters = list(word)
    extras = ['Н','М','Т','К','Л','Р','С','П','Б','Д']
    # Add 1-2 distractors that aren't already in the word
    distractors = [l for l in extras if l not in letters][:2]
    opts = letters + distractors
    random.shuffle(opts)
    return opts

pk = 200
for lesson_num, syl in enumerate(SYLLABLES, 1):
    hint = SYLLABLE_HINTS[syl]
    audio_opts = syllable_options(syl)
    word_str, img_distractors = SYLLABLE_WORDS[syl]
    img_opts = [syl] + img_distractors
    random.shuffle(img_opts)
    syl_letters = [syl[0], syl[1]]
    syl_distractors = [l for l in ['Н','М','Т','К','Л','Р','С','П'] if l not in syl_letters][:2]
    compose_opts = syl_letters + syl_distractors
    random.shuffle(compose_opts)

    # Task 1: audio_choice
    pk += 1
    tasks.append({"model":"learning.task","pk":pk,"fields":{
        "title": f"Слушай слог {syl}",
        "task_type": "syllable", "task_subtype": "audio_choice",
        "lesson_number": lesson_num, "order_num": 1,
        "question_text": "Послушай и выбери слог",
        "content_text": syl, "correct_answer": syl,
        "options": audio_opts, "level": 2, "difficulty": 1,
        "is_placement_test": False, "hint_text": hint,
        "image_url": "", "audio_url": "",
    }})

    # Task 2: compose — click letters to form syllable
    pk += 1
    tasks.append({"model":"learning.task","pk":pk,"fields":{
        "title": f"Составь слог {syl}",
        "task_type": "syllable", "task_subtype": "compose",
        "lesson_number": lesson_num, "order_num": 2,
        "question_text": f"Составь слог из букв",
        "content_text": syl, "correct_answer": syl,
        "options": compose_opts, "level": 2, "difficulty": 2,
        "is_placement_test": False, "hint_text": hint,
        "image_url": "", "audio_url": "",
    }})

    # Task 3: image_choice — word picture, pick syllable
    pk += 1
    tasks.append({"model":"learning.task","pk":pk,"fields":{
        "title": f"Найди слог {syl} по картинке",
        "task_type": "syllable", "task_subtype": "image_choice",
        "lesson_number": lesson_num, "order_num": 3,
        "question_text": "Каким слогом начинается это слово?",
        "content_text": word_str, "correct_answer": syl,
        "options": img_opts, "level": 2, "difficulty": 2,
        "is_placement_test": False, "hint_text": hint,
        "image_url": "", "audio_url": "",
    }})

# ── WORDS ──────────────────────────────────────────────────────────────────

WORDS = [
    ('КОТ','🐱','Мяукает и ловит мышей',['ДОМ','РАК','КИТ']),
    ('ДОМ','🏠','Здесь живут люди',['КОТ','СОМ','МАК']),
    ('РАК','🦀','Живёт в реке, ходит боком',['КОТ','ДОМ','ЖУК']),
    ('МЯЧ','⚽','Им играют в футбол',['МАК','МЁД','МЕЧ']),
    ('ЖУК','🐞','Маленькое насекомое',['ЖАР','ЗУБ','РАК']),
    ('БЫК','🐂','Большое рогатое животное',['КОТ','КИТ','ДУБ']),
    ('НОС','👃','Им мы нюхаем цветы',['РОТ','УХО','ЗУБ']),
    ('УХО','👂','Им мы слышим звуки',['НОС','РОТ','ЗУБ']),
    ('КИТ','🐳','Самое большое морское животное',['КОТ','ЛЕВ','РАК']),
    ('ЛЕВ','🦁','Царь зверей с гривой',['КОТ','КИТ','ЛУК']),
    ('ЛУК','🧅','Растение со слезами',['ЛЕВ','МАК','ДУБ']),
    ('МАК','🌺','Красный цветок',['ЛУК','МЁД','ДУБ']),
    ('ДУБ','🌳','Большое дерево с желудями',['ЛЕС','МАК','ЛУК']),
    ('МЁД','🍯','Пчёлы делают его в улье',['СОК','МАК','ДАР']),
    ('СОН','😴','Это бывает ночью',['СОК','СОМ','ШАР']),
    ('СОК','🧃','Напиток из фруктов',['СОН','СОМ','МЁД']),
    ('ШАР','🎈','Летит вверх, бывает воздушным',['СОК','ДАР','ЛЁД']),
    ('ЛЁД','🧊','Замёрзшая вода',['ШАР','ЗУБ','МИР']),
    ('ЗУБ','🦷','Им мы жуём еду',['НОС','УХО','РОТ']),
    ('СОМ','🐟','Большая речная рыба',['КИТ','РАК','ЖУК']),
    ('РОТ','👄','Им мы говорим и едим',['НОС','УХО','ЗУБ']),
    ('МЕЧ','⚔️','Оружие рыцаря',['МЯЧ','МАК','МЁД']),
    ('ЛЕС','🌲','Много деревьев вместе',['ДУБ','ЛЕВ','МАК']),
    ('ГОЛ','🥅','Мяч влетает в ворота — это...',['ДОМ','КОТ','МАК']),
    ('ЗАЛ','🏛️','Большая комната',['ДОМ','БАЛ','ВОЗ']),
    ('БАЛ','💃','Танцевальный праздник',['ЗАЛ','ДАР','МИР']),
    ('ВОЛ','🐮','Рабочее животное (бык без рогов)',['БЫК','КОТ','ДОМ']),
    ('ВОЗ','🛒','На нём возят груз',['ДОМ','ЗАЛ','МИР']),
    ('МИР','🌍','Вся наша планета',['ДАР','ЛЕС','ЗАЛ']),
    ('ДАР','🎁','Подарок',['МИР','МЁД','МАК']),
]

pk = 300
for lesson_num, (word, emoji, hint_text, dist_words) in enumerate(WORDS, 1):
    img_opts = [word] + dist_words
    random.shuffle(img_opts)
    comp_opts = compose_options(word)

    # Task 1: image_choice — see emoji, pick word
    pk += 1
    tasks.append({"model":"learning.task","pk":pk,"fields":{
        "title": f"Узнай слово {word}",
        "task_type": "word", "task_subtype": "image_choice",
        "lesson_number": lesson_num, "order_num": 1,
        "question_text": "Что изображено на картинке?",
        "content_text": emoji, "correct_answer": word,
        "options": img_opts, "level": 3, "difficulty": 1,
        "is_placement_test": False, "hint_text": hint_text,
        "image_url": "", "audio_url": "",
    }})

    # Task 2: compose — click letters to spell word
    pk += 1
    tasks.append({"model":"learning.task","pk":pk,"fields":{
        "title": f"Составь слово {word}",
        "task_type": "word", "task_subtype": "compose",
        "lesson_number": lesson_num, "order_num": 2,
        "question_text": f"Составь слово из букв",
        "content_text": word, "correct_answer": word,
        "options": comp_opts, "level": 3, "difficulty": 2,
        "is_placement_test": False, "hint_text": hint_text,
        "image_url": "", "audio_url": "",
    }})

    # Task 3: keyboard — type the word
    pk += 1
    tasks.append({"model":"learning.task","pk":pk,"fields":{
        "title": f"Напечатай слово {word}",
        "task_type": "word", "task_subtype": "keyboard",
        "lesson_number": lesson_num, "order_num": 3,
        "question_text": f"Напечатай слово по картинке",
        "content_text": emoji, "correct_answer": word,
        "options": [], "level": 3, "difficulty": 3,
        "is_placement_test": False, "hint_text": hint_text,
        "image_url": "", "audio_url": "",
    }})

# ── PLACEMENT TESTS ─────────────────────────────────────────────────────────

placement = [
    # Letters (4 tasks)
    {"pk":401,"task_type":"letter","task_subtype":"audio_choice","level":1,
     "content_text":"А","correct_answer":"А","options":["А","О","У","И"],
     "question_text":"Какая это буква?","hint_text":"","lesson_number":0,"order_num":1},
    {"pk":402,"task_type":"letter","task_subtype":"audio_choice","level":1,
     "content_text":"М","correct_answer":"М","options":["М","Н","П","Л"],
     "question_text":"Какая это буква?","hint_text":"","lesson_number":0,"order_num":2},
    {"pk":403,"task_type":"letter","task_subtype":"audio_choice","level":1,
     "content_text":"О","correct_answer":"О","options":["О","А","У","Э"],
     "question_text":"Какая это буква?","hint_text":"","lesson_number":0,"order_num":3},
    {"pk":404,"task_type":"letter","task_subtype":"audio_choice","level":1,
     "content_text":"К","correct_answer":"К","options":["К","Г","Т","Х"],
     "question_text":"Какая это буква?","hint_text":"","lesson_number":0,"order_num":4},
    # Syllables (3 tasks)
    {"pk":405,"task_type":"syllable","task_subtype":"audio_choice","level":2,
     "content_text":"МА","correct_answer":"МА","options":["МА","НА","ПА","ДА"],
     "question_text":"Как читается этот слог?","hint_text":"","lesson_number":0,"order_num":5},
    {"pk":406,"task_type":"syllable","task_subtype":"audio_choice","level":2,
     "content_text":"ДО","correct_answer":"ДО","options":["ДО","ДА","НО","ТО"],
     "question_text":"Как читается этот слог?","hint_text":"","lesson_number":0,"order_num":6},
    {"pk":407,"task_type":"syllable","task_subtype":"audio_choice","level":2,
     "content_text":"НА","correct_answer":"НА","options":["НА","МА","НО","КА"],
     "question_text":"Как читается этот слог?","hint_text":"","lesson_number":0,"order_num":7},
    # Words (3 tasks)
    {"pk":408,"task_type":"word","task_subtype":"image_choice","level":3,
     "content_text":"🐱","correct_answer":"КОТ","options":["КОТ","ДОМ","РАК","КИТ"],
     "question_text":"Что изображено?","hint_text":"","lesson_number":0,"order_num":8},
    {"pk":409,"task_type":"word","task_subtype":"image_choice","level":3,
     "content_text":"🏠","correct_answer":"ДОМ","options":["ДОМ","КОТ","СОМ","МЁД"],
     "question_text":"Что изображено?","hint_text":"","lesson_number":0,"order_num":9},
    {"pk":410,"task_type":"word","task_subtype":"image_choice","level":3,
     "content_text":"⚽","correct_answer":"МЯЧ","options":["МЯЧ","МАК","МЁД","МЕЧ"],
     "question_text":"Что изображено?","hint_text":"","lesson_number":0,"order_num":10},
]

for p in placement:
    tasks.append({"model":"learning.task","pk":p["pk"],"fields":{
        "title": "Входное тестирование",
        "task_type": p["task_type"], "task_subtype": p["task_subtype"],
        "lesson_number": p["lesson_number"], "order_num": p["order_num"],
        "question_text": p["question_text"],
        "content_text": p["content_text"], "correct_answer": p["correct_answer"],
        "options": p["options"], "level": p["level"], "difficulty": 1,
        "is_placement_test": True, "hint_text": p["hint_text"],
        "image_url": "", "audio_url": "",
    }})

print(f"Generated {len(tasks)} tasks")
with open('VKR/fixtures/tasks.json', 'w', encoding='utf-8') as f:
    json.dump(tasks, f, ensure_ascii=False, indent=2)
print("Written to VKR/fixtures/tasks.json")
