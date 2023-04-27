import yaml
import json
import csv
import time

##################################################

# Открытие файла credit.json и чтение его содержимого
##################################################
with open("credit.json") as f:
    credit_data = json.load(f)
# Вложенный словарь кредитов с ключами id
credit_dict = {}
for credit in credit_data:
    credit_dict[credit['id']] = {
        'percent': credit['percent'],
        'sum': credit['sum'],
        'term': credit['term']
    }
# print (credit_dict)
##################################################

# Открытие файла deposit.yaml и чтение его содержимого
##################################################
with open("deposit.yaml") as f:
    deposit_data = yaml.safe_load(f)
# Создание списка словарей с атрибутами депозитов
deposit_dict = {}
for deposit in deposit_data:
    deposit_dict[deposit['id']] = {
        'percent': deposit['percent'],
        'sum': deposit['sum'],
        'term': deposit['term']
    }
##################################################

# Открытие файла account.csv и чтение его содержимого
##################################################
with open('account.csv', newline='') as f:
    reader = csv.reader(f)
    next(reader)  # Пропуск заголовка
    account_data = list(reader)
# Создание вложенного словаря с ключами id
accounts = {}
for row in account_data:
    accounts[int(row[0])] = {'amount': int(row[1])}
##################################################
# Функция кредита
##################################################
def credit (id):
    if "credit_status" not in accounts[id]:
        if credit_dict[id]["sum"] > 0:
            accounts[id]["amount"] = accounts[id]["amount"] + credit_dict[id]["sum"]
            accounts[0]["amount"] = accounts[0]["amount"] - credit_dict[id]["sum"]
            accounts[id]["credit_status"] = "on"
            accounts[id]["total_mounth"] = 12 * credit_dict[id]["term"]
            accounts[id]["current_mounth"] = 12 * credit_dict[id]["term"]
            accounts[id]["monthly_write_off"] = (credit_dict[id]["sum"] * ((1 + (credit_dict[id]["percent"]/10))**credit_dict[id]["term"])) / (12 * credit_dict[id]["term"])

        else:
            accounts[id]["credit_status"] = "none"
    
    if accounts[id]["credit_status"] == "on":
        if accounts[id]["current_mounth"] == 0:
            accounts[id]["credit_status"] = "off"
        else:
            accounts[id]["amount"] = accounts[id]["amount"] - accounts[id]["monthly_write_off"]
            accounts[0]["amount"] = accounts[0]["amount"] + accounts[id]["monthly_write_off"]
            accounts[id]["current_mounth"] = accounts[id]["current_mounth"] - 1

    if accounts[id]["amount"] < 0:
        print(f"Дорогой клиент, {id}, погасите ваш кредит. Сумма задолжености {accounts[id]['amount']}")
##################################################

# Функция депозита
##################################################
def deposit (id):
    if "deposit_status" not in accounts[id]:
        if deposit_dict[id]["sum"] > 0:
            accounts[id]["amount"] = accounts[id]["amount"] - deposit_dict[id]["sum"]
            accounts[0]["amount"] = accounts[0]["amount"] + deposit_dict[id]["sum"]
            accounts[id]["deposit_status"] = "on"
            accounts[id]["total_deposit_mounth"] = 12 * deposit_dict[id]["term"]
            accounts[id]["current_deposit_mounth"] = 12 * deposit_dict[id]["term"]
            accounts[id]["monthly_write_on"] = (deposit_dict[id]["sum"] * ((1 + (deposit_dict[id]["percent"]/10))**deposit_dict[id]["term"])) / (12 * deposit_dict[id]["term"])

        else:
            accounts[id]["deposit_status"] = "none"
    
    if accounts[id]["deposit_status"] == "on":
        if accounts[id]["current_deposit_mounth"] == 0:
            accounts[id]["deposit_status"] = "off"
        else:
            accounts[id]["amount"] = accounts[id]["amount"] + accounts[id]["monthly_write_on"]
            accounts[0]["amount"] = accounts[0]["amount"] - accounts[id]["monthly_write_on"]
            accounts[id]["current_deposit_mounth"] = accounts[id]["current_deposit_mounth"] - 1
# print (accounts)
# print (accounts.keys())
##################################################

# Запуск времени + запись в файл
##################################################
while True:
    for id in accounts.keys():
        if id == 0:
            continue
        credit(id)
        deposit(id)
    # открываем файл для записи
    with open('account.csv', 'w', newline='') as csvfile:
    
        # определяем названия столбцов
        fieldnames = ['id', 'amount']
        
        # создаем writer объект
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        
        # записываем хедер
        writer.writeheader()
        
        # записываем значения из словаря
        for id, account in accounts.items():
            writer.writerow({'id': id, 'amount': account['amount']})
    print("Месяц")
    time.sleep(4)
##################################################

