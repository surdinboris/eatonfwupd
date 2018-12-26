import serial
import time
import io
import sys
import glob
import re
import os
from shutil import copyfile

debug = True
buff=io.BytesIO(b'')


#sio = io.TextIOWrapper(ser,  newline='\r')
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

def inwait(func): #decorator function for monitoring
    def wrapper(*args,**kwargs):
        func(*args, **kwargs)
        if debug == True and (ser.inWaiting() > 0):
            # if incoming bytes are waiting to be read from the serial input buffer
            data_str = ser.read(ser.inWaiting()).decode('ascii')
            buff.write(ser.read(ser.inWaiting()))
            print(data_str, end='')

    return wrapper

def sendcom(cmd=''):
    ser.write(cmd.encode())
    ser.write("\r\n".encode())

# def login():
#     for e in range(2):
#         sendcom()
#     ser.read_until(b"Enter password to activate Maintenance Menu :")
#     sendcom(b'admin')
#     ser.read_until(b"0 : Exit")
#     print('logged in')

def read_until(val=None):
    while True:
        line = str(ser.readline().decode('ascii'))
        if len(line) > 1:
            print(line)
        rev = re.search(val, line)
        if val and rev:
            return rev

def write(comm):
    print('Writing {}'.format(comm))
    ser.write(comm.encode())
    time.sleep(0.5)
    ser.write('\r\n'.encode())

def upgrade():
    ser.flushInput()
    #Booting - searching for revision
    while True:
        line = str(ser.readline().decode('ascii'))
        rev = re.search('Kitting revision : (\w+)', line)
        print(line)
        if rev:
            break
    print('~~~Network card found, revision {}~~~\n'.format(rev[1]))

    if rev[1] == 'LA':
        #put filename on tftp server for new revision NMC_EATON_JB_rp.bin
        copyfile(os.path.join(os.getcwd(), 'NMC_EATON_JB_rp.bin'),os.path.join(os.getcwd(),'TFTP-Root','image.bin'))
    else:
        # put filename on tftp server for OLD revision Network-Card-MS_Revision_JB.bin
        copyfile(os.path.join(os.getcwd(), 'Network-Card-MS_Revision_JB.bin'), os.path.join(os.getcwd(), 'TFTP-Root', 'image.bin'))

    #Waiting for upgrade mode
    read_until("To force the upgrade mode, type 'y', then press ENTER")
    write('y')
    print("~~~Wait 3 min until boot...~~~")
    read_until("Set the IP address :")
    write('192.168.1.2')
    read_until("Set the subnet mask address :")
    write('255.255.255.0')
    read_until("Set the gateway address :")
    write('0.0.0.0')
    read_until('Set the TFTP server IP address :')
    write('192.168.1.3')
    read_until()



if __name__ == "__main__":
    for file in os.listdir(os.path.join(os.getcwd(),'TFTP-Root')):
        os.remove(os.path.join(os.getcwd(),'TFTP-Root', file))
    port=serial_ports()[0]
    ser = serial.Serial(port,
                        timeout=30,
                        baudrate=9600,
                        xonxoff=0,
                        stopbits=1,
                        parity=serial.PARITY_NONE,
                        bytesize=8)
    print('Please connect bbu to {}, ethernet, plug in power cord and press Enter...'.format(port))
    input()
    upgrade()
    #command('tcpip')