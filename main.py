import abc
import json
import yaml
import config
import threading
from account_clients import AccountClient
from datetime import datetime, date
from flask import Flask, request, jsonify, make_response
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.exc import IntegrityError
from psycopg2.errors import NotNullViolation, UniqueViolation


app = Flask(__name__)

app.config[
    "SQLALCHEMY_DATABASE_URI"
] = f"postgresql://{config.PG_USER}:{config.PG_PASSWORD}@{config.PG_HOST}:{config.PG_PORT}/{config.PG_DATABASE}"
db = SQLAlchemy(app)


class BankProduct(db.Model):
    __abstract__ = True

    client_id = db.mapped_column(db.Integer)
    percent = db.mapped_column(db.Double)
    sum = db.mapped_column(db.Double)
    term = db.mapped_column(db.Integer)
    periods = db.mapped_column(db.Integer)
    closed = db.mapped_column(db.Boolean, default=False)

    def __init__(self, **kwargs):
        if "closed" in kwargs:
            raise ValueError("closed attribute should not set")
        if kwargs["sum"] < 0:
            raise ValueError("sum must be more than 0")
        if kwargs["percent"] < 0:
            raise ValueError("percent must be more than 0")
        if kwargs["term"] < 0:
            raise ValueError("term must be more than 0")
        if "client_id" not in kwargs:
            raise ValueError("client_id must be defined")
        kwargs["periods"] = (
            kwargs["periods"] if "periods" in kwargs else (kwargs["term"] * 12)
        )
        for cls_field, cls_field_value in kwargs.items():
            setattr(self, cls_field, cls_field_value)

    @property
    def total_periods(self):
        return self.term * 12

    @property
    def end_sum(self):
        return self.sum * (1 + self.percent / 100) ** self.term

    @property
    def monthly_fee(self):
        return self.end_sum / self.total_periods

    def to_dict(self):
        return {
            "client_id": self.client_id,
            "percent": self.percent,
            "sum": self.sum,
            "term": self.term,
            "periods": self.periods,
        }

    def __eq__(self, other):
        if isinstance(other, BankProduct):
            return (
                self.client_id == other.client_id
                and self.percent == other.percent
                and self.sum == other.sum
                and self.term == other.term
            )

        return NotImplemented

    def __hash__(self):
        return hash((self.client_id, self.percent, self.sum, self.term))


