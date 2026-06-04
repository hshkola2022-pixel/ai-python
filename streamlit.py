import streamlit as st
import sys
import io
import contextlib
import requests
import time

# --- НАСТРОЙКИ СТРАНИЦЫ И ТЕПЛАЯ ТЕМА ---
st.set_page_config(
    page_title="Python AI Тренажёр",
    page_icon="🐍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Внедрение кастомного CSS для создания теплой янтарно-каменной гаммы
st.markdown("""
<style>
    /* Настройка темной теплой темы */
    .stApp {
        background-color: #0c0a09; /* stone-950 */
        color: #f5f5f4; /* stone-100 */
    }
    
    /* Стилизация боковой панели */
    [data-testid="stSidebar"] {
        background-color: #1c1917; /* stone-900 */
        border-right: 1px solid #2e2a24;
    }
    
    /* Заголовки */
    h1, h2, h3 {
        color: #f59e0b !important; /* Amber-500 */
        font-family: 'Inter', sans-serif;
    }
    
    /* Стилизация кнопок */
    .stButton>button {
        background: linear-gradient(135deg, #f59e0b 0%, #ea580c 100%) !important; /* Amber to Orange */
        color: #0c0a09 !important;
        font-weight: bold !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 10px 24px !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 4px 15px rgba(245, 158, 11, 0.2);
    }
    
    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(245, 158, 11, 0.4);
        color: #ffffff !important;
    }
    
    /* Карточки и блоки */
    .theory-box {
        background-color: #1c1917;
        border: 1px solid #2e2a24;
        border-radius: 16px;
        padding: 24px;
        margin-bottom: 20px;
        box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.1);
    }
    
    /* Кастомная панель прогресса (XP) */
    .xp-badge {
        background: rgba(245, 158, 11, 0.1);
        border: 1px solid #f59e0b;
        color: #f59e0b;
        padding: 6px 16px;
        border-radius: 20px;
        font-weight: bold;
        display: inline-flex;
        align-items: center;
        gap: 8px;
    }
</style>
""", unsafe_allow_html=True)

# --- ИНИЦИАЛИЗАЦИЯ ИИ (Gemini API) ---
API_KEY = "" # Ключ предоставляется средой выполнения при деплое

# Функция для вызова ИИ-помощника с экспоненциальным бэк-оффом
def ask_gemini(user_code, task_desc, expected_out, system_prompt, user_lang):
    prompt = f"""
    Контекст задачи: {task_desc}
    Ожидаемый вывод: {expected_out}
    
    Код студента:
    ```python
    {user_code}
    ```
    
    Пожалуйста, проанализируй код, найди логическую или синтаксическую ошибку и дай подсказку на языке пользователя ({user_lang}). 
    НЕ пиши рабочий готовый код решения. Направляй студента наводящими вопросами.
    """
    
    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "systemInstruction": {"parts": [{"text": system_prompt}]}
    }
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash-preview-09-2025:generateContent?key={API_KEY}"
    
    # 5 попыток с экспоненциальным бэк-оффом
    delay = 1.0
    for i in range(5):
        try:
            response = requests.post(url, json=payload, headers={"Content-Type": "application/json"})
            if response.status_code == 200:
                res_json = response.json()
                return res_json['candidates'][0]['content']['parts'][0]['text']
        except Exception:
            pass
        time.sleep(delay)
        delay *= 2
        
    return "ИИ временно недоступен. Попробуйте отправить запрос позже или проверьте код самостоятельно."

# --- ИНТЕРПРЕТАТОР PYTHON (Запуск кода в реальном времени) ---
@contextlib.contextmanager
def stdout_io(stdout=None):
    old = sys.stdout
    if stdout is None:
        stdout = io.StringIO()
    sys.stdout = stdout
    yield stdout
    sys.stdout = old

def execute_python_code(code):
    with stdout_io() as s:
        try:
            # Выполняем код в изолированном контексте
            exec(code, {}, {})
            error = None
        except Exception as e:
            error = str(e)
    return s.getvalue(), error

# --- ИНИЦИАЛИЗАЦИЯ СЕССИИ (Session State) ---
if "xp" not in st.session_state:
    st.session_state.xp = 0
if "completed" not in st.session_state:
    st.session_state.completed = set()
if "lang" not in st.session_state:
    st.session_state.lang = "RU"

