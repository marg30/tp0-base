from multiprocessing import Process, Barrier, Queue, Lock, Manager
import socket
import logging
import signal
from collections import defaultdict
from threading import BrokenBarrierError
from .message import BatchMessage, ACKMessage, FinishedNotification, WinnerMessage
from .protocol import Protocol
from .utils import Bet, store_bets, load_bets, has_won

LENGTH_FINISHED_NOTIFICATION = 2
NUM_CLIENTS_CON_SERVER = 6
NUM_CLIENTS = 5

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
        self.client_sockets = []
        self.processes = []
        self.client_agency_map = defaultdict(int)
        self._server_socket.settimeout(self.timeout)
        self.barrier = Barrier(NUM_CLIENTS_CON_SERVER)
        self.result_queue = Queue()  # Cola para enviar resultados a los hijos
        self.file_lock = Lock()
        self._set_signal_handlers()

    def _set_signal_handlers(self):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)

    def run(self):
        try:
            while len(self.client_sockets) < NUM_CLIENTS:
                client_sock = self.__accept_new_connection()
                if client_sock:
                    self.client_sockets.append(client_sock)
                    process = Process(target=self.__handle_client_connection, args=(client_sock, ))
                    self.processes.append(process)
                    process.start()
                else:
                    break

            if self.client_sockets and not self.kill_now:
                logging.debug("Start to receive bets")
                self.__process_connections()
            self.__join_processes()
        finally:
            self.__cleanup_resources()
            logging.info("action: shutdown_server | result: success")

    def _accept_clients(self):
        while len(self.client_sockets) < NUM_CLIENTS:
            client_sock = self.__accept_new_connection()
            if client_sock:
                self.client_sockets.append(client_sock)
                process = Process(target=self.__handle_client_connection, args=(client_sock,))
                self.processes.append(process)
                process.start()
            else:
                break

    def __join_processes(self):
        for process in self.processes:
            process.join()

    def __process_connections(self):
        logging.debug("Waiting for clients to finish")
        while not self.kill_now:
            try:
                self.barrier.wait(timeout=10)
                break
            except TimeoutError:
                logging.error("Barrier wait timed out.")
                self.barrier.reset()    
            except BrokenBarrierError:
                logging.error("Barrier was broken.")
                if self.kill_now:
                    return
                self.barrier.reset()
            except Exception as e:
                logging.error(f"Unexpected error while waiting at barrier: {e}")

        logging.debug("All clients have finished sending bets.")
        winners_per_agency = self.calculate_winners()
        for _ in range(NUM_CLIENTS):
            self.result_queue.put(winners_per_agency)
        self.barrier.wait()

    def __handle_client_connection(self, client_sock, ):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        signal.signal(signal.SIGINT, self.children_exit_gracefully)
        signal.signal(signal.SIGTERM, self.children_exit_gracefully)

        logging.debug("Handling new client connection")
        protocol = Protocol(client_sock)
        while not self.kill_now:
            try:
                msg_encoded = protocol.receive_message()
                if msg_encoded:
                    if is_finished_notification(msg_encoded):
                        notification = FinishedNotification.decode(msg_encoded)
                        logging.info(f"action: finished_notification | result: success | client_id: {notification.client_id}")
                        break
                    else:
                        self.__handle_bet(msg_encoded, protocol)
                else:
                    logging.info("No more data received from client.")
            except OSError as e:
                logging.error(f"action: receive_message | result: fail | error: {e}")
        if not self.kill_now:
            self.__wait_for_other_clients(protocol)
            self.barrier.wait()
        logging.debug("Closing child")
        client_sock.close()

    def __wait_for_other_clients(self, protocol):
        logging.debug("Waiting for other clients")
        while not self.kill_now:
            try: 
                self.barrier.wait()
                break
            except BrokenBarrierError:
                if not self.kill_now:
                    logging.debug('Reseting barrier')
                    self.barrier.reset()
        winners_per_agency = self.result_queue.get()
        self.__send_winners(protocol, winners_per_agency)


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

        with self.file_lock:
            store_bets(bets)
        logging.info(f"action: apuesta_recibida | result: success | cantidad: {len(bets)}")

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

    def __cleanup_resources(self):
        """
        Close all open client sockets, and clean up task and result queues.
        """
        logging.info("action: cleanup_resources | result: in_progress")
        for client_sock in self.client_sockets:
            if client_sock:
                try:
                    client_sock.close()
                except OSError as e:
                    logging.error(f"action: close_client_socket | result: fail | error: {e}")
        try:
            self.result_queue.close()
            self.result_queue.join_thread()
        except Exception as e:
            logging.error(f"action: cleanup_queues | result: fail | error: {e}")
        logging.info("action: cleanup_resources | result: success")

    def calculate_winners(self):
        logging.info("action: sorteo | result: success")
        bets = []
        with self.file_lock:
            bets = load_bets()
        
        winners_per_agency = defaultdict(list)
        for bet in bets:
            if has_won(bet):
                winners_per_agency[bet.agency].append(bet.document)
        return winners_per_agency

    def children_exit_gracefully(self, signum, frame):
        logging.debug("action: received_signal (child) | result: in_progress")
        self.kill_now = True
