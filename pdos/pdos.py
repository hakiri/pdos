import grpc
import sys
import time

import proto.pdosd_pb2 as pdosd_proto
import proto.pdosd_pb2_grpc as pdosd_grpc

from utils.colors import bcolors


class Command():
    def __init__(self, args, options):
        self._args = args
        self._options = options

    def validate(self):
        raise("Not implemented")

    def run(self, stub):
        raise("Not implemented")

    def print_operation(
            self,
            operation,
    ):
        if operation.epoch_stop > int(time.time()):
            if operation.decided and operation.joined:
                print("- {}{} -- joined & decided{}".format(
                    bcolors.RED, operation.address, bcolors.ENDC
                ))
            elif operation.joined:
                print("- {}{} -- joined{}".format(
                    bcolors.ORANGE, operation.address, bcolors.ENDC
                ))
            elif operation.decided:
                print("- {}{} ----------  decided{}".format(
                    bcolors.GREEN, operation.address, bcolors.ENDC
                ))
            else:
                print("- {}".format(operation.address))
            print("    target: {} [{}]".format(
                operation.target, operation.service,
            ))
            print("    users: {}/{} [{}]".format(
                operation.users,
                operation.threshold,
                operation.decided,
            ))
            print("    start: {}".format(
                time.strftime(
                    '%Y-%m-%d %H:%M:%S',
                    time.localtime(operation.epoch_start),
                ),
            ))
            print("    duration: {}s".format(
                operation.epoch_stop - operation.epoch_start
            ))
            if operation.info != "":
                print("    info: {}".format(operation.info))


class OperationList(Command):
    def __init__(self, args, options):
        super(OperationList, self).__init__(args, options)

    def validate(self):
        if len(self._args) > 0:
            print("[ERROR] `operation list` expects no argument.")
            return False
        return True

    def run(self, stub):
        for operation in stub.OperationList(pdosd_proto.Empty()):
            self.print_operation(operation)
        print("[DONE]")


class OperationPropose(Command):
    def __init__(self, args, options):
        super(OperationPropose, self).__init__(args, options)

    def validate(self):
        if len(self._args) != 4:
            print("[ERROR] `operation propose` expects 4 arguments: " +
                  "target, threshold, epoch_start, duration.")
            return False

        self._target = self._args[0]

        self._threshold = int(self._args[1])
        if self._threshold <= 0:
            print("[ERROR] `threshold` must be a positive integer" +
                  ", got: {}".format(self._threshold))
            return False

        self._service = 'www'
        if 'service' in self._options:
            self._service = self._options['service']
        if self._service != 'www':
            print("[ERROR] `service` not supported. Supported values: www.")
            return False

        self._epoch_start = int(self._args[2])
        if self._epoch_start <= int(time.time()):
            print("[ERROR] `epoch_start` must be in the future, " +
                  "current epoch: {}".format(int(time.time())))
            return False

        duration = int(self._args[3])
        if duration <= 0:
            print("[ERROR] `threshold` must be a positive integer" +
                  ", got: {}".format(duration))
            return False
        self._epoch_stop = self._epoch_start + int(duration)

        self._staking = 0
        if 'staking' in self._options:
            self._staking = int(self._options['staking'])
        if self._staking < 0:
            print("[ERROR] `staking` must be a non-negative integer" +
                  ", got: {}".format(self._staking))
            return False

        self._info = ''
        if 'info' in self._options:
            self._info = self._options['info']

        return True

    def run(self, stub):
        options = pdosd_proto.OperationProposeOptions(
            threshold=self._threshold,
            target=self._target,
            service=self._service,
            epoch_start=self._epoch_start,
            epoch_stop=self._epoch_stop,
            staking=self._staking,
            info=self._info
        )
        try:
            stub.OperationPropose(options)
            print("[DONE] Operation created.")
        except Exception as e:
            print(e)
            print("[ERROR] Check operation parameters, " +
                  "and check your balance.")