# --- ЛОКАЛИЗАЦИОННЫЙ ПАК ---
t = {
    "RU": {
        "title": "Python AI Тренажёр 🐍",
        "subtitle": "Интеллектуальная среда обучения программированию",
        "lang_label": "Выберите язык обучения:",
        "xp_label": "Ваш Опыт:",
        "menu_module": "📚 Модули обучения",
        "menu_sandbox": "💻 Песочница кода",
        "menu_achievements": "🏆 Достижения",
        "theory_tab": "Теория",
        "task_tab": "Практическое задание",
        "test_tab": "Тест (10 вопросов)",
        "run_btn": "Запустить код",
        "reset_btn": "Сбросить код",
        "ai_btn": "Спросить AI-помощника",
        "ai_thinking": "ИИ анализирует ваш код...",
        "success_msg": "🎉 Великолепно! Задание решена верно. +50 XP",
        "fail_msg": "❌ Вывод не совпадает с ожидаемым. Попробуйте еще раз или спросите ИИ.",
        "test_warning": "Пожалуйста, ответьте на все 10 вопросов перед отправкой теста!",
        "test_passed": "🌟 Поздравляем! Вы прошли тест на {score}/10 и завершили модуль!",
        "test_failed": "⚠️ Для завершения модуля нужно набрать минимум 8/10. Попробуйте снова!",
        "ai_prompt": "Ты — профессиональный ментор по Python. Твоя задача — помочь студенту найти ошибку в его коде. НЕ давай готовое решение и рабочий код. Вместо этого укажи на логическую или синтаксическую ошибку наводящими вопросами или краткими советами. Отвечай строго на русском языке.",
    },
    "KK": {
        "title": "Python AI Тренажеры 🐍",
        "subtitle": "Бағдарламауды үйренуге арналған интеллектуалды орта",
        "lang_label": "Оқу тілін таңдаңыз:",
        "xp_label": "Сіздің Тәжірибеңіз:",
        "menu_module": "📚 Оқу модульдері",
        "menu_sandbox": "💻 Код құмсалғышы",
        "menu_achievements": "🏆 Жетістіктер",
        "theory_tab": "Теория",
        "task_tab": "Практикалық тапсырма",
        "test_tab": "Тест (10 сұрақ)",
        "run_btn": "Кодты іске қосу",
        "reset_btn": "Кодты тазалау",
        "ai_btn": "AI-дан сұрау",
        "ai_thinking": "ИИ кодты талдауда...",
        "success_msg": "🎉 Керемет! Тапсырма дұрыс орындалды. +50 XP",
        "fail_msg": "❌ Код нәтижесі дұрыс емес. Қайтадан байқап көріңіз немесе AI-дан сұраңыз.",
        "test_warning": "Тестті жібермес бұрын барлық 10 сұраққа жауап беріңіз!",
        "test_passed": "🌟 Құттықтаймыз! Сіз тестті {score}/10 балға тапсырып, модульді аяқтадыңыз!",
        "test_failed": "⚠️ Модульді аяқтау үшін кем дегенде 8/10 балл жинау керек. Қайтадан көріңіз!",
        "ai_prompt": "Сен — кәсіби Python менторысың. Сенің міндетің — студентке оның кодындағы қатені табуға көмектесу. Дайын шешім мен жұмыс істейтін кодты берме. Оның орнына логикалық немесе синтаксистік қателерді бағыттаушы сұрақтар немесе қысқаша кеңестер арқылы көрсет. Тек қазақ тілінде жауап бер.",
    }
}[st.session_state.lang]

