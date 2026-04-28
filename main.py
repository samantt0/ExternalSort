from tkinter import *
from tkinter import ttk
import ctypes
import threading
import struct

# Подключение библиотеки
lib = ctypes.CDLL("./generation&sort.dll")
PROGRESS_FUNC = ctypes.CFUNCTYPE(None, ctypes.c_int, ctypes.c_int)

# Количество записей
N_BIN = 25000000
N_CSV = 37000000

# Настройка функций
lib.generate_bin.argtypes = [ctypes.c_int, PROGRESS_FUNC]
lib.generate_bin.restype = ctypes.c_int

lib.generate_csv.argtypes = [ctypes.c_int, PROGRESS_FUNC]
lib.generate_csv.restype = ctypes.c_int

lib.sort_bin.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_int, PROGRESS_FUNC]
lib.sort_bin.restype = ctypes.c_int

lib.sort_csv.argtypes = [ctypes.c_char_p, ctypes.c_char_p, ctypes.c_int, ctypes.c_int, PROGRESS_FUNC]
lib.sort_csv.restype = ctypes.c_int

lib.check_bin.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int, PROGRESS_FUNC]
lib.check_bin.restype = ctypes.c_int

lib.check_csv.argtypes = [ctypes.c_char_p, ctypes.c_int, ctypes.c_int, PROGRESS_FUNC]
lib.check_csv.restype = ctypes.c_int

# ВАЖНО: Структура должна быть выровнена так же, как в C++
# C++ использует #pragma pack(push, 1), что означает выравнивание по 1 байту
RECORD_SIZE = 14 + 11 + 4 + 15  # = 44 байта


def set_buttons(state):
    for btn in [buttonGenBin, buttonGenCsv, buttonSortBin, buttonSortCsv,
                buttonCheckBin, buttonCheckCsv, buttonSortPyBin, buttonSortPyCsv]:
        btn.config(state=state)


def make_callback():
    def cb(current, total):
        percent = current / total * 100
        progressBar["value"] = percent
        labelProgress.config(text=f"{percent:.1f}%")
        root.update_idletasks()

    return PROGRESS_FUNC(cb)


# Генерация
def generate(type):
    set_buttons(DISABLED)
    progressBar["value"] = 0
    labelProgress.config(text="0%")
    callback = make_callback()

    def run():
        if type == "bin":
            lib.generate_bin(N_BIN, callback)
        else:
            lib.generate_csv(N_CSV, callback)
        set_buttons(NORMAL)
        labelProgress.config(text="Готово!")

    threading.Thread(target=run, daemon=True).start()


# Выбор ключа сортировки
def sort_key(mode, use_python=False):
    window = Toplevel(root)
    window.title("Поле для сортировки")
    window.geometry("320x180")
    window.resizable(False, False)

    Label(window, text="Выберите поле для сортировки:", font=("Arial", 10, "bold")).pack(pady=10)

    btn_frame = Frame(window)
    btn_frame.pack(fill="both", expand=True, padx=20, pady=5)

    Button(btn_frame, text="ID заказа", width=25,
           command=lambda: [window.destroy(), start_sort(mode, 0, use_python)]).pack(pady=3)
    Button(btn_frame, text="ID клиента", width=25,
           command=lambda: [window.destroy(), start_sort(mode, 1, use_python)]).pack(pady=3)
    Button(btn_frame, text="Цена", width=25,
           command=lambda: [window.destroy(), start_sort(mode, 2, use_python)]).pack(pady=3)
    Button(btn_frame, text="Статус", width=25,
           command=lambda: [window.destroy(), start_sort(mode, 3, use_python)]).pack(pady=3)


# Сортировка
def start_sort(mode, sort_key_val, use_python=False):
    set_buttons(DISABLED)
    progressBar["value"] = 0
    labelProgress.config(text="0%")
    callback = make_callback()

    def run():
        try:
            if use_python:
                import external_sort_py

                if mode == "bin":
                    result = external_sort_py.sort_bin("orders.bin", "orders.bin", sort_key_val, N_BIN, callback)
                else:
                    result = external_sort_py.sort_csv("orders.csv", "orders.csv", sort_key_val, N_CSV, callback)
            else:
                if mode == "bin":
                    result = lib.sort_bin(b"orders.bin", b"orders.bin", sort_key_val, N_BIN, callback)
                else:
                    result = lib.sort_csv(b"orders.csv", b"orders.csv", sort_key_val, N_CSV, callback)

            if result == 0:
                labelProgress.config(text="Готово!")
            else:
                labelProgress.config(text="Ошибка!")
        except Exception as e:
            labelProgress.config(text=f"Ошибка: {str(e)}")
        finally:
            set_buttons(NORMAL)

    threading.Thread(target=run, daemon=True).start()