class Credit(BankProduct):
    __tablename__ = "credits"
    credit_id = db.mapped_column(db.Integer, primary_key=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        client = AccountClient(self.client_id)
        bank = AccountClient(0)
        if self.periods == self.total_periods:
            client.transaction(add=self.sum)
            bank.transaction(substract=self.sum)

    def process(self):
        if not self.closed:
            client = AccountClient(self.client_id)
            bank = AccountClient(0)
            client.transaction(substract=self.monthly_fee)
            bank.transaction(add=self.monthly_fee)

            self.periods -= 1
            if self.periods == 0:
                self.closed = True


class Deposit(BankProduct):
    __tablename__ = "deposits"
    deposit_id = db.mapped_column(db.Integer, primary_key=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        client = AccountClient(self.client_id)
        bank = AccountClient(0)
        if self.periods == self.total_periods:
            client.transaction(substract=self.sum)
            bank.transaction(add=self.sum)

    def process(self):
        if not self.closed:
            client = AccountClient(self.client_id)
            bank = AccountClient(0)

            client.transaction(add=self.monthly_fee)
            bank.transaction(substract=self.monthly_fee)

            self.periods -= 1
            if self.periods == 0:
                self.closed = True


@app.route("/api/v1/credits/<int:client_id>", methods=["GET"])
def get_credits(client_id):
    credits = (
        db.session.query(Credit).filter_by(client_id=client_id, closed=False).all()
    )
    if len(credits) == 0:
        error_massage = f"client {client_id} does not have active credits"
        return jsonify({"status": "error", "message": error_massage}), 404
    else:
        return jsonify(credits[0].to_dict())


@app.route("/api/v1/deposits/<int:client_id>", methods=["GET"])
def get_deposit(client_id):
    deposits = (
        db.session.query(Deposit).filter_by(client_id=client_id, closed=False).all()
    )
    if len(deposits) == 0:
        error_message = f"Client {client_id} does not have active deposits"
        return jsonify({"status": "error", "message": error_message}), 404
    else:
        return jsonify(deposits[0].to_dict())


@app.route("/api/v1/deposits", methods=["GET"])
def get_all_deposits():
    deposits = db.session.query(Deposit).filter_by(closed=False).all()
    deposits = [d.to_dict() for d in deposits]
    return jsonify(deposits)


@app.route("/api/v1/credits", methods=["GET"])
def get_all_credits():
    credits = db.session.query(Credit).filter_by(closed=False).all()
    credits = [c.to_dict() for c in credits]
    return jsonify(credits)


@app.route("/api/v1/credits", methods=["PUT"])
def create_credit():
    try:
        data = request.get_json()

        credit = Credit(**data)

        credits = (
            db.session.query(Credit)
            .filter_by(client_id=credit.client_id, closed=False)
            .all()
        )
        if credits:
            return make_response(
                jsonify(
                    {
                        "status": "error",
                        "message": f"Client {credit.client_id} already has an open credit",
                    }
                ),
                400,
            )
        db.session.add(credit)
        db.session.commit()
        return (
            jsonify(
                {
                    "status": "ok",
                    "message": f"Credit added for client {credit.client_id}",
                }
            ),
            201,
        )
    except KeyError as e:
        return jsonify({"status": "error", "message": str(e)}), 400
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/v1/deposits", methods=["PUT"])
def create_deposit():
    try:
        data = request.get_json()

        deposit = Deposit(**data)

        deposits = (
            db.session.query(Deposit)
            .filter_by(client_id=deposit.client_id, closed=False)
            .all()
        )
        if deposits:
            return make_response(
                jsonify(
                    {
                        "status": "error",
                        "message": f"Client {deposit.client_id} already has an open deposit",
                    }
                ),
                400,
            )
        db.session.add(deposit)
        db.session.commit()
        return (
            jsonify(
                {
                    "status": "ok",
                    "message": f"Deposit added for client {deposit.client_id}",
                }
            ),
            201,
        )
    except KeyError as e:
        return (
            jsonify({"status": "error", "message": f"Missing attribute {str(e)}"}),
            400,
        )
    except ValueError as e:
        return jsonify({"status": "error", "message": str(e)}), 400


@app.route("/api/v1/bank/health_check", methods=["GET"])
def health_check():
    return jsonify({"status": "OK"}), 200


def process_credits_and_deposits():
    import time

    while True:
        with app.app_context():
            credits = db.session.query(Credit).filter_by(closed=False).all()
            deposits = db.session.query(Deposit).filter_by(closed=False).all()

            for credit in credits:
                credit.process()
            for deposit in deposits:
                deposit.process()

            db.session.add_all(deposits)
            db.session.add_all(credits)
            db.session.commit()
        time.sleep(10)


def seed_data():
    credits = db.session.query(Credit).all()
    deposits = db.session.query(Deposit).all()

    with open("data/credits_deposits.yaml", "r") as f:
        product_data = yaml.safe_load(f)
        credits_data = product_data["credits"]
        for credit in credits_data:
            credit = Credit(**credit)
            if credit not in credits:
                db.session.add(credit)
                db.session.commit()

        deposits_data = product_data["deposits"]
        for deposit in deposits_data:
            deposit = Deposit(**deposit)
            if deposit not in deposits:
                db.session.add(deposit)
                db.session.commit()


with app.app_context():
    db.create_all()
    seed_data()

credit_deposit_thread = threading.Thread(target=process_credits_and_deposits)
credit_deposit_thread.start()


if __name__ == "__main__":
    app.run(host="0.0.0.0")
