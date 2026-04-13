import wave
import numpy as np
import matplotlib.pyplot as plt

filename = 'voice.wav'
def read_wav(filename):
    try:
        with wave.open(filename, 'r') as wav_file:
            # получаем параметры файла
            sample_rate = wav_file.getframerate()
            n_frames = wav_file.getnframes()

            # читаем все отсчёты
            raw_data = wav_file.readframes(n_frames)
            # преобразуем в массив numpy
            audio_data = np.frombuffer(raw_data, dtype=np.int16)
            return audio_data, sample_rate
    except FileNotFoundError:
        print(f"файл '{filename}' не найден.")
        return None, None
    except Exception as e:
        print(f"ошибка при чтении файла: {e}")
        return None, None


def analyze_audio():
    # читаем файл
    audio_data, sample_rate = read_wav(filename)
    if audio_data is None:
        return

    print(f"частота дискретизации: {sample_rate} Гц")
    print(f"количество отсчетов: {len(audio_data)}")
    print(f"длительность: {len(audio_data) / sample_rate:.2f} секунд")

    # запрашиваем количество отсчётов для визуализации
    while True:
        try:
            num_samples = int(input(f"\nвведите количество отсчетов для отображения (1–{len(audio_data)}): "))
            if 1 <= num_samples <= len(audio_data):
                break
            else:
                print(f"введите число от 1 до {len(audio_data)}")
        except ValueError:
            print("введите целое число")

    # берём нужное количество отсчетов
    selected_data = audio_data[:num_samples]
    time_axis = np.arange(num_samples) / sample_rate  # ось времени в секундах

    # 2.1 визуализация отсчетов
    plt.figure(figsize=(12, 8))

    plt.subplot(2, 2, 1)
    plt.plot(time_axis, selected_data, 'r--', linewidth=1)  # пунктирная линия
    plt.title("отсчеты звукового сигнала")
    plt.xlabel("время, с")
    plt.ylabel("амплитуда, м")
    plt.grid(True)

    # 2.2 осциллограмма всего сигнала
    plt.subplot(2, 2, 2)
    full_time = np.arange(len(audio_data)) / sample_rate
    plt.plot(full_time, audio_data, 'b-', linewidth=0.8)
    plt.title("осциллограмма звукового сигнала")
    plt.xlabel("время, с")
    plt.ylabel("амплитуда, м")
    plt.grid(True)

    # 2.3 спектральный анализ
    plt.subplot(2, 2, 3)
    # вычисляем ДПФ
    fft_result = np.fft.fft(audio_data)
    # квадрат модуля
    power_spectrum = np.abs(fft_result) ** 2
    # частотная ось
    freq_axis = np.fft.fftfreq(len(power_spectrum), 1 / sample_rate)
    # берём положительную часть спектра
    positive_freq = freq_axis[:len(freq_axis) // 2]
    positive_power = power_spectrum[:len(power_spectrum) // 2]

    plt.plot(positive_freq, positive_power, 'g-', linewidth=1)
    plt.title("спектр сигнала")
    plt.xlabel("частота, Гц")
    plt.ylabel("мощность (|X(f)|²)")
    plt.grid(True)
    plt.xlim(0, sample_rate / 2)  # до частоты Найквиста

    # 2.4 гистограмма отсчётов сигнала
    plt.subplot(2, 2, 4)
    plt.hist(audio_data, bins=100, color='purple', alpha=0.7)
    plt.title("гистограмма амплитуд сигнала")
    plt.xlabel("амплитуда отсчета, м")
    plt.ylabel("количество отсчетов, n")
    plt.grid(True)

    # расположение графиков
    plt.tight_layout()
    plt.show()

# Запуск программы
if __name__ == "__main__":
    analyze_audio()
