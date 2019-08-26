from utils.log import log


class Listener():
    def __init__(self, OR_iface, trigger):
        """ Send all past entries to handle_event() for processing
        """
        self.OR_iface = OR_iface
        self.trigger = trigger

        for entry in self.OR_iface.get_past_event_entries():
            self.handle_event(entry)

    def handle_event(
            self,
            event,
    ):
        '''Called each time a registered event occurs.

        R reference contract (see R.sol):
            [solidity]
            event NewOperationEvent(address _sender, O _operation);
            event DestroyedContractEvent();

        O reference contract (see O.sol):
            [solidity]
            event NewUserEvent(address user);
            event OperationDecidedEvent();
        '''
        if event.event == 'OperationDecidedEvent':
            log("OperationDecidedEvent (operation: {})".format(
                event.address,
            ), "success")
            (_, target, service, epoch_start, epoch_stop, _, _, _, _,) = \
                self.OR_iface.get_operation_data(event.address)
            self.trigger.register(service, target, epoch_start, epoch_stop)
        elif event.event == 'NewUserEvent':
            log("NewUserEvent (operation: {}, user: {})".format(
                event.address, event.args._user,
            ), "success")
        elif event.event == 'NewOperationEvent':
            log("NewOperationEvent (operation: {})".format(
                event.args._operation,
            ), "success")
        elif event.event == 'DestroyedContractEvent':
            log("DestroyedContractEvent", "success")
        else:
            log("Unsupported: {}".format(event.event), "warning")

    def loop(
            self,
    ):
        '''EventThread main() function. Loops through registered event,
        and handles it when needed.
        '''
        for address in self.OR_iface.event_filters:
            for event in self.OR_iface.event_filters[address]:
                ev_entries = []
                try:
                    ev_entries = event.get_new_entries()
                except Exception as e:
                    log("Node timed out", "error")
                    print (e)

                for ev_instance in ev_entries:
                    self.handle_event(ev_instance)  # обработчик событий

