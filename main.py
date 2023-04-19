import math

# Входные данные
sum_arr = [
    "1_1000",
    "2_30000",
    "3_100000",
    "8_100",
    "5_11111",
    "9_14124124124",
    "6_444",
    "4_123456",
    "7_100000000000",
    "10_81214",
]
rate_arr = [
    "1_10",
    "2_11",
    "3_8",
    "4_13",
    "5_11",
    "6_6",
    "7_9",
    "8_11",
    "9_13",
    "10_12",
]
term_arr = ["1_1", "2_2", "3_2", "4_6", "5_8", "6_20", "7_9", "8_11", "9_13", "10_12"]


# Функция для расчета итоговой суммы по каждой строке
def calculate_end_sum(start_sum, rate, term):
    r = rate / 100
    n = term
    return start_sum * (1 + r) ** n


# Создаем список словарей с данными по каждой строке
result_arr = []
for i in range(len(sum_arr)):
    id, start_sum = sum_arr[i].split("_")
    id, rate = rate_arr[i].split("_")
    id, term = term_arr[i].split("_")
    id = int(id)
    start_sum = int(start_sum)
    rate = float(rate)
    term = int(term)
    end_sum = calculate_end_sum(start_sum, rate, term)
    result_arr.append(
        {
            "id": id,
            "start_sum": start_sum,
            "rate": rate,
            "term": term,
            "end_sum": math.ceil(end_sum),
        }
    )

# Результат
for item in result_arr:
    print(
        f"id: {item['id']}\nstart_sum: {item['start_sum']}\nrate: {item['rate']}\nterm: {item['term']}\nend_sum: {item['end_sum']}\n"
    )
