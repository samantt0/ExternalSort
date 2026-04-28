import struct
import heapq
import os

# Размер структуры Order (как в C++)
RECORD_SIZE = 44  # 14 + 11 + 4 + 15


class Order:
    def __init__(self, order_id, customer_id, price, status):
        self.order_id = order_id
        self.customer_id = customer_id
        self.price = price
        self.status = status


def read_order_from_bin(data):
    """Читает Order из бинарных данных"""
    if len(data) < RECORD_SIZE:
        return None

    order_id = data[0:14].rstrip(b'\x00').decode('ascii', errors='ignore')
    customer_id = data[14:25].rstrip(b'\x00').decode('ascii', errors='ignore')
    price = struct.unpack('<i', data[25:29])[0]
    status = data[29:44].rstrip(b'\x00').decode('ascii', errors='ignore')

    return Order(order_id, customer_id, price, status)


def write_order_to_bin(order):
    """Записывает Order в бинарный формат"""
    order_id_bytes = order.order_id.encode('ascii')[:14].ljust(14, b'\x00')
    customer_id_bytes = order.customer_id.encode('ascii')[:11].ljust(11, b'\x00')
    price_bytes = struct.pack('<i', order.price)
    status_bytes = order.status.encode('ascii')[:15].ljust(15, b'\x00')

    return order_id_bytes + customer_id_bytes + price_bytes + status_bytes


def sort_bin(input_file, output_file, sort_key, total_records, progress_callback=None):
    """Внешняя сортировка BIN файла"""
    chunk_size = 2000000
    chunks = []

    try:
        with open(input_file, "rb") as f:
            chunk_num = 0
            while True:
                orders = []
                for _ in range(chunk_size):
                    data = f.read(RECORD_SIZE)
                    if not data or len(data) < RECORD_SIZE:
                        break

                    order = read_order_from_bin(data)
                    if order:
                        orders.append(order)

                if not orders:
                    break

                # Сортировка чанка
                orders.sort(key=lambda o: (
                    o.order_id if sort_key == 0 else
                    o.customer_id if sort_key == 1 else
                    o.price if sort_key == 2 else
                    o.status
                ))

                # Сохранение чанка
                chunk_file = f"py_chunk_{chunk_num}.bin"
                chunks.append(chunk_file)
                with open(chunk_file, "wb") as cf:
                    for order in orders:
                        cf.write(write_order_to_bin(order))

                if progress_callback:
                    progress_callback(chunk_num * 50 // ((total_records + chunk_size - 1) // chunk_size), 100)

                chunk_num += 1

        # Слияние чанков
        merge_bin_chunks(chunks, output_file, sort_key, total_records, progress_callback)

        return 0
    except Exception as e:
        print(f"Error in sort_bin: {e}")
        return -1


def merge_bin_chunks(chunk_files, output_file, sort_key, total_records, progress_callback=None):
    """Слияние отсортированных чанков BIN"""
    files = [open(cf, "rb") for cf in chunk_files]
    heap = []

    # Инициализация кучи
    for i, f in enumerate(files):
        data = f.read(RECORD_SIZE)
        if data and len(data) == RECORD_SIZE:
            order = read_order_from_bin(data)
            if order:
                sort_val = (order.order_id if sort_key == 0 else
                            order.customer_id if sort_key == 1 else
                            order.price if sort_key == 2 else
                            order.status)
                heapq.heappush(heap, (sort_val, i, order))

    # Слияние
    with open(output_file, "wb") as out:
        written = 0
        while heap:
            sort_val, file_idx, order = heapq.heappop(heap)

            out.write(write_order_to_bin(order))
            written += 1

            if progress_callback and written % 100000 == 0:
                progress_callback(50 + written * 50 // total_records, 100)

            # Читаем следующую запись из того же файла
            data = files[file_idx].read(RECORD_SIZE)
            if data and len(data) == RECORD_SIZE:
                order = read_order_from_bin(data)
                if order:
                    sort_val = (order.order_id if sort_key == 0 else
                                order.customer_id if sort_key == 1 else
                                order.price if sort_key == 2 else
                                order.status)
                    heapq.heappush(heap, (sort_val, file_idx, order))

    # Закрытие и удаление временных файлов
    for f in files:
        f.close()
    for cf in chunk_files:
        try:
            os.remove(cf)
        except:
            pass

    if progress_callback:
        progress_callback(100, 100)


def sort_csv(input_file, output_file, sort_key, total_records, progress_callback=None):
    """Внешняя сортировка CSV файла"""
    chunk_size = 3000000
    chunks = []

    try:
        with open(input_file, "r", encoding="utf-8") as f:
            header = f.readline()
            chunk_num = 0

            while True:
                orders = []
                for _ in range(chunk_size):
                    line = f.readline()
                    if not line:
                        break

                    parts = line.strip().split(",")
                    if len(parts) >= 4:
                        orders.append(Order(parts[0], parts[1], int(parts[2]), parts[3]))

                if not orders:
                    break

                # Сортировка чанка
                orders.sort(key=lambda o: (
                    o.order_id if sort_key == 0 else
                    o.customer_id if sort_key == 1 else
                    o.price if sort_key == 2 else
                    o.status
                ))

                # Сохранение в бинарный формат
                chunk_file = f"py_chunk_csv_{chunk_num}.bin"
                chunks.append(chunk_file)
                with open(chunk_file, "wb") as cf:
                    for order in orders:
                        cf.write(write_order_to_bin(order))

                if progress_callback:
                    progress_callback(chunk_num * 50 // ((total_records + chunk_size - 1) // chunk_size), 100)

                chunk_num += 1

        # Слияние в CSV
        merge_csv_chunks(chunks, output_file, header, sort_key, total_records, progress_callback)

        return 0
    except Exception as e:
        print(f"Error in sort_csv: {e}")
        return -1


def merge_csv_chunks(chunk_files, output_file, header, sort_key, total_records, progress_callback=None):
    """Слияние чанков в CSV формат"""
    files = [open(cf, "rb") for cf in chunk_files]
    heap = []

    for i, f in enumerate(files):
        data = f.read(RECORD_SIZE)
        if data and len(data) == RECORD_SIZE:
            order = read_order_from_bin(data)
            if order:
                sort_val = (order.order_id if sort_key == 0 else
                            order.customer_id if sort_key == 1 else
                            order.price if sort_key == 2 else
                            order.status)
                heapq.heappush(heap, (sort_val, i, order))

    with open(output_file, "w", encoding="utf-8") as out:
        out.write(header)
        written = 0

        while heap:
            sort_val, file_idx, order = heapq.heappop(heap)

            out.write(f"{order.order_id},{order.customer_id},{order.price},{order.status}\n")
            written += 1

            if progress_callback and written % 100000 == 0:
                progress_callback(50 + written * 50 // total_records, 100)

            data = files[file_idx].read(RECORD_SIZE)
            if data and len(data) == RECORD_SIZE:
                order = read_order_from_bin(data)
                if order:
                    sort_val = (order.order_id if sort_key == 0 else
                                order.customer_id if sort_key == 1 else
                                order.price if sort_key == 2 else
                                order.status)
                    heapq.heappush(heap, (sort_val, file_idx, order))

    for f in files:
        f.close()
    for cf in chunk_files:
        try:
            os.remove(cf)
        except:
            pass

    if progress_callback:
        progress_callback(100, 100)