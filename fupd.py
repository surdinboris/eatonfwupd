import serial
import time
import io
import sys
import glob
import re
import os
from shutil import copyfile
#import subprocess
debug = False
buff= io.BytesIO(b'')
cwd= os.path.dirname(os.path.realpath(__file__))
def serial_ports():
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')
    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

# def sendcom(cmd=''):
#     ser.write(cmd.encode())
#     ser.write("\r\n".encode())

def spinning_cursor():
    while True:
        for cursor in '|/-\\':
            yield cursor

def read_until(ser,val,inval=None,timeout=230):
    start = time.time()
    time.clock()
    spinner = spinning_cursor()
    while True:
        elapsed = time.time() - start
        exceeded = elapsed > timeout
        if exceeded:
            raise TimeoutError
        sys.stdout.write(next(spinner))
        sys.stdout.flush()
        sys.stdout.write('\b')

        line = str(ser.readline().decode('ascii'))
        if len(line) > 1:
            if debug:
                print('>',line)
        if inval:
            invrev = re.search(inval, line)
        if inval and invrev:
            raise ConnectionError("Network card did not recieved IP via DHCP and asks for manual IP address, please check your DHCP server configuration")
        rev = re.search(val, line)
        if val and rev:
            # print('\b')
            return rev

def write(ser,comm):
    time.sleep(0.1)
    if len(comm) == 1:
        if debug:
            print('Writing {}'.format(comm.encode('ascii')))
        ser.write(comm.encode('ascii'))
    else:
        if debug:
            print('Writing {}'.format(comm.encode('ascii')))
        for sym in comm:
            ser.write(sym.encode('ascii'))
            time.sleep(0.1)

    time.sleep(1)
    ser.write('\r'.encode('ascii'))

def searchv(ser,val):
    while True:
        line = str(ser.readline().decode('UTF-8'))
        rev = re.search('{} (\w+)'.format(val), line)
        if debug:
            print(line)
        if rev:
            return rev[1]

def upgrade(ser):
    print('\n')
    input('Please connect bbu to COM port and network and press any key...\n\n')
    print('Please turn on BBU...')
    ser.flushInput()
    ser.flushOutput()
    print('\n')
    #Booting - searching for revision

    rev = searchv(ser,'Kitting revision :')
    sn = searchv(ser,'Serial number :')
    print('  >1 Network card {} found, revision {}'.format(sn, rev))

    if rev == 'LA':
        #put filename on tftp server for new revision NMC_EATON_JB_rp.bin
        copyfile(os.path.join(cwd, 'NMC_EATON_JB_rp.bin'),os.path.join(cwd,'TFTP-Root','image.bin'))
    else:
        # put filename on tftp server for OLD revision Network-Card-MS_Revision_JB.bin
        copyfile(os.path.join(cwd, 'Network-Card-MS_Revision_JB.bin'), os.path.join(cwd, 'TFTP-Root', 'image.bin'))

    #Waiting for upgrade mode
    read_until(ser,"To force the upgrade mode, type 'y', then press ENTER",timeout=20)
    write(ser,'y')
    print("  >2 Wait 1 min until boot...")
    # read_until("Set the IP address :")
    # write('192.168.1.2')
    # read_until("Set the subnet mask address :")
    # write('255.255.255.0')
    # read_until("Set the gateway address :")
    # write('0.0.0.0')
    read_until(ser,'Set the TFTP server IP address :',"Set the IP address :",timeout=70)
    print("  >3 Setting TFTP server IP address....")
    write(ser,'192.168.1.3')
    print("  >4 Working. DO NOT DISCONNECT BBU! Please wait...")
    read_until(ser,'Flashing done',timeout=30)
    print('  >5 Resetting card to default configuration')
    read_until(ser,'Press a key to display the Rescue Menu',timeout=280)
    ser.write('a'.encode('ascii'))
    read_until(ser,'Enter password :')
    write(ser,'admin')
    read_until(ser,'Return to Default Configuration ?')
    write(ser,'y')
    # read_until(ser,'Network connection with DHCP mode...')
    print('  >6 Flashing done successfully.')
    print('~'*50)
    upgrade(ser)


def init():
    #print("Restarting TFTP server...")
    # if not debug:
    #     subprocess.run(["net stop", "SolarWinds TFTP Server"])
    #     subprocess.run(["net start", "SolarWinds TFTP Server"])
    for file in os.listdir(os.path.join(cwd,'TFTP-Root')):
        os.remove(os.path.join(cwd,'TFTP-Root', file))
    if len(serial_ports()) > 0:
        port = serial_ports()[0]
        ser = serial.Serial(port,
                            timeout=10,
                            baudrate=9600,
                            xonxoff=0,
                            stopbits=1,
                            parity=serial.PARITY_NONE,
                            bytesize=8)
        upgrade(ser)
    else:
        input("No active COM ports found.  Please connect COM cable and press any key...")
        init()

if __name__ == "__main__":
    init()