# Выбор ключа проверки
def check_key(mode):
    window = Toplevel(root)
    window.title("Поле для проверки")
    window.geometry("320x180")
    window.resizable(False, False)

    Label(window, text="Выберите поле для проверки:", font=("Arial", 10, "bold")).pack(pady=10)

    btn_frame = Frame(window)
    btn_frame.pack(fill="both", expand=True, padx=20, pady=5)

    Button(btn_frame, text="ID заказа", width=25,
           command=lambda: [window.destroy(), start_check(mode, 0)]).pack(pady=3)
    Button(btn_frame, text="ID клиента", width=25,
           command=lambda: [window.destroy(), start_check(mode, 1)]).pack(pady=3)
    Button(btn_frame, text="Цена", width=25,
           command=lambda: [window.destroy(), start_check(mode, 2)]).pack(pady=3)
    Button(btn_frame, text="Статус", width=25,
           command=lambda: [window.destroy(), start_check(mode, 3)]).pack(pady=3)


# Проверка
def start_check(mode, sort_key_val):
    set_buttons(DISABLED)
    progressBar["value"] = 0
    labelProgress.config(text="0%")
    callback = make_callback()

    def run():
        if mode == "bin":
            result = lib.check_bin(b"orders.bin", sort_key_val, N_BIN, callback)
        else:
            result = lib.check_csv(b"orders.csv", sort_key_val, N_CSV, callback)

        if result == 0:
            labelProgress.config(text="Файл упорядочен!")
        elif result == -1:
            labelProgress.config(text="Ошибка открытия файла!")
        else:
            labelProgress.config(text=f"Нарушение на записи {result + 1}!")

        set_buttons(NORMAL)

    threading.Thread(target=run, daemon=True).start()


# Загрузка BIN
def load_bin():
    table.delete(*table.get_children())
    try:
        with open("orders.bin", "rb") as f:
            record_count = 0

            while record_count < 1000:
                # Читаем ровно 44 байта (размер структуры Order)
                data = f.read(RECORD_SIZE)

                if not data or len(data) < RECORD_SIZE:
                    break

                # Разбираем структуру вручную:
                # char order_id[14] - байты 0-13
                # char customer_id[11] - байты 14-24
                # int total_price - байты 25-28 (4 байта)
                # char order_status[15] - байты 29-43

                order_id_bytes = data[0:14]
                customer_id_bytes = data[14:25]
                price_bytes = data[25:29]
                status_bytes = data[29:44]

                # Декодируем строки
                try:
                    order_id = order_id_bytes.rstrip(b'\x00').decode("ascii", errors='ignore')
                    customer_id = customer_id_bytes.rstrip(b'\x00').decode("ascii", errors='ignore')
                    status = status_bytes.rstrip(b'\x00').decode("ascii", errors='ignore')

                    # Распаковываем int (little-endian)
                    price = struct.unpack('<i', price_bytes)[0]

                    # Вставляем в таблицу
                    table.insert("", END, values=(record_count + 1, order_id, customer_id, price, status))
                    record_count += 1

                except Exception as e:
                    print(f"Ошибка декодирования записи {record_count}: {e}")
                    # Показываем сырые данные для отладки
                    print(f"Raw data: {data.hex()}")
                    continue

        labelProgress.config(text=f"Загружено {record_count} записей из BIN файла")

    except FileNotFoundError:
        labelProgress.config(text="Файл orders.bin не найден")
    except Exception as e:
        labelProgress.config(text=f"Ошибка чтения: {str(e)}")
        print(f"Detailed error: {e}")


# Загрузка CSV
def load_csv():
    table.delete(*table.get_children())
    try:
        with open("orders.csv", "r", encoding="utf-8") as f:
            next(f)  # Пропуск заголовка
            for i, line in enumerate(f):
                if i >= 1000:
                    break
                parts = line.strip().split(",")
                if len(parts) >= 4:
                    table.insert("", END, values=(i + 1, parts[0], parts[1], parts[2], parts[3]))

        labelProgress.config(text=f"Загружено записей из CSV файла")
    except FileNotFoundError:
        labelProgress.config(text="Файл orders.csv не найден")
    except Exception as e:
        labelProgress.config(text=f"Ошибка чтения: {str(e)}")


