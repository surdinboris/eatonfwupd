import time
debug=False
def read_until(timeout=180):
    start=time.time()
    time.clock()
    while True:
        elapsed = time.time() - start
        print(elapsed)
        exceeded=elapsed>timeout

        # line = str(ser.readline().decode('ascii'))
        # if len(line) > 1:
        #     if debug:
        #         print('>',line)
        # if inval:
        #     invrev = re.search(inval, line)
        # if inval and invrev:
        #     raise ConnectionError("Network card did not recieved IP via DHCP and asks for manual IP address, please check your DHCP server configuration")
        # rev = re.search(val, line)
        # if val and rev:
        #     return rev
        if exceeded:
            raise TimeoutError

read_until()