import sys
import socket
import selectors
import types
from collections import defaultdict
from service_actions import register, login, delete_account, update_notification_limit, parse_request
from Model.ClientRequest import ClientRequest

# todo: bot up with ipp address as command line argument 
# todo: cooked can we use HTTO oor auth?


"""
Welcome & Command-Line Arguments.
We recommend using PORT = 5001 or 5002.

Proper usage to launch server:
    
    python3 main.py PORT VERSION=1
"""
if not len(sys.argv) == 4 and not len(sys.argv) == 3:
    sys.exit("Please follow the proper usage: python3 main.py PORT VERSION=1")
# TODO: more easy checks??? brownie points???
# elif not isinstance(sys.argv[2], int) or int(sys.argv[2]) < 0:
#     sys.exit("The PORT entered must be a positive integer.") 


# MARK: Configuration
PORT = int(sys.argv[1])
if sys.argv[2]:
    VERSION = int(sys.argv[2])
else:
    VERSION = 1


# MARK: Prepare sockets & selectors
selector = selectors.DefaultSelector()
hostname = socket.gethostname()
HOST = socket.gethostbyname(hostname) 


# MARK: Track necessary states
active_connections = {}                 # Track currently connected clients
pending_messages = defaultdict(list)    # Track undelivered messages
pending_deletion = defaultdict(list)    # Track messages to be deleted

# MARK: Managing Client-Server Connections
def accept_connection(sock):
    """
    Registers and forms socket connections between the server and individual clients.
    Utilizes selectors in a non-blocking manner to accept and register socket connections.

            Parameters:
                    sock: A socket used to connect with the client.
            Returns:
                    Void: Registers the connection in our global selectors.
                    Error: If the socket fails to connect, a socket error will be raised. 
    """
    try:
        conn, addr = sock.accept()
        print(f"Accepted connection from {addr}.")
        conn.setblocking(False)
        data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        selector.register(conn, events, data=data)
    except socket.error as e:
        print(f"Failed to accept socket connection with socket error: {e}")


def service_connection(key, mask):
    """
    Maintains socket connections to handle incoming messages and to address socket closures.
    Calls upon helper functions to handle cases of requests.

            Parameters:
                    key: key pieces of information about a socket, including its data, fd, 
                         and more.
                    mask: an integer representing events occuring on the socket
            Returns:
                    Void: handles delegating to specific functionalities
    """
    sock = key.fileobj
    data = key.data
    # Data received from the client
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)
        if recv_data:
            data.outb += recv_data
            handle_client_requests(sock, data)
        else:
            print(f"Closing connection to {data.addr}")
            username = None
            for user, client_sock in active_connections.items():
                if client_sock == sock:
                    username = user
                    break
            
            # Remove from active_connections if found
            if username:
                print(f"Removing active connection for user: {username}")
                active_connections.pop(username)
            
            selector.unregister(sock)
            sock.close()
    # TODO: Can we delete this?
    # if mask & selectors.EVENT_WRITE:
    #     if data.outb:
            # print("data", data.outb)
            # return_data = "Service connection established."
            # return_data = return_data.encode("utf-8")
            # sent = sock.send(return_data)
            # data.outb = data.outb[sent:]
            # something = 0


# MARK: Managing Client-Server Requests & Operations
def handle_client_requests(sock, data):
    """
    Maintains socket connections to handle incoming messages and to address socket closures.
    Calls upon helper functions to handle cases of requests.

            Parameters:
                    key: key pieces of information about a socket, including its data, fd, 
                         and more.
                    mask: an integer representing events occuring on the socket
            Returns:
                    Void: handles delegating to specific functionalities
    """
    print(f"Entering handle_client_requests: data.outb = {data.outb}")
    try:
        # Decipher message as a ClientRequest object.
        request = parse_request(data)
        opcode = request.opcode
        arguments = request.arguments
        # Verify parsing.
        print(f"Verify parsed request with OPCODE {opcode}: {arguments}")

        # Considering the given operation desired, respond accordingly.
        # Call out to helper functionalities & operation-handy code.
        match opcode:         
            case "REGISTER":
                response = register(*arguments)
            
            case "LOGIN":
                response = login(*arguments)
                # Ensure that we add this connection to our currently active
                # connections.
                
                # Send success immediately
                if response.split("§")[2] == "LOGIN_SUCCESS":
                    data.outb = response.encode("utf-8")
                    sent = sock.send(data.outb)             # Send the response over the wire.
                    data.outb = data.outb[sent:] 
                    
                    active_connections[arguments[0]] = sock
                    check_pending_messages(arguments[0])
                    response = ""
            
            case "SEND_MESSAGE":
                response = send_message(*arguments)
            case "DELETE_MESSAGE":
                response = delete_message(*arguments)
            case "DELETE_ACCOUNT":
                response = delete_account(*arguments)
            case "NOTIFICATION_LIMIT":
                response = update_notification_limit(*arguments)
            case _:
                response = "Nothing to do."

        # Encode the appropriate response, which may contain
        # information about the success or failure of an operation,
        # using our serialization functionality.
        data.outb = response.encode("utf-8")
        sent = sock.send(data.outb)             # Send the response over the wire.
        data.outb = data.outb[sent:]            # Clear the output buffer.
        print(f"Check outb: {data.outb}")     # MUST be empty when all is sent.
        print(f"Response sent successfully via {sock}")
    except:
        # TODO: make this better!!
        print(f"handling_client_reponse: error handling data {data}")


