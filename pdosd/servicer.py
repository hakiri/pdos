import time

import proto.pdosd_pb2_grpc as pdosd_grpc
import proto.pdosd_pb2 as pdosd_proto


class Servicer(pdosd_grpc.PDOSDServicer):
    def __init__(self, OR_iface):
        super(Servicer, self).__init__()
        self.OR_iface = OR_iface

    def OperationList(
            self,
            request,
            context,
    ):
        operations = self.OR_iface.enum_operations()

        for operation in operations:
            (threshold,
             target,
             service,
             epoch_start,
             epoch_stop,
             staking,
             info,
             nbusers,
             decided,
             ) = \
                self.OR_iface.get_operation_data(operation)

            joined = self.OR_iface.has_user_joined(operation)

            yield pdosd_proto.Operation(
                address=operation,
                threshold=threshold,
                target=target,
                service=service,
                epoch_start=epoch_start,
                epoch_stop=epoch_stop,
                staking=staking,
                info=info,
                users=nbusers,
                decided=decided,
                joined=joined)

    def OperationPropose(
            self,
            request,
            context,
    ):
        self.OR_iface.propose_operation(
            request.threshold,
            request.target,
            request.service,
            request.epoch_start,
            request.epoch_stop,
            request.staking,
            request.info,
        )
        return pdosd_proto.OperationProposeResult()

    def OperationJoin(
            self,
            request,
            context,
    ):
        '''Find out required staking, then join
        '''
        (_, _, _, _, _, required_staking, _, _, _) = \
            self.OR_iface.get_operation_data(request.address)
        self.OR_iface.join_operation(request.address, required_staking)

        return pdosd_proto.OperationJoinResult()
