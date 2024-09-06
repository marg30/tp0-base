from multiprocessing import Process, Barrier, Queue
import socket
import logging
import signal
from collections import defaultdict
from .message import BatchMessage, ACKMessage, FinishedNotification, WinnerMessage
from .protocol import Protocol
from .utils import Bet, store_bets, load_bets, has_won

LENGTH_FINISHED_NOTIFICATION = 2
NUM_CLIENTS_CON_SERVER = 6
NUM_CLIENTS = 5


def calculate_winners():
    logging.info("action: sorteo | result: success")
    bets = load_bets()
    winners_per_agency = defaultdict(list)
    for bet in bets:
        if has_won(bet):
            winners_per_agency[bet.agency].append(bet.document)
    return winners_per_agency


def is_finished_notification(bytes_arr):
    # Suponiendo que FinishedNotification tiene un identificador único o alguna forma de distinguirse
    return len(bytes_arr) == LENGTH_FINISHED_NOTIFICATION


class Server:
    def __init__(self, port, listen_backlog, timeout=5):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self.kill_now = False
        self.timeout = timeout
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)
        self.client_sockets = []
        self.processes = []
        self.client_agency_map = defaultdict(int)
        self._server_socket.settimeout(self.timeout)
        self.barrier = Barrier(NUM_CLIENTS_CON_SERVER)
        self.task_queue = Queue()  # Cola para enviar apuestas al proceso padre
        self.result_queue = Queue()  # Cola para enviar resultados a los hijos

    def run(self):
        try:
            bet_processing_worker = Process(target=self.__process_bets)
            bet_processing_worker.start()
            while len(self.client_sockets) < NUM_CLIENTS:
                try:
                    client_sock = self.__accept_new_connection()
                    if client_sock:
                        self.client_sockets.append(client_sock)
                        process = Process(target=self.__handle_client_connection, args=(client_sock,))
                        self.processes.append(process)
                        process.start()
                except OSError as e:
                    if self.kill_now:
                        # If we are shutting down, it's okay if accept fails
                        break
                    else:
                        logging.error(f"action: accept_connection | result: fail | error: {e}")
                        continue
            if len(self.client_sockets) > 0:
                logging.debug("Start to receive bets")
                self.__process_connections()
        
            logging.debug("joining processes")
            for p in self.processes:
                p.join()
            logging.debug("finished joining")
        finally:
            bet_processing_worker.terminate()
            bet_processing_worker.join()
            self.__cleanup_resources()
            logging.info("action: shutdown_server | result: success")

    def __process_connections(self):
        self.barrier.wait()
        logging.debug("All clients have finished sending bets.")
        winners_per_agency = calculate_winners()
        for _ in range(NUM_CLIENTS):
            self.result_queue.put(winners_per_agency)
        self.barrier.wait()

    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        logging.debug("Starting new process")
        protocol = Protocol(client_sock)
        while True:
            try:
                msg_encoded = protocol.receive_message()
                if msg_encoded:
                    if is_finished_notification(msg_encoded):
                        notification = FinishedNotification.decode(msg_encoded)
                        logging.info(f"action: finished_notification | result: success | client_id: {notification.client_id}")
                        self.barrier.wait()
                        winners_per_agency = self.result_queue.get()
                        self.__send_winners(protocol, winners_per_agency)
                        self.barrier.wait() 
                        break
                    else:
                        self.__handle_bet(msg_encoded, protocol)
                else: 
                    logging.info("No more data received from client.")
            except OSError as e:
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
            logging.debug("Processing batch")
            for msg in batch_message.messages:
                bet = Bet(batch_message.client_id, msg.name, msg.last_name, msg.id_document, msg.birth_date, msg.number)
                bets.append(bet)
        except:
            logging.error(f"action: apuesta_recibida | result: fail | cantidad: {len(bets)}.")
        
        self.task_queue.put(bets)
        ack_msg = ACKMessage(batch_message.batch_id, len(bets))
        protocol.send_message(ack_msg.encode()) 

    def __send_winners(self, protocol, winners_per_agency):        
            agency_id = self.client_agency_map[protocol.client_sock]
            winner_msg = WinnerMessage(winners_per_agency[agency_id])
            protocol.send_message(winner_msg.encode())

    def exit_gracefully(self, signum, frame):
        """
        Set the kill flag to True to stop accepting new connections and close the server socket.
        """
        logging.info("action: received_signal | result: in_progress")
        self.kill_now = True
        self._server_socket.close()

        for process in self.processes:
            if process.is_alive():
                process.terminate()

        for process in self.processes:
            process.join()        
        self.__cleanup_resources()
        logging.info("action: shutdown_server | result: success")

    def __cleanup_resources(self):
        """
        Close all open client sockets, and clean up task and result queues.
        """
        logging.info("action: cleanup_resources | result: in_progress")
        for client_sock in self.client_sockets:
            try:
                if client_sock:
                    client_sock.close()
            except OSError as e:
                logging.error(f"action: close_client_socket | result: fail | error: {e}")
        logging.info("action: cleanup_resources | result: success")    

        try:
            self.task_queue.close()
            self.result_queue.close()
        except Exception as e:
            logging.error(f"action: cleanup_queues | result: fail | error: {e}")

    def __process_bets(self):
        """
        Continuously process bets from the task_queue as they are received.
        This function will run in a separate process.
        """
        logging.info("action: start_processing_bets | result: in_progress")
        while not self.kill_now:
            try:
                if not self.task_queue.empty():
                    bets = self.task_queue.get()
                    store_bets(bets)
                    logging.info(f"action: apuesta_recibida | result: success | cantidad: {len(bets)}")
            except Exception as e:
                logging.error(f"action: process_bets | result: fail | error: {e}")
        logging.info("action: stop_processing_bets | result: success")