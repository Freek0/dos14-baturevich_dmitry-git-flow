import csv
import json
from abc import ABC, abstractmethod
import time
import yaml
from account_clients import AccountClient
from flask import Flask, make_response, request, jsonify
import threading

app = Flask(__name__)

class BankProduct(ABC):
    def __init__(self, client_id, percent, term, sum):
        self._client_id = client_id
        self._percent = percent
        self._term = term
        self._sum = sum

    @property
    def client_id(self):
        return self._client_id

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
        return self._sum * (1 + self._percent / 100) ** self._term

    @abstractmethod
    def process(self):
        pass


class Credit(BankProduct):
    def __init__(self, client_id, percent, term, sum, periods=-1):
        super().__init__(client_id, percent, term, sum)
        self.__closed = False
        self.__monthly_fee = self.end_sum / (term * 12)
        
        client_acc = AccountClient(self.client_id)
        bank_acc = AccountClient(0)
        if periods == -1:
            self.__periods = self.term * 12
        else:
            self.__periods = periods

        if self.sum > 0:
            client_acc.transaction(add = self.sum)
            bank_acc.transaction(substract = self.sum)


    @property
    def periods(self):
        return self.__periods
    
    @periods.setter
    def periods(self, value):
        self.__periods = value

    @property
    def closed(self):
        return self.__closed

    @property
    def monthly_fee(self):
        return self.__monthly_fee

    def process(self):
        if not self.closed:
            client_acc = AccountClient(self.client_id)
            bank_acc = AccountClient(0)
            client_acc.transaction(substract=self.monthly_fee)
            bank_acc.transaction(add=self.monthly_fee)

            self.__periods -= 1
            if self.__periods == 0:
                self.__closed = True



class Deposit(BankProduct):
    def __init__(self, client_id, percent, term, sum, periods=-1):
        super().__init__(client_id, percent, term, sum)
        self.__closed = False
        self.__monthly_fee = self.end_sum / (term * 12)
        
        client_acc = AccountClient(self.client_id)
        bank_acc = AccountClient(0)

        if periods == -1:
            self.__periods = self.term * 12
        else:
            self.__periods = periods

        if self.sum > 0:
            client_acc.transaction(substract = self.sum)
            bank_acc.transaction(add = self.sum)


    @property
    def periods(self):
        return self.__periods

    @periods.setter
    def periods(self, value):
        self.__periods = value

    @property
    def monthly_fee(self):
        return self.__monthly_fee

    @property
    def closed(self):
        return self.__closed

    def process(self):
        if not self.closed:
            client_acc = AccountClient(self.client_id)
            bank_acc = AccountClient(0)
            client_acc.transaction(add=self.monthly_fee)
            bank_acc.transaction(substract=self.monthly_fee)

            self.__periods -= 1
            if self.__periods == 0:
                self.__closed = True

def process_credits_deposits():

    # Основной цикл
    while True:
        with open("credits_deposits.yaml", "r") as f:

            data = yaml.load(f, Loader=yaml.FullLoader)

        # Создаем список объектов Credit и Deposit
        products_bank = []
        for credit_data in data['credit']:
            credit = Credit(
                client_id=credit_data['client_id'],
                percent=credit_data['percent'],
                term=credit_data['term'],
                sum=credit_data['sum'],
                periods=credit_data['periods']
            )
            products_bank.append(credit)
        for deposit_data in data['deposit']:
            deposit = Deposit(
                client_id=deposit_data['client_id'],
                percent=deposit_data['percent'],
                term=deposit_data['term'],
                sum=deposit_data['sum'],
                periods=deposit_data['periods']

            )
            products_bank.append(deposit)
        for product in products_bank:
            product.process()
            if product.closed:
                products_bank.remove(product)


        with open("credits_deposits.yaml", "w") as f:
            yaml.dump({
                'credit': [{
                    'client_id': p.client_id, 
                    'percent': p.percent, 
                    'sum': p.sum, 
                    'term': p.term, 
                    'periods': p.periods
                    } 
                    for p in products_bank if isinstance(p, Credit)],

                'deposit': [{
                    'client_id': p.client_id,
                    'percent': p.percent, 
                    'sum': p.sum, 
                    'term': p.term, 
                    'periods': p.periods
                    } 
                    for p in products_bank if isinstance(p, Deposit)]
            }, f)



        time.sleep(10)


