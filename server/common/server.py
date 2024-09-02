import socket
import logging
import signal

class Server:
    def __init__(self, port, listen_backlog):
        # Initialize server socket
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', port))
        self._server_socket.listen(listen_backlog)
        self.kill_now = False
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)
        self.client_sockets = []

    def run(self):
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """

        # TODO: Modify this program to handle signal to graceful shutdown
        # the server
        try:
            while not self.kill_now:
                try:
                    client_sock = self.__accept_new_connection()
                    if client_sock:  # Only handle the client if the server is still running
                        self.__handle_client_connection(client_sock)
                except OSError as e:
                    if self.kill_now:
                        # If we are shutting down, it's okay if accept fails
                        break
                    else:
                        logging.error(f"action: accept_connection | result: fail | error: {e}")
                        continue
        finally:
            self.__cleanup_resources()
            logging.info("action: shutdown_server | result: success")

    def __handle_client_connection(self, client_sock):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        try:
            # TODO: Modify the receive to avoid short-reads
            msg = client_sock.recv(1024).rstrip().decode('utf-8')
            addr = client_sock.getpeername()
            logging.info(f'action: receive_message | result: success | ip: {addr[0]} | msg: {msg}')
            self.client_sockets.append(client_sock)
            # TODO: Modify the send to avoid short-writes
            client_sock.send("{}\n".format(msg).encode('utf-8'))
        except OSError as e:
            logging.error("action: receive_message | result: fail | error: {e}")
        finally:
            client_sock.close()

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
        except OSError as e:
            if self.kill_now:
                # Server is shutting down, so this error is expected
                logging.info("Server socket closed, stopping acceptance of new connections.")
            else:
                logging.error(f"action: accept_connections | result: fail | error: {e}")
            return None       
    
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
                client_sock.close()
            except OSError as e:
                logging.error(f"action: close_client_socket | result: fail | error: {e}")
        logging.info("action: cleanup_resources | result: success")    
