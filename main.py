from abc import abstractmethod, ABC
from account_clients import (
    AccountClient,
)  # Импорт библиотек @ggramal для 19 домашней работы
import yaml
from flask import Flask, make_response, request
from threading import Thread
import time


class BankProduct:  # Создание класса BankProduct
    def __init__(self, client_id, percent, term, a_sum):
        self.__client_id = client_id
        self.__percent = percent
        self.__term = term
        self.__a_sum = a_sum
        self.__end_sum = float(
            "{:.2f}".format(self.__a_sum * ((1 + self.__percent / 100) ** self.__term))
        )

    def client_id(self):
        return self.__client_id

    def percent(self):
        return self.__percent

    def term(self):
        return self.__term

    def a_sum(self):
        return self.__a_sum

    def end_sum(self):
        return self.__end_sum

    @abstractmethod
    def process(self):
        pass


class Credit(BankProduct, ABC):  # Создание класса Credit, наследник BankProduct
    def __init__(self, client_id, percent, term, a_sum):
        BankProduct.__init__(self, client_id, percent, term, a_sum)
        acc_cl = AccountClient(self.client_id())
        acc_cl.transaction(add=self.a_sum())
        self.__periods = self.term() * 12
        self.__closed = False

    def periods(self):
        return self.__periods

    def closed(self):
        return self.__closed

    def monthly_fee(self):
        return float("{:.2f}".format(self.end_sum() / (self.term() * 12)))

    def show_c(self):
        return {
            "client_id": self.client_id(),
            "percent": self.percent(),
            "term": self.term(),
            "sum": self.a_sum(),
            "end_sum": self.end_sum(),
            "monthly_fee": self.monthly_fee(),
            "closed": self.closed(),
        }

    def filed(self):
        return {
            "client_id": self.client_id(),
            "percent": self.percent(),
            "term": self.term(),
            "sum": self.a_sum(),
            "credit": 1,
            "deposit": 0,
        }

    def process(self):  # Реализация метода process
        if not self.closed():
            self.__periods = self.__periods - 1  # Уменьшение periods на 1
            if self.__periods == 0:  # Если periods == 0 то closed = True
                self.__closed = True
            else:
                cl_credit = AccountClient(self.client_id())
                cl_credit.transaction(self.monthly_fee(), 0)


class Deposit(BankProduct, ABC):  # Создать класс Deposit, наследник BankProduct
    def __init__(self, client_id, percent, term, a_sum):
        BankProduct.__init__(self, client_id, percent, term, a_sum)
        acc_cl = AccountClient(self.client_id())
        acc_cl.withdraw = False
        self.__periods = self.term() * 12
        self.__closed = False

    def periods(self):
        return self.__periods

    def closed(self):
        return self.__closed

    def monthly_fee(self):
        return float(
            "{:.2f}".format((self.end_sum() - self.a_sum()) / (self.term() * 12))
        )

    def show_d(self):
        return {
            "client_id": self.client_id(),
            "percent": self.percent(),
            "term": self.term(),
            "sum": self.a_sum(),
            "end_sum": self.end_sum(),
            "monthly_fee": self.monthly_fee(),
            "closed": self.closed(),
            "credit": 0,
            "deposit": 1,
        }

    def filed(self):
        return {
            "client_id": self.client_id(),
            "percent": self.percent(),
            "term": self.term(),
            "sum": self.a_sum(),
        }

    def process(self):  # Реализация метода process аналогична process Credit
        if not self.closed():
            self.__periods = self.__periods - 1
            if self.__periods == 0:
                self.__closed = True
            else:
                cl_deposit = AccountClient(self.client_id())
                cl_deposit.transaction(substract=0, add=self.monthly_fee())


def data_read():
    with open("./data/credits_deposits.yaml", "r") as open_db:
        read_db = open_db.read()
        db_ds = yaml.load(
            read_db, Loader=yaml.FullLoader
        )  # Из базы данных credits_deposits.yaml получаем данные
    db_dc = sorted(
        db_ds["credit"], key=lambda dictionary_c: dictionary_c["client_id"]
    )  # Словарь клиентов кредита
    db_dd = sorted(
        db_ds["deposit"], key=lambda dictionary_c: dictionary_c["client_id"]
    )  # Словарь клиентов депозита
    bank_clients = []  # На их основании создаём объекты Кредитов и депозитов
    for credit_client in db_dc:
        credit = Credit(
            client_id=credit_client["client_id"],
            percent=credit_client["percent"],
            term=credit_client["term"],
            a_sum=credit_client["sum"],
        )
        bank_clients.append(credit)
    for deposit_client in db_dd:
        deposit = Deposit(
            client_id=deposit_client["client_id"],
            percent=deposit_client["percent"],
            term=deposit_client["term"],
            a_sum=deposit_client["sum"],
        )
        bank_clients.append(deposit)
    check = []
    for a in db_dd:
        check.append(a["client_id"])
    for b in db_dc:
        check.append(b["client_id"])
    return [db_dc, db_dd, bank_clients, check]


