import socket
import logging
import time
import signal
from collections import defaultdict
from .message import BatchMessage, ACKMessage, FinishedNotification, WinnerMessage
from .protocol import Protocol
from .utils import Bet, store_bets, load_bets, has_won

LENGTH_FINISHED_NOTIFICATION = 2


def is_finished_notification(bytes_arr):
    return len(bytes_arr) == LENGTH_FINISHED_NOTIFICATION


class Server:
    def __init__(self, port, listen_backlog, timeout=5):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self.kill_now = False
        self.timeout = timeout
        self.received_notifications = set()
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)
        self.client_sockets = []
        self.client_agency_map = defaultdict(int)
        self.start_time = None
        self._server_socket.settimeout(self.timeout)

    def run(self):
        try:
            self.start_time = time.time()
            while not self.kill_now and (time.time() - self.start_time) < self.timeout:
                try:
                    client_sock = self.__accept_new_connection()
                    if client_sock:
                        self.client_sockets.append(client_sock)
                except OSError as e:
                    if self.kill_now:
                        # If we are shutting down, it's okay if accept fails
                        break
                    else:
                        logging.error(f"action: accept_connection | result: fail | error: {e}")
                        continue
            if len(self.client_sockets) > 0:
                self.__process_connections()
        finally:
            self.__cleanup_resources()
            logging.info("action: shutdown_server | result: success")

    def __process_connections(self):
        protocols = []
        for client_sock in self.client_sockets:
            protocols.append(Protocol(client_sock))
        while not self.__all_notifications_received():
            for protocol in protocols:
                self.__handle_client_connection(protocol)
                if self.__all_notifications_received():
                    break
        self.__send_winners()

    def __handle_client_connection(self, protocol):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            msg_encoded = protocol.receive_message()
            if msg_encoded:
                if is_finished_notification(msg_encoded):
                    notification = FinishedNotification.decode(msg_encoded)
                    self.received_notifications.add(notification.client_id)
                    logging.info(f"action: finished_notification | result: success | client_id: {notification.client_id}")
                else:
                    self.__handle_bet(msg_encoded, protocol)
            else: 
                logging.info("No more data received from client.")
        except OSError as e:
            if e == "timed out":
                logging.debug("No more data received from client.")
            else:
                logging.error(f"action: receive_message | result: fail | error: {e}")

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        logging.info('action: accept_connections | result: in_progress')
        try:
            # Connection arrived
            c, addr = self._server_socket.accept()
            logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
            return c
        except socket.timeout:
            logging.info("Stopped accepting new connections (timeout).")
        except OSError as e:
            if self.kill_now:
                # Server is shutting down, so this error is expected
                logging.info("Server socket closed, stopping acceptance of new connections.")
            else:
                logging.error(f"action: accept_connections | result: fail | error: {e}")
            return None

    def __handle_bet(self, msg_encoded, protocol):
        batch_message = BatchMessage.decode(msg_encoded)
        bets = []
        logging.debug(f"action: process_bet")
        if protocol.client_sock not in self.client_agency_map:
            self.client_agency_map[protocol.client_sock] = batch_message.client_id

        try:
            for msg in batch_message.messages:
                bet = Bet(batch_message.client_id, msg.name, msg.last_name, msg.id_document, msg.birth_date, msg.number)
                bets.append(bet)
        except Exception as e: 
            logging.debug(e)
            logging.error(f"action: apuesta_recibida | result: fail | cantidad: {len(bets)}.")

        store_bets(bets)
        logging.info(f"action: apuesta_recibida | result: success | cantidad: {len(bets)}")
        ack_msg = ACKMessage(batch_message.batch_id, len(bets))
        protocol.send_message(ack_msg.encode())

    def __send_winners(self):
        logging.info("action: sorteo | result: success")
        bets = load_bets()
        winners_per_agency = defaultdict(int)
        for bet in bets: 
            if has_won(bet):
                winners_per_agency[bet.agency] += 1
        
        for client_sock in self.client_sockets:
            agency_id = self.client_agency_map[client_sock]
            protocol = Protocol(client_sock)
            winner_msg = WinnerMessage(winners_per_agency[agency_id])
            protocol.send_message(winner_msg.encode())

    
    def exit_gracefully(self, signum, frame):
        """
        Set the kill flag to True to stop accepting new connections and close the server socket.
        """
        logging.info("action: received_signal | result: in_progress")
        self.kill_now = True
        self._server_socket.close()

    def __cleanup_resources(self):
        """
        Close all open client sockets.
        """
        logging.info("action: cleanup_resources | result: in_progress")
        for client_sock in self.client_sockets:
            try:
                if client_sock:
                    client_sock.close()
            except OSError as e:
                logging.error(f"action: close_client_socket | result: fail | error: {e}")
        logging.info("action: cleanup_resources | result: success")

    def __all_notifications_received(self):
        return len(self.received_notifications) == len(self.client_sockets)
