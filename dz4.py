import os
import time
import threading
import multiprocessing
from queue import Queue

# -------------------------------
# Основна функція для пошуку ключових слів у файлі
# -------------------------------

def search_in_file(filepath, keywords):
    found = {word: [] for word in keywords}
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            text = f.read().lower()
            for word in keywords:
                count = text.count(word.lower())
                if count > 0:
                    found[word].append((filepath, count))
    except Exception as e:
        print(f"[Помилка] Неможливо відкрити файл {filepath}: {e}")
    return found


# -------------------------------
# БАГАТОПОТОКОВИЙ ВАРІАНТ
# -------------------------------

# num_threads - кількість потоків для створення
def threaded_search(file_list, keywords, num_threads=4):
    results = {word: [] for word in keywords}
    queue = Queue()

    for f in file_list:
        queue.put(f)

    # lock для синхронізації доступу до results
    lock = threading.Lock()

    def worker():
        while not queue.empty():
            try:
                filepath = queue.get_nowait()
            except Exception:
                break  # черга порожня

            try:
                found = search_in_file(filepath, keywords)
                with lock:
                    for word, files in found.items():
                        results[word].extend(files)
            except Exception as e:
                print(f"[Помилка у потоці] помилка при обробці файлу {filepath}: {e}")
            finally:
                queue.task_done()

    threads = []
    for _ in range(num_threads):
        t = threading.Thread(target=worker)
        t.start()
        threads.append(t)

    # Очікуємо завершення всіх потоків
    queue.join()
    for t in threads:
        t.join()

    return results


# -------------------------------
# БАГАТОПРОЦЕСОРНИЙ ВАРІАНТ
# -------------------------------
def process_worker(file_chunk, keywords, queue):
    local_results = {word: [] for word in keywords}
    try:
        for filepath in file_chunk:
            found = search_in_file(filepath, keywords)
            for word, files in found.items():
                local_results[word].extend(files)
    except Exception as e:
        print(f"[Помилка у процесі] Виникла проблема під час обробки: {e}")
    finally:
        queue.put(local_results)


# num_processes - кількість процесів для створення
def multiprocessing_search(file_list, keywords, num_processes=4):
    results = {word: [] for word in keywords}

    # Розбиваємо список файлів на рівні частини, але без додаткової логіки
    # все просто — як у твоєму коді
    chunk_size = max(1, len(file_list) // num_processes)
    chunks = [file_list[i:i + chunk_size] for i in range(0, len(file_list), chunk_size)]

    queue = multiprocessing.Queue()
    processes = []

    for chunk in chunks:
        p = multiprocessing.Process(target=process_worker, args=(chunk, keywords, queue))
        p.start()
        processes.append(p)

    # Очікуємо завершення всіх процесів
    for p in processes:
        p.join()

    while not queue.empty():
        local_results = queue.get()
        for word, files in local_results.items():
            results[word].extend(files)

    return results



if __name__ == "__main__":

    # Введення шляху до папки з файлами
    folder = input("Введіть шлях до папки з .txt файлами: ")
    if not os.path.isdir(folder):
        print("Вказана папка не існує.")
        exit(-1)

    # Збір усіх .txt файлів
    files = [os.path.join(folder, f) for f in os.listdir(folder) if f.endswith(".txt")]
    if not files:
        print("У вказаній папці немає .txt файлів.")
        exit(-1)
    else:
        print(f"Знайдено {len(files)} файлів для обробки.")
    
    keywords = input("Введіть ключові слова для пошуку (через кому): ").split(',')
    keywords = [k.strip() for k in keywords if k.strip()]
    # print(f"Шукаємо ключові слова: {keywords}")



    # ----------------------------
    # пошук з використанням багатопотоковості та багатопроцесорності
    #-----------------------------

    # --- Багатопотокова версія ---
    start = time.time()
    thread_results = threaded_search(files, keywords, num_threads=4)
    thread_time = time.time() - start

    print("\n=== Результати пошуку (threading) ===")
    for k, v in thread_results.items():
        if v:
            print(f"{k}:")
            total_count = 0
            for path, count in v:
                total_count += count
                print(f" --> {path} (збігів: {count})")
        else:
            print(f"{k}: не знайдено")
    print(f"Час виконання threading: {thread_time:.8f} c")

    # --- Багатопроцесорна версія ---
    start = time.time()
    process_results = multiprocessing_search(files, keywords, num_processes=4)
    process_time = time.time() - start

    print("\n=== Результати пошуку (multiprocessing) ===")
    for k, v in process_results.items():
        if v:
            print(f"{k}:")
            total_count = 0
            for path, count in v:
                total_count += count
                print(f" --> {path} (збігів: {count})")
        else:
            print(f"{k}: не знайдено")
    print(f"Час виконання multiprocessing: {process_time:.8f} c")