def send_message(sender, recipient, message):
    """ADD COMMENTS"""
    print(f"Sending message from {sender} to {recipient}: {message}")
    # Case 1: Recipient is online.
    #       Then, send the message immediately.
    # 
    # Case 2: The recipient is not online.
    #       Then, wait until they are back to check.
    OP_CODE = "NEW_MESSAGE"
    request = ClientRequest.serialize(VERSION, OP_CODE, [sender, recipient, message])
    # message_request = f"NEW_MESSAGE§{sender}§{recipient}§{message}"
    # request = f"{VERSION}§{len(message_request)}§{message_request}"
    if recipient in active_connections.keys():
        # They are online, so send the message
        # message_request = f"NEW_MESSAGE§{sender}§{recipient}§{message}"
        # request = f"{VERSION}§{len(message_request)}§{message_request}"

        # Okay, so we have now added data to the buffer of this particular socket of 
        # the person who is receiving the message, thus we must select their data buffer and
        # clear it!
        # sent = active_connections[recipient].send(request.encode("utf-8"))
        sent = active_connections[recipient].send(request.encode("utf-8"))
        key = selector.get_key(active_connections[recipient])
        key.data.outb = key.data.outb[sent:]
        
        message_status = ClientRequest.serialize(VERSION, "RECEIVED_MESSAGE", [sender, message])
        # message_status = f"RECEIVED_MESSAGE§{sender}§{message}"
        # request2 = f"{VERSION}§{len(message_status)}§{message_status}"

        # return request2
        return message_status
    else:
        # not online!
        # Add to a list of pending messages, so that when the user 
        # comes back online that they will receive their messages.
        print("pending messages append: ", request)
        pending_messages[recipient].append(request)
        print("updated pending messages", pending_messages)
        # To ensure no failures occur!
        message_status = f"RECEIVED_MESSAGE§{sender}§{message}"
        request2 = f"{VERSION}§{len(message_status)}§{message_status}∞"
        return request2

# MARK: Deletion
def delete_message(sender, message, timestamp):
    print("delete_message", sender, message, timestamp)
    OP_CODE = "DELETE_MESSAGE"
    request = ClientRequest.serialize(VERSION, OP_CODE, [timestamp, sender, message])
    
    if recipient in active_connections.keys():
        sent = active_connections[recipient].send(request.encode("utf-8"))
        key = selector.get_key(active_connections[recipient])
        key.data.outb = key.data.outb[sent:]
        message_status = ClientRequest.serialize(VERSION, "DELETE_MESSAGE_SUCCEEDED", [message_uuid, sender, recipient])
        return message_status
    else:
        pending_deletion[recipient].append(request)
        message_status = ClientRequest.serialize(VERSION, "DELETE_MESSAGE_SUCCEEDED", [message_uuid, sender, recipient])
        return message_status

def check_pending_deleted_messages(username):
    if len(pending_deletion[username]) > 0:
        try:
            for message in pending_deletion[username]:
                active_connections[username].send(message.encode("utf-8"))
            pending_deletion[username] = []
        except: 
            # The socket must have disconnected, thus hold onto the pending options.
            return

def check_pending_messages(username):
    """Documentation"""
    if len(pending_messages[username]) > 0:
        print("check_pending_messages")
        # Send over all of the pending messages to the client.
        try:
            for message in pending_messages[username]:
                print("found a pending message", message)
                active_connections[username].send(message.encode("utf-8"))
            pending_messages[username] = []
        except: 
            # The socket must have disconnected, thus hold onto the pending options.
            return

if __name__ == "__main__":
    # AF_INET defines the address family (ex. IPv4)
    # SOCK_STREAM defines socket type (ex. TCP)
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.bind((HOST, PORT))
    server_socket.listen()
    print("Listening on", (HOST, PORT))
    # Allow the socket to continue working without putting other possible connections on hold.
    server_socket.setblocking(False)
    # Register the initial socket by the server (only looks for incoming connections)
    selector.register(server_socket, selectors.EVENT_READ, data=None)
    
    try:
        # Infinitely listen to the socket
        while True:
            # Look at all currently registered sockets, and if we get an event sent, it selects it & then we handle the events.
            events = selector.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    print("accepting connection!")
                    accept_connection(key.fileobj)
                else:
                    service_connection(key, mask)
    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting")
    finally:
        selector.close()