# Интерфейс
root = Tk()
root.title("Сортировка больших файлов - Заказы")
root.geometry("950x550")
root.resizable(True, True)

# Верхняя панель с кнопками генерации
frameGen = LabelFrame(root, text="Генерация файлов", font=("Arial", 9, "bold"))
frameGen.pack(fill="x", padx=10, pady=5)

buttonGenBin = Button(frameGen, text="📁 Создать BIN", width=20, command=lambda: generate("bin"))
buttonGenBin.pack(side=LEFT, padx=5, pady=5)

buttonGenCsv = Button(frameGen, text="📄 Создать CSV", width=20, command=lambda: generate("csv"))
buttonGenCsv.pack(side=LEFT, padx=5, pady=5)

# Панель сортировки C++ DLL
frameSortDLL = LabelFrame(root, text="Сортировка (C++ DLL)", font=("Arial", 9, "bold"))
frameSortDLL.pack(fill="x", padx=10, pady=5)

buttonSortBin = Button(frameSortDLL, text="⚡ Сортировать BIN", width=20, command=lambda: sort_key("bin"))
buttonSortBin.pack(side=LEFT, padx=5, pady=5)

buttonSortCsv = Button(frameSortDLL, text="⚡ Сортировать CSV", width=20, command=lambda: sort_key("csv"))
buttonSortCsv.pack(side=LEFT, padx=5, pady=5)

# Панель сортировки Python
frameSortPy = LabelFrame(root, text="Сортировка (Python модуль)", font=("Arial", 9, "bold"))
frameSortPy.pack(fill="x", padx=10, pady=5)

buttonSortPyBin = Button(frameSortPy, text="🐍 Сортировать BIN (Py)", width=20,
                         command=lambda: sort_key("bin", use_python=True))
buttonSortPyBin.pack(side=LEFT, padx=5, pady=5)

buttonSortPyCsv = Button(frameSortPy, text="🐍 Сортировать CSV (Py)", width=20,
                         command=lambda: sort_key("csv", use_python=True))
buttonSortPyCsv.pack(side=LEFT, padx=5, pady=5)

# Панель проверки и просмотра
frameCheck = LabelFrame(root, text="Проверка и просмотр", font=("Arial", 9, "bold"))
frameCheck.pack(fill="x", padx=10, pady=5)

buttonCheckBin = Button(frameCheck, text="✓ Проверить BIN", width=15, command=lambda: check_key("bin"))
buttonCheckBin.pack(side=LEFT, padx=5, pady=5)

buttonCheckCsv = Button(frameCheck, text="✓ Проверить CSV", width=15, command=lambda: check_key("csv"))
buttonCheckCsv.pack(side=LEFT, padx=5, pady=5)

buttonLoadBin = Button(frameCheck, text="👁 Показать BIN", width=15, command=load_bin)
buttonLoadBin.pack(side=RIGHT, padx=5, pady=5)

buttonLoadCsv = Button(frameCheck, text="👁 Показать CSV", width=15, command=load_csv)
buttonLoadCsv.pack(side=RIGHT, padx=5, pady=5)

# Прогресс бар
frameProgress = Frame(root)
frameProgress.pack(fill="x", padx=10, pady=5)

progressBar = ttk.Progressbar(frameProgress, maximum=100)
progressBar.pack(fill="x", side=LEFT, expand=True, padx=5)

labelProgress = Label(frameProgress, text="Готов к работе", width=20, anchor="w")
labelProgress.pack(side=LEFT, padx=5)

# Таблица
frameTable = LabelFrame(root, text="Данные файла (первые 1000 записей)", font=("Arial", 9, "bold"))
frameTable.pack(fill="both", expand=True, padx=10, pady=5)

scrollbar = ttk.Scrollbar(frameTable)
scrollbar.pack(side=RIGHT, fill="y")

columns = ("id", "order_id", "customer_id", "price", "status")
table = ttk.Treeview(frameTable, columns=columns, show="headings", yscrollcommand=scrollbar.set)
table.heading("id", text="№")
table.heading("order_id", text="ID заказа")
table.heading("customer_id", text="ID клиента")
table.heading("price", text="Цена")
table.heading("status", text="Статус")

table.column("id", width=50, anchor="center")
table.column("order_id", width=150, anchor="w")
table.column("customer_id", width=120, anchor="w")
table.column("price", width=100, anchor="e")
table.column("status", width=120, anchor="w")

table.pack(side=LEFT, expand=True, fill="both", padx=5, pady=5)
scrollbar.config(command=table.yview)

root.mainloop()