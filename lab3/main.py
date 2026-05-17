# Подключаем библиотеку PIL для работы с изображениями
from PIL import Image
import os

# Кодировка Windows-1251 для поддержки кириллицы
ENCODING = 'cp1251'

def read_keys(filename: str):
    # Чтение координат пикселей из файла
    # Формат файла: каждая строка содержит координаты в скобках
    # Возвращает список кортежей (x, y)
    coords = []
    # Открываем файл с ключами в режиме чтения, кодировка UTF-8
    with open(filename, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()  # Удаляем пробелы и символы перевода строки
            if line:  # Пропускаем пустые строки
                # Удаляем круглые скобки: (150, 451) - "150, 451"
                line = line.strip('()')
                # Разделяем по запятой и преобразуем в целые числа
                x, y = map(int, line.split(','))
                coords.append((x, y))
    return coords

def decode_task1(image_path: str, keys_file: str):
    # 1.1: Декодирование текста из изображения
    # Каждый байт текста записан в синий канал (B) пикселя
    # Координаты пикселей берутся из файла keys.txt
    print("1.1.\n")
    # Читаем координаты пикселей из файла с ключами
    coords = read_keys(keys_file)
    print(f"Загружено координат: {len(coords)}")

    # Открываем изображение
    img = Image.open(image_path)
    # Преобразуем в RGB, если изображение в другом формате (например, RGBA)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    pixels = img.load()  # Загружаем пиксели для быстрого доступа

    # Шаг 3: Читаем байты из синего канала по указанным координатам
    data = bytearray()  # Массив для хранения прочитанных байтов
    for x, y in coords:
        try:
            # pixels[x, y] возвращает кортеж (R, G, B)
            b = pixels[x, y][2]  # Индекс 2 - это синий канал (Blue)
            data.append(b)  # Добавляем байт в массив
        except Exception as e:
            print(f"Ошибка на координате ({x},{y}): {e}")

    # Декодируем байты в текст с помощью кодировки cp1251
    text = data.decode(ENCODING, errors='ignore')

    # Выводим результат
    print(f"\nДекодированное сообщение:")
    print(text)

    # Сохраняем результат в файл
    with open("decoded_message.txt", "w", encoding=ENCODING) as f:
        f.write(text)
    print("\nСохранено в decoded_message.txt")

    return text

def encode_task2(text: str, output_image: str):
    # 1.2: Кодирование текста в изображение
    # Метод: 0-е биты красного (R) и зелёного (G) каналов используются для записи битов сообщения
    # Чётные биты (0,2,4,6) записываются в красный канал
    # Нечётные биты (1,3,5,7) записываются в зелёный канал
    print("\n1.2.\n")

    # Преобразуем текст в байты с помощью кодировки cp1251
    bytes_data = text.encode(ENCODING)
    print(f"Текст для кодирования: \"{text}\"")
    print(f"Байтовое представление (hex): {bytes_data.hex()}")
    print(f"Всего байт: {len(bytes_data)}")

    # Извлекаем все биты из байтов (младший бит - первый)
    # Например, для байта 0x48 (72): биты будут [0,0,0,1,0,0,1,0]
    bits = []
    for b in bytes_data:
        for i in range(8):  # 8 бит в байте
            # (b >> i) & 1 - получаем i-й бит (0 - младший, 7 - старший)
            bits.append((b >> i) & 1)

    print(f"Всего бит для записи: {len(bits)}")

    # Рассчитываем размер изображения
    # В каждом пикселе можно записать 2 бита (в R и G каналы)
    pixels_needed = (len(bits) + 1) // 2  # Округление вверх
    width = 20  # Фиксированная ширина для простоты
    height = (pixels_needed // width) + 2  # +2 для запаса

    # Создаём новое белое изображение
    # (255,255,255) - белый цвет
    img = Image.new('RGB', (width, height), (255, 255, 255))
    pixels = img.load()

    print(f"Размер создаваемого изображения: {width} x {height}")
    print(f"Всего пикселей: {width * height}, необходимо: {pixels_needed}")

    # Кодируем биты в изображение
    x, y = 0, 0  # Начинаем с верхнего левого угла
    bit_idx = 0  # Индекс текущего бита

    while bit_idx < len(bits):
        # Получаем текущий пиксель (по умолчанию (255,255,255) - белый)
        r, g, b = pixels[x, y]

        # Запись в красный канал
        if bit_idx < len(bits):
            # Устанавливаем 0-й бит: (r & 0xFE) обнуляет младший бит, | bit устанавливает нужное значение
            new_r = (r & 0xFE) | bits[bit_idx]
            bit_idx += 1
        else:
            new_r = r

        # Запись в зеленый канал
        if bit_idx < len(bits):
            new_g = (g & 0xFE) | bits[bit_idx]
            bit_idx += 1
        else:
            new_g = g

        # Сохраняем изменённый пиксель в изображении
        pixels[x, y] = (new_r, new_g, b)

        # Переход к следующему пикселю (построчно)
        x += 1
        if x >= width:  # Если дошли до конца строки
            x = 0  # Переходим в начало следующей строки
            y += 1

    # Сохраняем закодированное изображение
    img.save(output_image)
    print(f"\nИзображение сохранено: {output_image}")
    print(f"Закодировано {len(bytes_data)} байт ({len(bits)} бит)")

    return output_image, len(bytes_data)

def decode_task2(image_path: str, expected_bytes: int):
    # Декодирование текста из изображения, закодированного методом R0/G0
    # Используется для проверки корректности кодирования
    print("\nПроверка:\n")

    # Открываем изображение
    img = Image.open(image_path)
    if img.mode != 'RGB':
        img = img.convert('RGB')
    pixels = img.load()
    width, height = img.size

    # Читаем биты в том же порядке, в котором они были записаны
    # Сначала R0, потом G0 каждого пикселя
    bits = []
    for y in range(height):
        for x in range(width):
            r, g, b = pixels[x, y]
            bits.append(r & 1)  # Извлекаем 0-й бит из красного канала
            bits.append(g & 1)  # Извлекаем 0-й бит из зелёного канала

    print(f"Всего считано битов из изображения: {len(bits)}")

    # Обрезаем лишние биты (оставляем только нужное количество)
    needed_bits = expected_bytes * 8
    bits = bits[:needed_bits]
    print(f"Используем для декодирования: {len(bits)} бит (должно быть {needed_bits})")

    # Преобразуем биты обратно в байты
    byte_data = bytearray()
    for i in range(0, len(bits), 8):
        if i + 8 <= len(bits):
            byte_val = 0
            for j in range(8):
                # Собираем байт: бит j сдвигается на j позиций
                byte_val |= (bits[i + j] << j)
            byte_data.append(byte_val)

    print(f"Сформировано байт: {len(byte_data)} (ожидалось {expected_bytes})")

    # Декодируем байты в текст
    text = byte_data.decode(ENCODING, errors='replace')
    print(f"\nДекодированный текст: {text}")

    return text

def main():
    # 1.1
    keys_file = "keys17.txt"  # Файл с координатами
    image_file = "new17.png"  # Закодированное изображение

    # Проверяем, существуют ли файлы
    if os.path.exists(keys_file) and os.path.exists(image_file):
        decoded_text = decode_task1(image_file, keys_file)
    else:
        print(f"\nДля задания 1.1 нужны файлы: {keys_file} и {image_file}")

    # 1.2
    # Текст для кодирования
    test_text = "Hello, 24_IST_2!"

    # Кодируем текст в изображение
    output_img, num_bytes = encode_task2(test_text, "encoded_task2.png")

    # Декодируем полученное изображение для проверки
    decoded_check = decode_task2(output_img, num_bytes)

    # Сравниваем результаты
    print("\nПроверка сообщения:\n")
    print(f"Оригинальный текст: \"{test_text}\"")
    print(f"Расшифрованный текст: \"{decoded_check}\"")

    if test_text == decoded_check:
        print("\nУспешно!")
    else:
        print("\nНе успешно!")

# Точка входа в программу
if __name__ == "__main__":
    main()