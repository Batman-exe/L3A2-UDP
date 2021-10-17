import socket
import threading
import time
import datetime
import os

lock = threading.Lock()


def pedirDatos():
    fileName = ""
    fileExt = ""
    entry = int(input("Ingrese archivo que quiere enviar 1 (100 MB) o 2 (250MB)"))
    if entry == 1:
        fileName = "../files/100MB.txt"
        fileExt = ".txt"
    elif entry == 2:
        fileName = "../files/250MB.txt"
        fileExt = ".txt"
    entry = int(input("Ingrese el numero de clientes en simultaneo a enviar el archivo"))
    numClientes = entry
    return fileName, fileExt, numClientes


fileData = pedirDatos()
fileName = fileData[0]
numClientes = fileData[2]
fileExt = fileData[1]
c_clientes = 0
attend = False


def createLog():
    print("Creando log")

    # Fecha y hora --creacion log
    fecha = datetime.datetime.now()

    logName = "../Logs/Server/" + str(fecha.timestamp()) + "-log.txt"
    logFile = open(logName, "a")
    logFile.write("Fecha: " + str(fecha) + "\n")

    # Nombre del archivo enviado
    fileN = fileName.split("/")
    fileN = fileN[2]
    logFile.write("Nombre del archivo: " + fileN + "\n")

    # Tamanio del archivo enviado
    fSize = os.path.getsize(fileName)
    logFile.write("Tamanio del archivo: " + str(fSize) + " bytes\n")
    logFile.write("----------------------------------------\n")

    logFile.close()
    return logName


# Crear el archivo de log
logName = createLog()


def logDatosCliente(recepcion, tiempo, numPaqEnv, numPaqRec):
    with lock:
        paquetesE = "Numero de paquetes enviados por el servidor: " + str(numPaqEnv) + "\n"
        paquetesR = "Numero de paquetes recibidos por el cliente: " + str(numPaqRec) + "\n"
        tiempoT = "Tiempo: " + str(tiempo) + " segundos\n"
        separador = "\n=============================================\n"
        logFile = open(logName, "a")
        logFile.write(recepcion + "\n" + paquetesE + paquetesR + tiempoT + separador)
        logFile.close()


host = ""
BUFFER = 4096


def servidor(port1, dir):
    global c_clientes
    global attend
    port = 20001+port1
    s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

    # Bind to address and ip
    s.bind((host, port))
    s.sendto(str(port).encode(), dir)
    print("UDP server up and listening at port ", port)

    while True:
        data = s.recvfrom(BUFFER)
        msg = data[0]
        dir = data[1]

        print('Server received', msg.decode())

        if msg.decode() == "READY":
            c_clientes += 1
            print("Numero Clientes Conectados: ", c_clientes)
            while True:
                if c_clientes >= numClientes or attend:
                    print("Starting to send")
                    break
            attend = True
            i = 0

            s.sendto(fileExt.encode(), dir)

            time.sleep(0.01)

            inicioT = time.time()
            f = open(fileName, 'rb')
            while True:
                i += 1
                data = f.read(BUFFER)
                if not data:
                    break
                s.sendto(data, dir)
            print("Archivo Enviado")

            f.close()
            data = s.recvfrom(BUFFER)

            # Notificacion de recepcion
            datosCiente = data[0].decode().split("/")
            recepcion = datosCiente[1]
            print(recepcion)

            # Notificacion de tiempo
            finT = float(datosCiente[2])
            totalT = finT - inicioT

            # Numero de paquetes recibidos por el cliente
            paqRecv = datosCiente[0]

            logDatosCliente(recepcion, totalT, i, paqRecv)

            print('Fin envio')
            c_clientes -= 1
            print("Numero Clientes Conectados: ", c_clientes)

            # Notificacion de fin de cliente o no
            terminS = datosCiente[3]

            if terminS == "TERMINATE":
                print(terminS)
                s.close()
                print("Fin Server en puerto ", port)
                break


port1 = 20001
# TCP ------> socket.AF_INET, socket.SOCK_STREAM
# UDP ------> socket.AF_INET, socket.SOCK_DGRAM
s = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM)

# Bind to address and ip
s.bind((host, port1))
i = 1
while True:
    data = s.recvfrom(BUFFER)
    msg = data[0]
    dir = data[1]

    if msg.decode() == "REQUEST":
        if i == 26:
            i = 1
        t = threading.Thread(target=servidor, args=(i, dir))
        i += 1
        t.start()

    if msg.decode() == "END":
        print("FIN CONEXIONES")
        break
