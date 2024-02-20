# CSC361 P1 Marking Script
# Author: Victor Kamel

from enum import Enum
from collections import namedtuple
from time import sleep
import pexpect

import sys

Score = float
Test = namedtuple("Test", ["type", "value", "test"])
TestType = Enum("Type", {"POS" : + 1, "NEG" : - 1})

tests = []

current_port = 8888

SWS = sys.argv[1]
output_file = open(f"output.txt", "w")

def dprint(*args, **kwargs):
    print(*args, **kwargs)
    print(*args, file=output_file, **kwargs)

def make_test(ttype, tvalue):
    return lambda func: tests.append(Test(ttype, tvalue, func))

def compare(expected, received, weight, decode = False):
    assert(isinstance(received, bytes))
    if isinstance(expected, bytes): expected = [expected]
    assert(all(isinstance(x, bytes) for x in expected))
    
    if received in expected:
        return weight
    else:
        dprint(" --- Expected --- ", expected[0] if not decode else expected[0].decode(), sep="\n")
        dprint(" --- Received --- ", received if not decode else received.decode(), sep="\n")
        dprint(" ---")
        
        while True:
            try:
                score = Score(input(f"Score? [0-{weight}]: ")); assert(0 <= score <= weight)
                return score
            except (ValueError, AssertionError):
                pass

### TEST DATA

with open("small.html", "rb") as file: small = file.read()
with open("large.html", "rb") as file: large = file.read()

server = None

def activate_server():
    global server

    server = pexpect.spawn(f'/bin/bash -c "sudo ip netns exec h2 python3 {SWS} 10.10.1.100 {current_port}"', timeout = 5)
    sleep(1)

def ensure_server_alive(score):
    if server.isalive():
        return score
    else:
        server.expect_exact([pexpect.EOF, pexpect.TIMEOUT], timeout = 0)
        dprint(" --- Server Output ---", server.before.decode(), sep = "\n")
        dprint(" ---")
        dprint("Server has died. No points awarded. Restarting...")
        global current_port
        current_port += 1
        sleep(3)
        activate_server()
        return 0

# https://pexpect.readthedocs.io/en/stable/overview.html#find-the-end-of-line-cr-lf-conventions
efmt = lambda x : x.replace(b"\n", b"\r\n")

create_client = lambda timeout = 5, host = 'h1': pexpect.spawn(f'/bin/bash -c "sudo ip netns exec {host} nc 10.10.1.100 {current_port}"', echo = False, timeout = timeout)

@make_test(TestType.POS, 0)
def test_start_server():
    activate_server()
    
    if not server.isalive():
        server.expect_exact([pexpect.EOF, pexpect.TIMEOUT], timeout = 0)
        dprint(" --- Server Output ---", server.before.decode(), sep = "\n")
        dprint(" ---")
        dprint("Failed to start server.")
        exit(-1)
    
    return 0

@make_test(TestType.POS, 1)
def test_200_ok_small():
    request = b'GET /small.html HTTP/1.0'
    expected_responses = [
        efmt(b"HTTP/1.0 200 OK\r\n\r\n" + small),
        efmt(b"HTTP/1.0 200 OK\r\nConnection: close\r\n\r\n" + small),
    ]

    client = create_client()

    # Request
    client.sendline(request)
    client.sendline('')

    # Response
    client.expect_exact([pexpect.EOF, pexpect.TIMEOUT])
    score = compare(expected_responses, client.before, 1)
    client.close()

    return ensure_server_alive(score)

@make_test(TestType.POS, 1)
def test_200_ok_large():
    request = b'GET /large.html HTTP/1.0'
    expected_responses = [
        efmt(b"HTTP/1.0 200 OK\r\n\r\n" + large),
        efmt(b"HTTP/1.0 200 OK\r\nConnection: close\r\n\r\n" + large),
    ]

    client = create_client()

    # Request
    client.sendline(request)
    client.sendline('')

    # Response
    client.expect_exact([pexpect.EOF, pexpect.TIMEOUT])
    score = compare(expected_responses, client.before, 1)
    client.close()

    return ensure_server_alive(score)

@make_test(TestType.POS, 1)
def test_404_not_found():
    request = b'GET /notfound HTTP/1.0'
    expected_responses = [
        efmt(b"HTTP/1.0 404 Not Found\r\nConnection: close\r\n\r\n"),
        efmt(b"HTTP/1.0 404 Not Found\r\n\r\n")
    ]

    client = create_client()

    # Request
    client.sendline(request)
    client.sendline('')

    # Response
    client.expect_exact([pexpect.EOF, pexpect.TIMEOUT])
    score = compare(expected_responses, client.before, 1)
    client.close()

    return ensure_server_alive(score)

