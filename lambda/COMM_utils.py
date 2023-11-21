# Libreria de MQTT simplificada
from MQTT_utils import *

PLC_ok = Subscription('PLC_ok')
PLC2Alexa = Subscription('PLC2Alexa')

def init_subs():
    PLC_ok.subscribe()
    PLC2Alexa.subscribe()

def BinCMD(dim1, comando):
    """
    dim1: Fila en el arreglo de matricial booleano (int) (0-99)
    comando: combinacion de comandos binarios (S,R,T,K) (string)
        S: Set
        R: Reset
        T: Toggle
        K: Keep
    """
    if dim1 > 9:
        message = '{"' + str(dim1) + '":"' + comando + '"}'
    else:
        message = '{"0' + str(dim1) + '":"' + comando + '"}'
    return command('BinCMD', message, PLC_ok.sub_dic)

def ValueCMD(datatype, dim1, dim2, data):
    """
    datatype: tipo de dato (INT, REAL, TIME) (string)
    dim1: Fila en el arreglo matricial del datatype (int)
    dim2: Columna en el arreglo matricial del datatype (int)
    data: valor a enviar (int, float, time string (00:00))
    """

    type_txt = datatype + '_' + ('0' if dim1 < 10 else '') + str(dim1) + '_' + ('0' if dim2 < 10 else '') + str(dim2)
    
    if datatype == "INT":
        data = int(data)
        message = '{"' + type_txt + '":"'+ str(data) +'"}' 
    
    elif datatype == "REAL":
        data = round(data, 4) # 4 cifras despues de punto
        
        message = '{"' + type_txt + '":"'+ str(data) + '0' * (4 - (len(str(data)) - len(str(int(data))) - 1)) +'"}' 
    
    elif datatype == "TIME":
        data = (int(data[0:2])*60 + int(data[3:5]))*60 # En segundos
        message = '{"' + type_txt + '":"'+ str(data) + '"}'
    
    else:
        return False
    
    return command('ValueCMD', message, PLC_ok.sub_dic)

def ListCMD(datatype, dim1, datos):
    """
    datatype: tipo de dato (INT, REAL, TIME) (string)
    dim1: Fila en el arreglo matricial del datatype (int)
    datos: lista de valores a enviar (int, float, time string (00:00)) (None donde no van datos)
    """
    
    type_txt = datatype + '_' + ('0' if dim1 < 10 else '') + str(dim1)
    
    if datatype == "INT":
        data = ""
        for n in datos:
            if n == None:
                data += 'K'
            else:
                data += str(int(n))
            data += ','
        
        data = data[0:len(data)-1]
        
        message = '{"' + type_txt + '":"'+ data +'"}' 
    
    elif datatype == "REAL":
        data = ""
        for n in datos:
            if n == None:
                data += 'K'
            else:
                num = round(n, 4)
                data += str(num) + '0' * (4 - (len(str(num)) - len(str(int(num))) - 1))
            data += ','
        
        data = data[0:len(data)-1]
        
        message = '{"' + type_txt + '":"'+ data +'"}' 
    
    elif datatype == "TIME":
        data = ""
        for n in datos:
            if n == None:
                data += 'K'
            else:
                data += str((int(n[0:2])*60 + int(n[3:5]))*60)
            data += ','
        
        data = data[0:len(data)-1]
        
        message = '{"' + type_txt + '":"'+ data +'"}' 
    
    else:
        return False
    
    return command('ListCMD', message, PLC_ok.sub_dic)

def DataReq(datatype, dim1, dim2):
    """
    datatype: tipo de dato (BOOL, INT, REAL, TIME) (string)
    dim1: Fila en el arreglo matricial del datatype (int)
    dim2: lista de valores a recolectar (columna en el arreglo matricial) (List Int)
    """
    type_txt = datatype + '_' + ('0' if dim1 < 10 else '') + str(dim1)
    
    data = ""
    for n in dim2:
        data += ('0' if n < 10 else '') + str(n)
        data += ','
    
    data = data[0:len(data)-1]
    message = '{"' + type_txt + '":"'+ data +'"}' 
    
    response = query('DataReq', message, PLC2Alexa.sub_dic, 'Alexa_ok', "{\"ok\":\"1\"}")
    
    if response == "TIMEOUT":
        return response
        
    elif datatype == 'BOOL':
        data = []
        for n in response[13:len(response)-2]:
            data.append(n == '1')
            if n != '1' and n != '0':
                return "DATAERROR"
        
        if len(data) == 1:
            data = data[0]
    
    elif datatype == 'INT':
        data = []
        response = response[16:len(response)-2]
        
        for n in response.split(','):
            data.append(int(n))
        
        if len(data) == 1:
            data = data[0]
        
    elif datatype == 'REAL':
        data = []
        response = response[16:len(response)-2]
        
        for n in response.split(','):
            data.append(float(n))
        
        if len(data) == 1:
            data = data[0]
    
    elif datatype == 'TIME':
        data = []
        response = response[16:len(response)-2]
        
        for n in response.split(','):
            sec = int(n)
            minute = sec // 60
            hour = minute // 60
            minute = minute % 60
            hour = ('0' if hour <= 9 else '') + str(hour)
            minute = ('0' if minute <= 9 else '') + str(minute)
            data.append(hour + ":" + minute)
        
        if len(data) == 1:
            data = data[0]
    
    else:
        return "DATAERROR"
    
    return data
        
    
    
    
    