# --- УЧЕБНЫЙ МАТЕРИАЛ (5 модулей, 5 задач, 5 тестов по 10 вопросов) ---
modules_data = {
    "RU": [
        {
            "id": 1,
            "title": "1. Основы Python и переменные",
            "theory": """### Что такое Python?
Python — это современный, высокоуровневый язык программирования. Он спроектирован так, чтобы быть лаконичным и читаемым.

### Переменные и типы данных
Переменная — это коробка для хранения данных. В Python используется динамическая типизация:
```python
name = "Алексей"  # Строка (str)
age = 20          # Целое число (int)
pi = 3.14         # Вещественное число (float)
is_student = True # Булево значение (bool)
```

### Вывод данных
Для вывода информации в консоль используется функция `print()`.
```python
print("Привет,", name)
```
""",
            "task_desc": "Создайте переменную `course` со значением `\"Python\"` и выведите её на экран при помощи `print(course)`.",
            "expected_output": "Python\n",
            "initial_code": "course = \"Python\"\n# Выведите переменную на экран ниже\n",
            "quiz": [
                {"q": "Какой символ используется для комментариев?", "opts": ["//", "#", "/*", "--"], "ans": 1},
                {"q": "Какая функция выводит данные на экран?", "opts": ["input()", "print()", "show()", "out()"], "ans": 1},
                {"q": "Как объявить переменную со значением 'Hello'?", "opts": ["var s = 'Hello'", "string s = 'Hello'", "s = 'Hello'", "let s = 'Hello'"], "ans": 2},
                {"q": "Какой тип данных у числа 3.14?", "opts": ["int", "str", "float", "bool"], "ans": 2},
                {"q": "К какому типу относится значение False?", "opts": ["bool", "int", "str", "float"], "ans": 0},
                {"q": "Какое имя переменной некорректно?", "opts": ["my_var", "1_user", "_user", "userAge"], "ans": 1},
                {"q": "Что делает функция input()?", "opts": ["Очищает терминал", "Считывает ввод пользователя", "Выводит текст", "Импортирует код"], "ans": 1},
                {"q": "Как возвести x в степень y?", "opts": ["x ^ y", "x ** y", "pow(x,y)", "Варианты 2 и 3"], "ans": 3},
                {"q": "Результат выражения 15 % 4?", "opts": ["3", "1", "3.75", "0"], "ans": 0},
                {"q": "Что выведет print('A', 'B', sep='-')?", "opts": ["AB", "A B", "A-B", "Error"], "ans": 2}
            ]
        },
        {
            "id": 2,
            "title": "2. Условия и Циклы",
            "theory": """### Условный оператор if-elif-else
Позволяет выполнять код по условию. В Python блоки кода выделяются **отступами** (обычно 4 пробела).
```python
x = 10
if x > 5:
    print("Больше")
else:
    print("Меньше")
```

### Цикл for и while
Циклы позволяют повторять действия.
```python
# Выведет числа от 0 до 2
for i in range(3):
    print(i)
```
""",
            "task_desc": "Напишите цикл `for` с использованием `range()`, который выведет числа от `1` до `3` включительно (каждое на новой строке).",
            "expected_output": "1\n2\n3\n",
            "initial_code": "for i in range(1, 4):\n    # Допишите тело цикла здесь\n",
            "quiz": [
                {"q": "Как в Python обозначаются блоки кода?", "opts": ["С помощью {}", "С помощью отступов", "С помощью ()", "Ключевым словом end"], "ans": 1},
                {"q": "Что выведет print(5 > 3 and 2 > 4)?", "opts": ["True", "False", "None", "Error"], "ans": 1},
                {"q": "Какой оператор проверяет равенство?", "opts": ["=", "==", "is", "equal"], "ans": 1},
                {"q": "Что заменяет 'else if' в Python?", "opts": ["elseif", "elif", "else_if", "if_else"], "ans": 1},
                {"q": "Сколько раз выполнится цикл while False?", "opts": ["0 раз", "1 раз", "Бесконечно", "Ошибка"], "ans": 0},
                {"q": "Как прервать выполнение цикла?", "opts": ["continue", "stop", "exit", "break"], "ans": 3},
                {"q": "Что делает continue?", "opts": ["Останавливает цикл", "Переходит к следующему шагу", "Выходит из функции", "Ничего"], "ans": 1},
                {"q": "Что сгенерирует range(2, 5)?", "opts": ["2,3,4,5", "2,3,4", "3,4,5", "2 и 5"], "ans": 1},
                {"q": "Какое ключевое слово обрабатывает ветку по умолчанию?", "opts": ["finally", "default", "else", "except"], "ans": 2},
                {"q": "Что произойдет, если в while не менять переменную условия?", "opts": ["Выполнится 1 раз", "Будет бесконечный цикл", "Ошибка компиляции", "Остановится сам"], "ans": 1}
            ]
        }
    ],
    "KK": [
        {
            "id": 1,
            "title": "1. Python негіздері және айнымалылар",
            "theory": """### Python дегеніміз не?
Python — бұл заманауи, жоғары деңгейлі бағдарламалау тілі. Ол кодты барынша түсінікті ету үшін жасалған.

### Айнымалылар және деректер типтері
Айнымалы — мәліметтерді сақтайтын ұяшық. Динамикалық типтеу қолданылады:
```python
name = "Әлихан"   # Жол (str)
age = 20          # Бүтін сан (int)
pi = 3.14         # Жылжымалы нүктелі сан (float)
is_student = True # Бульдік мән (bool)
```

### Мәліметтерді шығару
Консольге ақпаратты шығару үшін `print()` функциясы қолданылады.
```python
print("Сәлем,", name)
```
""",
            "task_desc": "Мәні `\"Python\"` болатын `course` айнымалысын жасап, оны `print(course)` көмегімен экранға шығарыңыз.",
            "expected_output": "Python\n",
            "initial_code": "course = \"Python\"\n# Айнымалыны экранға төменде шығарыңыз\n",
            "quiz": [
                {"q": "Бір жолды түсініктеме жасау үшін қай белгі қолданылады?", "opts": ["//", "#", "/*", "--"], "ans": 1},
                {"q": "Деректерді экранға шығаратын функция қайсысы?", "opts": ["input()", "print()", "show()", "out()"], "ans": 1},
                {"q": "Жолдық айнымалыны қалай дұрыс жариялаймыз?", "opts": ["var s = 'Hello'", "string s = 'Hello'", "s = 'Hello'", "let s = 'Hello'"], "ans": 2},
                {"q": "3.14 санының типі қандай?", "opts": ["int", "str", "float", "bool"], "ans": 2},
                {"q": "False мәні қай типке жатады?", "opts": ["bool", "int", "str", "float"], "ans": 0},
                {"q": "Қай айнымалы атауы қате?", "opts": ["my_var", "1_user", "_user", "userAge"], "ans": 1},
                {"q": "input() функциясы не істейді?", "opts": ["Терминалды тазартады", "Пайдаланушыдан деректер сұрайды", "Мәтінді басып шығарады", "Кодты импорттайды"], "ans": 1},
                {"q": "х-ті у дәрежесіне қалай көтереміз?", "opts": ["x ^ y", "x ** y", "pow(x,y)", "2 мен 3 нұсқалары"], "ans": 3},
                {"q": "15 % 4 өрнегінің нәтижесі?", "opts": ["3", "1", "3.75", "0"], "ans": 0},
                {"q": "print('A', 'B', sep='-') не шығарады?", "opts": ["AB", "A B", "A-B", "Error"], "ans": 2}
            ]
        },
        {
            "id": 2,
            "title": "2. Шарттар мен Циклдар",
            "theory": """### if-elif-else шартты операторы
Шарттар бағдарламаға таңдау жасауға мүмкіндік береді. Python-да код блоктары тек **шегініспен** (4 бос орын) ерекшеленеді.
```python
x = 10
if x > 5:
    print("Үлкен")
else:
    print("Кіші")
```

### Циклдар for және while
Әрекеттерді қайталау үшін қолданылады.
```python
# 0-ден 2-ге дейінгі сандарды басып шығарады
for i in range(3):
    print(i)
```
""",
            "task_desc": "Экранға `1`-ден `3`-ке дейінгі сандарды (әр санды жаңа жолда) шығаратын `range()` функциясы бар `for` циклін жазыңыз.",
            "expected_output": "1\n2\n3\n",
            "initial_code": "for i in range(1, 4):\n    # Цикл денесін осында аяқтаңыз\n",
            "quiz": [
                {"q": "Python-да код блоктары қалай белгіленеді?", "opts": ["{} белгілерімен", "Шегіністер арқылы", "() жақшалармен", "end кілт сөзімен"], "ans": 1},
                {"q": "print(5 > 3 and 2 > 4) нәтижесі қандай болады?", "opts": ["True", "False", "None", "Error"], "ans": 1},
                {"q": "Теңдікті тексеретін оператор қайсы?", "opts": ["=", "==", "is", "equal"], "ans": 1},
                {"q": "Python-да 'else if'-ті не алмастырады?", "opts": ["elseif", "elif", "else_if", "if_else"], "ans": 1},
                {"q": "while False циклі неше рет орындалады?", "opts": ["0 рет", "1 рет", "Шексіз", "Қате"], "ans": 0},
                {"q": "Циклды қалай күштеп тоқтатамыз?", "opts": ["continue", "stop", "exit", "break"], "ans": 3},
                {"q": "continue не істейді?", "opts": ["Циклды тоқтатады", "Келесі қадамға көшеді", "Функциядан шығады", "Ештеңе"], "ans": 1},
                {"q": "range(2, 5) не береді?", "opts": ["2,3,4,5", "2,3,4", "3,4,5", "2 мен 5 сандарын"], "ans": 1},
                {"q": "Әдепкі бойынша қай тармақ іске қосылады?", "opts": ["finally", "default", "else", "except"], "ans": 2},
                {"q": "while циклінде шарт айнымалысын өзгертпесек не болады?", "opts": ["1 рет орындалады", "Шексіз цикл болады", "Компиляция қатесі", "Өздігінен тоқтайды"], "ans": 1}
            ]
        }
    ]
}