credit_deposit_thread = threading.Thread(target=process_credits_deposits)
credit_deposit_thread.start()


###
# получить данные о кредите клиента
@app.route("/api/v1/credits/<int:client_id>", methods=["GET"])
def get_credits(client_id):
    with open("credits_deposits.yaml", "r") as f:
        data = yaml.load(f, Loader=yaml.FullLoader)

    credits = [credit for credit in data.get("credit", [])]
    credits_client = [
        credit for credit in credits if credit["client_id"] == client_id
    ]
    try:
        response = make_response(jsonify(credits_client[0]))
    except IndexError:
        error_massage = f"client {client_id} does not have active credits"
        response = make_response(jsonify({"status": "error", "message": error_massage}))
        response.status = 404
    
    return response

# получить данные о депозите клиента
@app.route("/api/v1/deposits/<int:client_id>", methods=["GET"])
def get_deposit(client_id):
    with open("credits_deposits.yaml", "r") as f:
        data = yaml.load(f, Loader=yaml.FullLoader)

    deposits = [credit for credit in data.get("deposit", [])]
    deposit_client = [
        deposit for deposit in deposits if deposit["client_id"] == client_id
    ]
    try:
        response = make_response(jsonify(deposit_client[0]))
    except IndexError:
        error_massage = f"client {client_id} does not have active deposits"
        response = make_response(jsonify({"status": "error", "message": error_massage}))
        response.status = 404
    
    return response
# получить данные о всех депозитах
@app.route("/api/v1/deposits/all", methods=["GET"])
def get_all_deposits():
    with open("credits_deposits.yaml", "r") as f:
        data = yaml.load(f, Loader=yaml.FullLoader)
    deposits = [deposit for deposit in data.get("deposit", [])]
    return jsonify(deposits)


# получить данные о всех кредитах
@app.route("/api/v1/credits/all", methods=["GET"])
def get_all_credits():
    with open("credits_deposits.yaml", "r") as f:
        data = yaml.load(f, Loader=yaml.FullLoader)

    credits = [credit for credit in data.get("credit", [])]
    return jsonify(credits)

# Создаем новый кредит с проверкой на существование до этого и пишем в файл
@app.route("/api/v1/credits", methods=["POST"])
def create_credit():

    client_request = request.json
    client_id = client_request["client_id"]
    percent = client_request["percent"]
    sum = client_request["sum"]
    term = client_request["term"]
    periods = term*12

    with open("credits_deposits.yaml", "r") as f:
        file_data = yaml.safe_load(f)
    credits = file_data["credit"]

    # Проверяем, существует ли уже кредит для данного клиента
    for credit in credits:
        if credit["client_id"] == client_id:
            return make_response(jsonify(
                    {
                        "status": "error",
                        "message": f"Credit for client {client_id} already exists",
                    }
                    ),
                400,
            )

    # Добавляем новый кредит в список credits
    new_credit = {
        "client_id": client_id,
        "percent": percent,
        "sum": sum,
        "term": term,
        "periods": periods,
    }
    credits.append(new_credit)
    file_data["credit"] = credits
    with open("credits_deposits.yaml", "w") as f:
        yaml.dump(file_data, f)

    return (
        jsonify({"status": "ok", "message": f"Credit added for client {client_id}"}),
        201,
    )

# Создаем новый депозит с проверкой на существование до этого и пишем в файл
@app.route("/api/v1/deposits", methods=["POST"])
def create_deposit():

    client_request = request.json
    client_id = client_request["client_id"]
    percent = client_request["percent"]
    sum = client_request["sum"]
    term = client_request["term"]
    periods = term*12

    with open("credits_deposits.yaml", "r") as f:
        file_data = yaml.safe_load(f)
    deposits = file_data["deposit"]

    
    for deposit in deposits:
        if deposit["client_id"] == client_id:
            return make_response(jsonify(
                    {
                        "status": "error",
                        "message": f"Deposit for client {client_id} already exists",
                    }
                    ),
                400,
            )

    
    new_deposit = {
        "client_id": client_id,
        "percent": percent,
        "sum": sum,
        "term": term,
        "periods": periods,
    }
    deposits.append(new_deposit)
    file_data["deposit"] = deposits
    with open("credits_deposits.yaml", "w") as f:
        yaml.dump(file_data, f)

    return (
        jsonify({"status": "ok", "message": f"Deposit added for client {client_id}"}),
        201,
    )
####

if __name__ == "__main__":
    app.run()