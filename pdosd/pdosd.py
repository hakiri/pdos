import argparse
import concurrent.futures
import grpc
import proto.pdosd_pb2_grpc as pdosd_grpc
import time

from solidity.primitives import ORContractsInterface

from pdosd.listener import Listener
from pdosd.trigger import Trigger
from pdosd.servicer import Servicer

from utils.log import log

# to open wallet files
from eth_account import Account
import getpass


def main():
    # NB: checksummed addresses
    REF_ADDRESS = "0x5aF932dD7c4da229f89e820bfab3dEa36Dce4103"

    parser = argparse.ArgumentParser(description="pDoS daemon")

    parser.add_argument(
        '--eth_rpc',
        type=str,
        default="http://127.0.0.1:8545",
        help="web3 rpc address to use [default: http://127.0.0.1:8545]",
    )
    parser.add_argument(
        '--eth_account',
        type=str,
        default="coinbase",
        help="ETH (checksummed) address to use (see README) [default: coinbase]",
    )
    parser.add_argument(
        '--eth_privkey',
        type=str,
        default=None,
        help="ETH private key to use to sign transaction inside this script [default: empty]",
    )
    parser.add_argument(
        '--eth_wallet',
        type=str,
        default=None,
        help="path to ETH wallet file (instead of suppling eth_account and eth_privkey) [default: empty]",
    )
    parser.add_argument(
        '--gasprice',
        type=int,
        default=21000000000,
        help="ETH private key to use to sign transaction inside this script in wei [default: 21 Gwei]",
    )
    parser.add_argument(
        '--port',
        type=str,
        default="7331",
        help="port to listen to [default: 7331]",
    )
    parser.add_argument(
        '--deploy',
        default=False,
        action='store_true',
        help="deploy new R contract. Only for dev purposes (see README) [default: False]",
    )
    parser.add_argument(
        '--reference',
        type=str,
        default="",
        help="override reference contract address (dev/testing purposes)",
    )
    parser.add_argument(
        '--networktype',
        type=str,
        default="PoW",
        choices=["PoW", "PoA"],
        help="Network type (PoW/PoA) [default: PoW]",
    )

    args = parser.parse_args()

    if args.deploy:
        if args.reference != "":
            log("Can't have --deploy and --reference", "error")
            return
        # deploy mode will deploy a new reference contract (R).
        REF_ADDRESS = None
    else:
        if args.reference != "":
            REF_ADDRESS = args.reference

    account = args.eth_account
    privatekey = args.eth_privkey

    if args.eth_wallet != None:
        if args.eth_privkey != None or args.eth_account != "coinbase":
            log("You don't need to specify --eth_privkey nor --eth_account if you use --eth_wallet", "error")
            return

        try:
            with open(args.eth_wallet) as keyfile:
                passwd = getpass.getpass('Wallet file password:')
                encrypted_key = keyfile.read()
                clear = Account.decrypt(encrypted_key, passwd)
        except Exception as e:
            log("Decrypt failed.", "error")
            print (e)
            return

        wallet = Account.privateKeyToAccount(clear)
        account = wallet.address
        privatekey = wallet.privateKey

    OR_iface = ORContractsInterface(
        REF_ADDRESS,
        RPC_INSTANCE=args.eth_rpc,
        account=account,
        privatekey=privatekey,
        PoA=(args.networktype == "PoA"),
        gasprice=args.gasprice,
    )

    if REF_ADDRESS != None:
        log("Reference contract address is {}.".format(OR_iface.HARCODED_R_ADDRESS), "success")
    server = grpc.server(
        concurrent.futures.ThreadPoolExecutor(max_workers=10)
    )

    pdosd_grpc.add_PDOSDServicer_to_server(Servicer(OR_iface), server)

    trigger = Trigger()
    listener = Listener(OR_iface, trigger)

    log("Starting GRPC server on port {}.".format(args.port), "success")
    server.add_insecure_port("[::]:{}".format(args.port))
    server.start()

    try:
        while True:
            listener.loop()
            trigger.loop()
            time.sleep(5)
    except KeyboardInterrupt:
        server.stop(0)