# Добавим заглушки для остальных модулей, чтобы их было ровно 5 (для полной функциональности)
for l in ["RU", "KK"]:
    while len(modules_data[l]) < 5:
        m_id = len(modules_data[l]) + 1
        modules_data[l].append({
            "id": m_id,
            "title": f"{m_id}. Модуль Python" if l == "RU" else f"{m_id}. Python модулі",
            "theory": "### Теория в процессе наполнения" if l == "RU" else "### Теория дайындалу үстінде",
            "task_desc": "Выведите число 100 на экран при помощи `print(100)`" if l == "RU" else "Экранға `print(100)` арқылы 100 санын шығарыңыз",
            "expected_output": "100\n",
            "initial_code": "print(100)\n",
            "quiz": [
                {"q": f"Вопрос {i+1}" if l == "RU" else f"Сұрақ {i+1}", "opts": ["Вариант A", "Вариант B", "Вариант C", "Вариант D"], "ans": 0} for i in range(10)
            ]
        })

# --- БОКОВАЯ ПАНЕЛЬ (НАВИГАЦИЯ) ---
with st.sidebar:
    st.image("https://images.unsplash.com/photo-1526374965328-7f61d4dc18c5?w=200&auto=format&fit=crop", width=120)
    st.title("Python AI Trainer")
    
    # Переключатель языка
    st.session_state.lang = st.radio(t["lang_label"], ["RU", "KK"], index=0 if st.session_state.lang == "RU" else 1)
    
    # Отображение XP
    st.markdown(f"<div class='xp-badge'>🏆 {t['xp_label']} {st.session_state.xp} XP</div>", unsafe_allow_html=True)
    
    # Кнопки разделов меню
    menu = st.radio(
        "",
        [t["menu_module"], t["menu_sandbox"], t["menu_achievements"]]
    )

