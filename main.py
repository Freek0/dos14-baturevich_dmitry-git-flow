import csv
import json
from abc import ABC, abstractmethod
import time

class BankProduct(ABC):
    def __init__(self, entity_id, percent, term, sum):
        self._entity_id = entity_id
        self._percent = percent
        self._term = term
        self._sum = sum
    
    @property
    def entity_id(self):
        return self._entity_id
    
    @property
    def percent(self):
        return self._percent
    
    @property
    def term(self):
        return self._term
    
    @property
    def sum(self):
        return self._sum
    
    @property
    def end_sum(self):
        return self._sum * (1 + self._percent/100)**self._term
    
    @abstractmethod
    def process(self):
        pass


class Credit(BankProduct):
    def __init__(self, entity_id, percent, term, sum):
        super().__init__(entity_id, percent, term, sum)
        self.__periods = term * 12
        self.__closed = False
        self.__monthly_fee = self.end_sum / (term * 12)
    
    @property
    def periods(self):
        return self.__periods
    
    @property
    def closed(self):
        return self.__closed
    
    @property
    def monthly_fee(self):
        return self.__monthly_fee
    
    def process(self, user_id):
        with open('transactions.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([user_id, self.monthly_fee, 'substract'])
            writer.writerow([0, self.monthly_fee, 'add'])
        self.__periods -= 1
        if self.__periods == 0:
            self.__closed = True


class Deposit(BankProduct):
    def __init__(self, entity_id, percent, term, sum):
        super().__init__(entity_id, percent, term, sum)
        self.__periods = term * 12
        self.__closed = False
        self.__monthly_fee = self.end_sum / (term * 12)
    
    @property
    def periods(self):
        return self.__periods
    
    @property
    def monthly_fee(self):
        return self.__monthly_fee
    
    @property
    def closed(self):
        return self.__closed
    
    def process(self, user_id):
        with open('transactions.csv', 'a', newline='') as f:
            writer = csv.writer(f)
            writer.writerow([user_id, self.monthly_fee, 'add'])
            writer.writerow([0, self.monthly_fee, 'substract'])
        self.__periods -= 1
        if self.__periods == 0:
            self.__closed = True 

    
# Открываем файл с данными
with open('credits_deposits.json', 'r') as f:
    data = json.load(f)

# Создаем список объектов Credit и Deposit
products_bank = []
for credit_data in data['credit']:
    credit = Credit(
        entity_id=credit_data['entity_id'],
        percent=credit_data['percent'],
        term=credit_data['term'],
        sum=credit_data['sum']
    )
    products_bank.append(credit)
for deposit_data in data['deposit']:
    deposit = Deposit(
        entity_id=deposit_data['entity_id'],
        percent=deposit_data['percent'],
        term=deposit_data['term'],
        sum=deposit_data['sum']
    )
    products_bank.append(deposit)

# Основной цикл
while True:
    for product in products_bank:
        product.process(user_id=product.entity_id)
        if product.closed:
            products_bank.remove(product)

    # Обновляем данные в файле credits_deposits.json
    with open('credits_deposits.json', 'w') as f:
        json.dump({
            'credit': [p.__dict__ for p in products_bank if isinstance(p, Credit)],
            'deposit': [p.__dict__ for p in products_bank if isinstance(p, Deposit)]
        }, f)

    time.sleep(1)  