@make_test(TestType.POS, 2)
def test_400_bad_request():
    request = b'get /notfound HTTP/1.0'
    expected_responses = [
        efmt(b"HTTP/1.0 400 Bad Request\r\nConnection: close\r\n\r\n"),
        efmt(b"HTTP/1.0 400 Bad Request\r\n\r\n"),
    ]

    client = create_client(timeout = 2)

    # Request
    client.sendline(request)
    client.expect_exact([pexpect.EOF, pexpect.TIMEOUT])

    score = 0

    if client.before != b"":
        dprint("Exited immediately.")
        score += 1
    else:
        dprint("Did not exit immediately.")
        client.sendline('')
        client.expect_exact([pexpect.EOF, pexpect.TIMEOUT])

    score += compare(expected_responses, client.before, 1)
    client.close()

    return ensure_server_alive(score)

@make_test(TestType.POS, 1)
def test_header_fields():
    request1 = b'GET /notfound HTTP/1.0\nConnection: keep-alive'
    request2 = b'GET /notfound HTTP/1.0'
    expected_responses = [
        efmt(b"HTTP/1.0 404 Not Found\r\nConnection: keep-alive\r\n\r\n" +
             b"HTTP/1.0 404 Not Found\r\nConnection: close\r\n\r\n"),
        efmt(b"HTTP/1.0 404 Not Found\r\nConnection: keep-alive\r\n\r\n" +
             b"HTTP/1.0 404 Not Found\r\n\r\n"),
    ]

    client = create_client()

    # Request
    client.sendline(request1)
    client.sendline('')
    sleep(0.2)
    client.sendline(request2)
    client.sendline('')

    # Response
    client.expect_exact([pexpect.EOF, pexpect.TIMEOUT])
    score = compare(expected_responses, client.before, 1)
    client.close()

    return ensure_server_alive(score)

@make_test(TestType.POS, 1)
def test_concurrent_connections():
    # Screen for use of select
    serverfile = pexpect.spawn(f'/bin/bash -c "cat {SWS}"')
    
    if serverfile.expect_exact(['select', pexpect.EOF, pexpect.TIMEOUT]) != 0:
        dprint("Use of select not detected.")
        return 0
    else:
        dprint("select detected.")

    serverfile.close()

    request1 = b'GET /notfound HTTP/1.0\nConnection: keep-alive'
    request2 = b'GET /notfound HTTP/1.0'
    expected_responses = [
        efmt(b"HTTP/1.0 404 Not Found\r\nConnection: keep-alive\r\n\r\n" +
             b"HTTP/1.0 404 Not Found\r\nConnection: close\r\n\r\n"),
        efmt(b"HTTP/1.0 404 Not Found\r\nConnection: keep-alive\r\n\r\n" +
             b"HTTP/1.0 404 Not Found\r\n\r\n"),
    ]

    client1 = create_client(host = "h1")
    client2 = create_client(host = "r")

    # Request
    client1.sendline(request1)
    client1.sendline('')
    client2.sendline(request1)
    client2.sendline('')
    sleep(0.1)
    client1.sendline(request2)
    client1.sendline('')
    client2.sendline(request2)
    client2.sendline('')

    client1.expect_exact([pexpect.EOF, pexpect.TIMEOUT])
    client2.expect_exact([pexpect.EOF, pexpect.TIMEOUT])

    if client1.before != client2.before:
        dprint(" --- Client 1 ---", client1.before, sep = "\n")
        dprint(" --- Client 2 ---", client2.before, sep = "\n")
        dprint(" ---")
        dprint("Output of client 1 and 2 do not match. No points.")
        score = 0
    else:
        score = compare(expected_responses, client1.before, 1)
    
    client1.close()
    client2.close()

    return ensure_server_alive(score)