class OperationJoin(Command):
    def __init__(self, args, options):
        super(OperationJoin, self).__init__(args, options)

    def validate(self):
        if len(self._args) != 1:
            print("[ERROR] `operation join` expects 1 arguments: " +
                  "address.")
            return False

        self._address = self._args[0]

        return True

    def run(self, stub):
        options = pdosd_proto.OperationJoinOptions(
            address=self._address
        )
        try:
            stub.OperationJoin(options)
            print("[DONE] Operation joined.")
        except Exception as e:
            print(e)
            print("[ERROR] Check operation address " +
                  "(note that you can't join more than once).")


class Help(Command):
    def __init__(self, args, options):
        super(Help, self).__init__(args, options)

    def validate(self):
        self._command = ' '.join(self._args)
        return True

    def run(self, stub):
        if self._command == 'operation list':
            print("pDoS client")
            print("")
            print("  List upcoming operations.")
            print("")
            print("  Usage:")
            print("    pdos operation list")
            print("")
            print("  Examples:")
            print("    pdos operation list")
        elif self._command == 'operation propose':
            print("pDoS client")
            print("")
            print("  Propose a new operation.")
            print("")
            print("  Usage:")
            print("    pdos operation propose " +
                  "<target> <threshold> <epoch_start> <duration>")
            print("")
            print("  Arguments:")
            print("    <target> the domain name of the target.")
            print("    <threshold> the number of users required to join.")
            print("    <epoch_start> the operation start epoch.")
            print("    <duration> the operation duration in seconds.")
            print("")
            print("  Options:")
            print("    --service SERVICE the service to attack " +
                  "(supported values: www) [default: www]")
            print("    --staking STAKE the required stake for the operation " +
                  "(in wei) [default: 0]")
            print("    --info INFO human readable rationale for the " +
                  "operation [default: ""]")
            print("")
            print("  Examples:")
            print("    pdos operation propose " +
                  "www.foo.bar 2000 1563888880 3600")
            print("    pdos operation propose " +
                  "fcbk.com 2000 1563888880 3600 --info \"save the world\"")
        elif self._command == 'operation join':
            print("pDoS client")
            print("")
            print("  Commmit your participation to an operation.")
            print("")
            print("  Usage:")
            print("    pdos operation join <address>")
            print("")
            print("  Arguments:")
            print("    <address> the address of the opeation to join.")
            print("")
            print("  Examples:")
            print("    pdos operation join " +
                  "0x9E845a89AcacE3B2093A0c5c6a3fe75518758e8f")
        else:
            print("pDoS client")
            print("")
            print("  General options:")
            print("    --pdosd_rpc PDOSD_RPC pdosd RPC address " +
                  "[default: 127.0.0.1:7331]")
            print("")
            print("  pdos help [command]")
            print("    Display help about a command " +
                  "or this messsage if no command is provided.")
            print("    `pdos help operation propose`")
            print("")
            print("  pdos operation list")
            print("    List upcoming operations.")
            print("    `pdos operation list`")
            print("")
            print("  pdos operation propose " +
                  "<target> <threshold> <epoch_start> <duration>")
            print("    Propose a new operation.")
            print("    `pdos operation propose " +
                  "www.foo.bar 2000 1563888880 3600`")
            print("")
            print("  pdos operation join <address>")
            print("    Commmit your participation to an operation.")
            print("    `pdos operation join " +
                  "0x9E845a89AcacE3B2093A0c5c6a3fe75518758e8f`")


def main():
    argv = sys.argv[1:]

    args = []
    options = {}

    option = None
    for el in argv:
        if option is not None:
            options[option] = el
            option = None
            continue
        if el[:2] == '--':
            option = el[2:]
        else:
            args += [el]

    command = Help(args, options)
    if len(args) >= 1 and args[0] == 'help':
        command = Help(args[1:], options)

    if len(args) >= 2:
        if args[0] == 'operation':
            if args[1] == 'list':
                command = OperationList(args[2:], options)
            elif args[1] == 'propose':
                command = OperationPropose(args[2:], options)
            elif args[1] == 'join':
                command = OperationJoin(args[2:], options)

    if command.validate():
        rpc = "127.0.0.1:7331"
        if 'pdosd_rpc' in options:
            rpc = options['pdosd_rpc']

        channel = grpc.insecure_channel(rpc)
        stub = pdosd_grpc.PDOSDStub(channel)

        command.run(stub)