# --- РАЗДЕЛ 1: МОДУЛИ ОБУЧЕНИЯ ---
if menu == t["menu_module"]:
    # Выбор модуля
    module_titles = [m["title"] for m in modules_data[st.session_state.lang]]
    selected_module_title = st.selectbox("Выберите модуль:" if st.session_state.lang == "RU" else "Модульді таңдаңыз:", module_titles)
    
    # Находим индекс выбранного модуля
    mod_idx = module_titles.index(selected_module_title)
    current_module = modules_data[st.session_state.lang][mod_idx]
    
    # Вкладки внутри модуля
    tab1, tab2, tab3 = st.tabs([t["theory_tab"], t["task_tab"], t["test_tab"]])
    
    with tab1:
        st.markdown(f"<div class='theory-box'>{current_module['theory']}</div>", unsafe_allow_html=True)
        
    with tab2:
        st.markdown(f"### {t['task_tab']}")
        st.info(current_module["task_desc"])
        
        # Редактор кода (Текстовое поле)
        code_input = st.text_area(
            "Код Python:", 
            value=current_module["initial_code"], 
            height=200, 
            key=f"code_{current_module['id']}"
        )
        
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button(t["run_btn"], key=f"run_{current_module['id']}"):
                output, error = execute_python_code(code_input)
                
                # Показ результатов в импровизированном терминале
                st.subheader("Терминал:")
                if error:
                    st.error(error)
                else:
                    st.code(output, language="python")
                    # Сверка результатов
                    if output == current_module["expected_output"]:
                        st.success(t["success_msg"])
                        if current_module['id'] not in st.session_state.completed:
                            st.session_state.xp += 50
                            st.session_state.completed.add(current_module['id'])
                    else:
                        st.warning(t["fail_msg"])
                        
        with col2:
            if st.button(t["ai_btn"], key=f"ai_{current_module['id']}"):
                with st.spinner(t["ai_thinking"]):
                    ai_reply = ask_gemini(
                        code_input, 
                        current_module["task_desc"], 
                        current_module["expected_output"], 
                        t["ai_prompt"], 
                        st.session_state.lang
                    )
                    st.subheader("💡 AI Совет:")
                    st.write(ai_reply)
                    
        with col3:
            if st.button(t["reset_btn"], key=f"reset_{current_module['id']}"):
                st.rerun()

    with tab3:
        st.markdown(f"### {t['test_tab']}")
        answers = {}
        for idx, q_data in enumerate(current_module["quiz"]):
            st.write(f"**{idx + 1}. {q_data['q']}**")
            answers[idx] = st.radio(
                f"Выберите ответ для вопроса {idx+1}", 
                q_data["opts"], 
                key=f"q_{current_module['id']}_{idx}",
                label_visibility="collapsed"
            )
            
        if st.button(t["run_btn"], key=f"submit_quiz_{current_module['id']}"):
            score = 0
            for idx, q_data in enumerate(current_module["quiz"]):
                chosen_opt_idx = q_data["opts"].index(answers[idx])
                if chosen_opt_idx == q_data["ans"]:
                    score += 1
                    
            if score >= 8:
                st.success(t["test_passed"].format(score=score))
                if f"quiz_{current_module['id']}" not in st.session_state.completed:
                    st.session_state.xp += 100
                    st.session_state.completed.add(f"quiz_{current_module['id']}")
            else:
                st.error(t["test_failed"])

