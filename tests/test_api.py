from eth_account import Account
import pytest
import trio

from pons import *


async def test_payment(test_provider):

    client = Client(provider=test_provider)

    root_account = test_provider.root_account
    root_signer = AccountSigner(root_account)

    acc1 = Account.create()

    root_address = Address.from_hex(root_account.address)
    acc1_address = Address.from_hex(acc1.address)

    # Fund the deployer account
    async with client.session() as session:
        root_balance = await session.get_balance(root_address)
        to_transfer = Amount.ether(10)
        await session.transfer(root_signer, acc1_address, to_transfer)
        # TODO: check that block has changed
        root_balance_after = await session.get_balance(root_address)
        acc1_balance_after = await session.get_balance(acc1_address)
        assert acc1_balance_after == to_transfer
        assert root_balance - root_balance_after > to_transfer


async def test_contract(test_provider, compiled_contracts):

    compiled_contract = compiled_contracts["Test"]

    client = Client(provider=test_provider)

    root_account = test_provider.root_account
    root_signer = AccountSigner(root_account)

    acc1 = Account.create()
    acc1_signer = AccountSigner(acc1)

    root_address = Address.from_hex(root_account.address)
    acc1_address = Address.from_hex(acc1.address)

    async with client.session() as session:

        # Fund the deployer account

        root_balance = await session.get_balance(root_address)
        to_transfer = Amount.ether(10)
        await session.transfer(root_signer, acc1_address, to_transfer)
        # TODO: check that block has changed
        root_balance_after = await session.get_balance(root_address)
        acc1_balance_after = await session.get_balance(acc1_address)
        assert acc1_balance_after == to_transfer
        assert root_balance - root_balance_after > to_transfer

        # Deploy the contract

        call = compiled_contract.constructor(12345, 56789)
        deployed_contract = await session.deploy(acc1_signer, call)

        # Transact with the contract
        call = deployed_contract.write.setState(111)
        await session.transact(acc1_signer, call)

        # Call the contract

        call = deployed_contract.read.getState(123)
        result = await session.call(call)

    assert result == [111 + 123]