def update_file(db_dc, db_dd):
    to_yaml = {"credit": db_dc, "deposit": db_dd}
    with open("./data/credits_deposits.yaml", "w") as f:
        yaml.dump(to_yaml, f)


"""Some flask"""
app = Flask(__name__)


@app.route("/api/v1/credits/<int:client_id>", methods=["GET"])
def f_credits_id(client_id):
    response = make_response(
        {
            "status": "error",
            "message": f"Client {client_id} does not have active credits",
        }
    )
    for accounts in bank_clients:
        if isinstance(accounts, Credit):
            if accounts.client_id() == client_id:
                return accounts.show_c()
    response.status = 404
    return response


@app.route("/api/v1/deposits/<int:client_id>", methods=["GET"])
def f_deposits_id(client_id):
    response = make_response(
        {
            "status": "error",
            "message": f"Client {client_id} does not have active deposits",
        }
    )
    for accounts in bank_clients:
        if isinstance(accounts, Deposit):
            if accounts.client_id() == client_id:
                return accounts.show_d()
    response.status = 404
    return response


@app.route("/api/v1/deposits", methods=["GET"])
def f_deposits():
    show = []
    for accounts in bank_clients:
        if isinstance(accounts, Deposit):
            show.append(accounts.show_d())
    x = "\n".join(map(str, show)) + "\n"
    return x


@app.route("/api/v1/credits", methods=["PUT"])
def create_account_c():
    account = request.json
    op_account = account
    response = make_response(
        {
            "status": "error",
            "message": f"Credit for client {account['client_id']} already exists",
        }
    )
    response.status = 400
    if account["client_id"] not in check:
        check.append(account["client_id"])
        op_account = Credit(**account)
        db_dc.append(op_account.filed())
        bank_clients.append(op_account)
        update_file(db_dc, db_dd)
        db_dc.append(op_account.filed())
        with open("./data/credits_deposits.yaml", "w") as f:
            yaml.dump(op_account.filed(), f)
        update_file(db_dc, db_dd)
        response = make_response(
            {"status": "ok", "message": f"Account for {account['client_id']} created"}
        )
        response.status = 201
    return response


@app.route("/api/v1/deposits", methods=["PUT"])
def create_account_d():
    account = request.json
    op_account = account
    response = make_response(
        {
            "status": "error",
            "message": f"Deposit for client {account['client_id']} already exists",
        }
    )
    response.status = 400
    if account["client_id"] not in check:
        check.append(account["client_id"])
        op_account = Deposit(**account)
        db_dd.append(op_account.filed())
        bank_clients.append(op_account)
        update_file(db_dc, db_dd)
        with open("./data/credits_deposits.yaml", "w") as f:
            yaml.dump(op_account.filed(), f)
        response = make_response(
            {"status": "ok", "message": f"Account for {account['client_id']} created"}
        )
        response.status = 201
    return response


@app.route("/api/v1/credits", methods=["GET"])
def f_credits():
    show = []
    for accounts in bank_clients:
        if isinstance(accounts, Credit):
            show.append(accounts.show_c())
    x = "\n".join(map(str, show)) + "\n"
    return x


@app.route("/api/v1/bank/health_check", methods=["GET"])
def health_check():
    response = make_response({"status": "ok", "message": "Service Bank is available"})
    response.status = 200
    return response


def start_f():
    while True:
        time.sleep(1)  # МЕСЯЦ = 1 секунда
        for (
                clients
        ) in bank_clients:  # Каждый месяц вызываем у этих объектов метод process
            clients.process()
            if clients.closed():  # Если кредит, депозит закрыт
                if isinstance(clients, Credit):
                    for c in db_dc:
                        if c["client_id"] == clients.client_id():
                            bank_clients.remove(clients)
                            check.remove(c["client_id"])
                            db_dc.remove(c)  # удаляем его из списка
                            for i in range(len(db_dc)):
                                if c["client_id"] in db_dc[i].values():
                                    del db_dc[i]
                                    break
                            update_file(db_dc, db_dd)
                            print(
                                "Client "
                                + str(clients.client_id())
                                + " close his credit"
                            )
                elif isinstance(clients, Deposit):
                    for d in db_dd:
                        if d["client_id"] == clients.client_id():
                            bank_clients.remove(clients)
                            check.remove(d["client_id"])
                            db_dd.remove(d)
                            update_file(db_dc, db_dd)
                            print(
                                "Client "
                                + str(clients.client_id())
                                + " close his deposit"
                            )


db_dc, db_dd, bank_clients, check = data_read()
start = Thread(target=start_f)
start.start()
if __name__ == "__main__":
    app.run(debug=False, host="0.0.0.0")
# curl -X PUT -H "Content-type: application/json" -d '{"client_id": 15, "percent": 10,
# "a_sum": 1000, "term": 1}' localhost:5000/api/v1/credits