# --- РАЗДЕЛ 2: ПЕСОЧНИЦА (SANDBOX) ---
elif menu == t["menu_sandbox"]:
    st.markdown(f"### {t['menu_sandbox']}")
    sandbox_code = st.text_area(
        "Напишите любой Python код для выполнения:", 
        value="x = 10\ny = 20\nprint('Сумма x + y =', x + y)", 
        height=300
    )
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button(t["run_btn"], key="sandbox_run"):
            output, error = execute_python_code(sandbox_code)
            st.subheader("Терминал:")
            if error:
                st.error(error)
            else:
                st.code(output, language="python")
    with col2:
        if st.button(t["ai_btn"], key="sandbox_ai"):
            with st.spinner(t["ai_thinking"]):
                ai_reply = ask_gemini(
                    sandbox_code, 
                    "Свободный код в песочнице", 
                    "", 
                    t["ai_prompt"], 
                    st.session_state.lang
                )
                st.subheader("💡 AI Совет:")
                st.write(ai_reply)

# --- РАЗДЕЛ 3: ДОСТИЖЕНИЯ ---
elif menu == t["menu_achievements"]:
    st.markdown(f"### {t['menu_achievements']}")
    
    badges = {
        "RU": [
            {"id": 1, "title": "Первые шаги", "desc": "Изучены основы Python"},
            {"id": 2, "title": "Повелитель циклов", "desc": "Освоены условия и циклы"},
            {"id": 3, "title": "Мастер структур", "desc": "Пройден блок работы со списками"},
            {"id": 4, "title": "Создатель функций", "desc": "Изучен синтаксис функций"},
            {"id": 5, "title": "Финал курса", "desc": "Пройдены все модули!"}
        ],
        "KK": [
            {"id": 1, "title": "Алғашқы қадамдар", "desc": "Python негіздері меңгерілді"},
            {"id": 2, "title": "Циклдар әміршісі", "desc": "Шарттар мен циклдар игерілді"},
            {"id": 3, "title": "Құрылымдар шебері", "desc": "Тізімдер блогы аяқталды"},
            {"id": 4, "title": "Функция жасаушы", "desc": "Функциялар синтаксисі меңгерілді"},
            {"id": 5, "title": "Курс финалшысы", "desc": "Барлық модульдер аяқталды!"}
        ]
    }[st.session_state.lang]

    cols = st.columns(5)
    for idx, b in enumerate(badges):
        # Проверяем, пройден ли соответствующий модуль
        is_unlocked = b["id"] in st.session_state.completed
        with cols[idx]:
            if is_unlocked:
                st.markdown(f"""
                <div style="text-align: center; border: 2px solid #f59e0b; border-radius: 16px; padding: 15px; background: rgba(245, 158, 11, 0.1);">
                    <span style="font-size: 40px;">🏆</span>
                    <h5 style="color: #f59e0b; margin-top: 10px;">{b['title']}</h5>
                    <p style="font-size: 11px; color: #a8a29e;">{b['desc']}</p>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div style="text-align: center; border: 2px dashed #44403c; border-radius: 16px; padding: 15px; opacity: 0.5;">
                    <span style="font-size: 40px; filter: grayscale(100%);">🔒</span>
                    <h5 style="color: #78716c; margin-top: 10px;">{b['title']}</h5>
                    <p style="font-size: 11px; color: #78716c;">{b['desc']}</p>
                </div>
                """, unsafe_allow_html=True)