@make_test(TestType.POS, 1)
def test_back_to_back_requests():
    expected_responses = [
        efmt(b"HTTP/1.0 404 Not Found\r\nConnection: keep-alive\r\n\r\nHTTP/1.0 200 OK\r\nConnection: keep-alive\r\n\r\n<h1>Lorem ipsum dolor sit amet</h1>\nHTTP/1.0 400 Bad Request\r\nConnection: close\r\n\r\n"),
        efmt(b"HTTP/1.0 404 Not Found\r\nConnection: keep-alive\r\n\r\nHTTP/1.0 200 OK\r\nConnection: keep-alive\r\n\r\n<h1>Lorem ipsum dolor sit amet</h1>\nHTTP/1.0 400 Bad Request\r\n\r\n"),
    ]
    
    # Request
    client = pexpect.spawn(f'/bin/bash -c "sudo ip netns exec h1 nc 10.10.1.100 {current_port} < multiple_requests.txt"', timeout = 5)

    # Response
    client.expect_exact([pexpect.EOF, pexpect.TIMEOUT])
    score = compare(expected_responses, client.before, 1)
    client.close()

    return ensure_server_alive(score)

@make_test(TestType.POS, 1)
def test_timeout():
    request1 = b'GET /notfound HTTP/1.0\nConnection: keep-alive'
    request2 = b'GET /notfound HTTP/1.0'
    expected_response = efmt(b"HTTP/1.0 404 Not Found\r\nConnection: keep-alive\r\n\r\n")

    client = create_client()

    # Request
    client.sendline(request1)
    client.sendline('')
    sleep(33)
    # The server should not respond to this request
    client.sendline(request2)
    client.sendline('')

    # Response
    client.expect_exact([pexpect.EOF, pexpect.TIMEOUT])
    score = compare(expected_response, client.before, 1)
    client.close()

    return ensure_server_alive(score)

@make_test(TestType.NEG, 0.5)
def test_supports_crlf():
    request = b'GET /small.html HTTP/1.0'
    expected_responses = [
        efmt(b"HTTP/1.0 200 OK\r\n\r\n" + small),
        efmt(b"HTTP/1.0 200 OK\r\nConnection: close\r\n\r\n" + small),
    ]

    client = pexpect.spawn(f'/bin/bash -c "sudo ip netns exec h1 nc -C 10.10.1.100 {current_port}"', echo = False, timeout = 5)

    # Request
    client.sendline(request)
    client.sendline('')

    # Response
    client.expect_exact([pexpect.EOF, pexpect.TIMEOUT])
    score = compare(expected_responses, client.before, 0.5)
    client.close()

    return ensure_server_alive(score)

@make_test(TestType.NEG, 0.5)
def test_parsing():
    request1 = b'GET /notfound HTTP/1.0\nconnection:Keep-ALIVE'
    request2 = b'GET /notfound HTTP/1.0'
    expected_responses = [
        efmt(b"HTTP/1.0 404 Not Found\r\nConnection: keep-alive\r\n\r\n" +
             b"HTTP/1.0 404 Not Found\r\nConnection: close\r\n\r\n"),
        efmt(b"HTTP/1.0 404 Not Found\r\nConnection: keep-alive\r\n\r\n" +
             b"HTTP/1.0 404 Not Found\r\n\r\n"),
    ]

    client = create_client()

    # Request
    client.sendline(request1)
    client.sendline('')
    sleep(0.2)
    client.sendline(request2)
    client.sendline('')

    # Response
    client.expect_exact([pexpect.EOF, pexpect.TIMEOUT])
    score = compare(expected_responses, client.before, 0.5)
    client.close()

    return ensure_server_alive(score)

@make_test(TestType.POS, 1)
def test_log_format():
    server.expect_exact([pexpect.EOF, pexpect.TIMEOUT], timeout = 0)
    
    dprint(f"There should be 17 lines. There are {len(server.before.splitlines())}. May vary if some tests failed.")
    score = compare(b"time: client_ip:client_port request; response", server.before, 1, decode = True)
    server.close()

    return score

def dprint_sep(): dprint("=========")

if __name__ == "__main__":
    points_earned = 0
    points_lost   = 0
    points_total  = 0

    dprint(f"Collected: {len(tests)} tests")
    
    for (ttype, tvalue, test) in tests:
        
        dprint_sep(); dprint(f"Running test: {test.__name__}")
        
        points = test(); assert(0 <= points <= tvalue)

        if ttype == TestType.POS:
            dprint(f"Earned: {points} points out of {tvalue}.")
            points_earned += points
            points_total  += tvalue
        elif ttype == TestType.NEG:
            lost = tvalue - points
            if lost:
                dprint(f"Lost: {lost} points.")
            else:
                dprint("Passed.")
            points_lost   += tvalue - points
        else:
            dprint(f"Lost: {points} points")
            raise Exception("Unknown test type.")


    score = max(0, points_earned - points_lost)

    dprint_sep()
    dprint(f"Score: {score} / {points_total}")
