import serial
import time
import io
import sys
import glob
import re
import os
from shutil import copyfile

debug = False
buff= io.BytesIO(b'')

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


def sendcom(cmd=''):
    ser.write(cmd.encode())
    ser.write("\r\n".encode())

def read_until(val,inval=None):
    while True:
        line = str(ser.readline().decode('ascii'))
        if len(line) > 1:
            if debug:
                print('>',line)
        if inval:
            invrev = re.search(inval, line)
        if inval and invrev:
            raise ConnectionError("Network card does not retrieved IP via DHCP and asks for manual IP address, please check your DHCP server configuration")
        rev = re.search(val, line)
        if val and rev:
            return rev

def write(comm):
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

def searchv(val):
    while True:
        line = str(ser.readline().decode('UTF-8'))
        rev = re.search('{} (\w+)'.format(val), line)
        if debug:
            print(line)
        if rev:
            return rev[1]

def upgrade():
    print('\n')
    input('Please connect bbu to COM port and network, plug in power cord and press any key...')
    print('\n')
    #Booting - searching for revision

    rev = searchv('Kitting revision :')
    sn = searchv('Serial number :')
    print('  > Network card {} found, revision {}'.format(sn, rev))

    if rev == 'LA':
        #put filename on tftp server for new revision NMC_EATON_JB_rp.bin
        copyfile(os.path.join(os.getcwd(), 'NMC_EATON_JB_rp.bin'),os.path.join(os.getcwd(),'TFTP-Root','image.bin'))
    else:
        # put filename on tftp server for OLD revision Network-Card-MS_Revision_JB.bin
        copyfile(os.path.join(os.getcwd(), 'Network-Card-MS_Revision_JB.bin'), os.path.join(os.getcwd(), 'TFTP-Root', 'image.bin'))

    #Waiting for upgrade mode
    read_until("To force the upgrade mode, type 'y', then press ENTER")
    write('y')
    print("  > Wait 1 min until boot...")
    # read_until("Set the IP address :")
    # write('192.168.1.2')
    # read_until("Set the subnet mask address :")
    # write('255.255.255.0')
    # read_until("Set the gateway address :")
    # write('0.0.0.0')
    read_until('Set the TFTP server IP address :',"Set the IP address :")
    print("  > Setting TFTP server IP address....")
    write('192.168.1.3')
    print("  > Working. DO NOT DISCONNECT BBU! Please wait...")
    read_until('Flashing done')
    print('  > Flashing done sucessfully.')
    print('~'*300)
    upgrade()

if __name__ == "__main__":
    for file in os.listdir(os.path.join(os.getcwd(),'TFTP-Root')):
        os.remove(os.path.join(os.getcwd(),'TFTP-Root', file))
    port=serial_ports()[0]
    ser = serial.Serial(port,
                        timeout=10,
                        baudrate=9600,
                        xonxoff=0,
                        stopbits=1,
                        parity=serial.PARITY_NONE,
                        bytesize=8)
    upgrade()