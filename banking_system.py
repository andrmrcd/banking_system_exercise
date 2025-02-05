from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Dict
from uuid import UUID, uuid4


@dataclass
class Account:
    customer_id: UUID
    account_number: str
    balance: Decimal = Decimal("0")
    account_id: UUID = field(default_factory=uuid4)

    def __post_init__(self):
        if not self.account_number.isdigit() or len(self.account_number) != 10:
            raise ValueError("Account number must be 10 digits")

    def deposit(self, amount: Decimal):
        if amount < 0:
            raise ValueError("Deposit amount must be greater than 0")
        self.balance += amount

    def withdraw(self, amount: Decimal):
        if amount <= 0:
            raise ValueError("Withdraw amount must be greater than 0")
        if amount > self.balance:
            raise ValueError("Insufficient balance")
        self.balance -= amount

    def get_balance(self) -> str:
        return str(self.balance)


@dataclass
class Customer:
    name: str
    email: str
    phone_number: str
    customer_id: UUID = field(default_factory=uuid4)

    def __post_init__(self):
        if not self.phone_number.isdigit() or len(self.phone_number) != 12:
            raise ValueError(
                "Invalid phone number. Please input phone number starting with '63' PH code"
            )

        if "@" not in self.email:
            raise ValueError("Invalid email")


class TransactionType(Enum):
    DEPOSIT = "DEPOSIT"
    WITHDRAW = "WITHDRAW"


@dataclass
class TransactionRecord:
    account_id: UUID
    amount: Decimal
    type: TransactionType
    transaction_timestamp: datetime = field(default_factory=datetime.now)
    transaction_id: UUID = field(default_factory=uuid4)

    def __repr__(self):
        return f"DATE: {self.transaction_timestamp} ------ TYPE: {self.type.value} ------- AMOUNT: P{self.amount:.2f}"


class AccountRepository:
    def __init__(self):
        self.accounts: Dict[UUID, Account] = {}
        self.customer_accounts: Dict[UUID, list[Account]] = {}
        self.current_account_number = 0

    def save_account(self, account: Account):
        if account.account_id in self.accounts:
            raise ValueError("Account already exists")
        self.accounts[account.account_id] = account
        if account.customer_id not in self.customer_accounts:
            self.customer_accounts[account.customer_id] = []
        self.customer_accounts[account.customer_id].append(account)

    def generate_account_number(self) -> str:
        self.current_account_number += 1
        account_number = f"{self.current_account_number:010d}"
        return account_number

    def find_account_by_id(self, account_id: UUID) -> Account:
        return self.accounts[account_id]

    def find_accounts_by_customer_id(self, customer_id: UUID) -> list[Account]:
        return self.customer_accounts.get(customer_id, [])


class TransactionRepository:
    def __init__(self):
        self.transactions: Dict[UUID, list[TransactionRecord]] = {}

    def get_transactions(self, account_id: UUID) -> list[TransactionRecord]:
        if account_id not in self.transactions:
            raise ValueError("Account has not made transactions")
        return self.transactions[account_id]

    def store_transaction(self, transaction_record: TransactionRecord):
        account_id = transaction_record.account_id
        if account_id not in self.transactions:
            self.transactions[account_id] = []
        self.transactions[account_id].append(transaction_record)


class AccountService:
    def __init__(self, account_repository: AccountRepository):
        self.account_repository = account_repository

    def create_account(self, input_customer: Customer) -> Account:
        account_number = self.account_repository.generate_account_number()

        new_account = Account(
            customer_id=input_customer.customer_id,
            account_number=account_number,
        )

        self.account_repository.save_account(new_account)

        return new_account


class TransactionService:
    def __init__(
        self,
        account_repository: AccountRepository,
        transaction_repository: TransactionRepository,
    ):
        self.account_repository = account_repository
        self.transaction_repository = transaction_repository

    @staticmethod
    def _create_transaction_record(
        account_id: UUID, amount: Decimal, type: TransactionType
    ) -> TransactionRecord:
        return TransactionRecord(account_id, amount, type)

    def _process_transaction(
        self, account_id, amount: Decimal, transaction_type: TransactionType
    ) -> TransactionRecord:
        if amount < 0:
            raise ValueError("Amount should be positive value")
        account: Account = self.account_repository.find_account_by_id(account_id)
        if transaction_type == TransactionType.DEPOSIT:
            account.deposit(amount)
        if transaction_type == TransactionType.WITHDRAW:
            account.withdraw(amount)

        return self._create_transaction_record(account_id, amount, transaction_type)

    def make_transaction(
        self, account_id: UUID, amount: Decimal, transaction_type: TransactionType
    ):
        transaction_record: TransactionRecord = self._process_transaction(
            account_id, amount, transaction_type
        )
        self.transaction_repository.store_transaction(transaction_record)


class AccountStatement:
    def __init__(self, transaction_repository: TransactionRepository):
        self.transaction_repository = transaction_repository

    def generate_account_statement(self, account_id: UUID) -> str:
        transactions = self.transaction_repository.get_transactions(account_id)

        return "\n".join(str(transaction) for transaction in transactions)


def main():
    new_customer1 = Customer(
        name="Andrei Mercado",
        email="AndreiMercado@email.com",
        phone_number="639213423123",
    )
    new_customer2 = Customer(
        name="John Mercado", email="JohnMercado@gmail.com", phone_number="639123456123"
    )

    print(f"New customer 1: {new_customer1}")
    print(f"New customer 2: {new_customer2}")

    account_repo = AccountRepository()
    transaction_repo = TransactionRepository()

    account_service = AccountService(account_repo)
    transaction_service = TransactionService(account_repo, transaction_repo)
    account_statement_service = AccountStatement(transaction_repo)

    new_account = account_service.create_account(new_customer1)
    print(f"New account created for customer {new_customer1.name}")

    find_account_test = account_repo.find_account_by_id(new_account.account_id)
    print(f"Account found: {find_account_test.account_number}")

    # scenario for customer with no account
    try:
        find_account_test = account_repo.find_accounts_by_customer_id(
            new_customer2.customer_id
        )
    except KeyError as e:
        print(f"Account Missing error: {e}")

    # scenario for already existing account
    try:
        account_service.create_account(new_customer1)
    except ValueError as e:
        print(f"Account error: {e}")
        pass

    # scenario for no transactions
    try:
        transaction_repo.get_transactions(new_account.account_id)
    except ValueError as e:
        print(f"Transaction error: {e}")
        pass

    # scenario for account deposit and withdraw transactions
    transaction_service.make_transaction(
        new_account.account_id, Decimal("5000.0"), TransactionType.DEPOSIT
    )
    print(f"Deposit successful. New balance: {new_account.get_balance()}")

    transaction_service.make_transaction(
        new_account.account_id, Decimal("500.00"), TransactionType.WITHDRAW
    )
    print(f"Withdraw succesful. New balance: {new_account.get_balance()}")

    # Generating account statement
    transaction_service.make_transaction(
        new_account.account_id, Decimal("250.00"), TransactionType.WITHDRAW
    )

    transaction_service.make_transaction(
        new_account.account_id, Decimal("200.00"), TransactionType.WITHDRAW
    )

    transactions = account_statement_service.generate_account_statement(
        new_account.account_id
    )
    print(f"Account statement for account number {new_account.account_number}")
    print(f"{transactions}")


if __name__ == "__main__":
    main()
