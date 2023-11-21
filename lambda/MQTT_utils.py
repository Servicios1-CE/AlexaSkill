
from awscrt import mqtt, io #Librerias para comunicacion con AWS
import uuid                 #Libreria para genera ID unico del cliente MQTT

# Librerias necesarias para la ejecucion
import time

#Callback que se ejecuta si se interrumpe la conexion al AWS (no se ejecuta nada)
def on_connection_interrupted(connection, error, **kwargs):
    None

#Callback que se ejecuta cuando se reconecta al AWS (no se ejecuta nada)
def on_connection_resumed(connection, return_code, session_present, **kwargs):
    None

#Parametros necesarios para crear el cliente MQTT
event_loop_group = io.EventLoopGroup(1)
host_resolver = io.DefaultHostResolver(event_loop_group)
client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)

#Ubicacion de los archivos de certificados y claves del certificado asociado al Thing de IoT en AWS
root_ca = "MQTT/AmazonRootCA1.pem"
cert = "MQTT/certificate.pem.crt"
key = "MQTT/private.pem.key"

#ID unico del cliente
client = "alexa_skill_"+str(uuid.uuid4())

#Asociando los certificados y la clave privada a las opciones de TLS
tls_options = io.TlsContextOptions.create_client_with_mtls_from_path(cert, key)
with open(root_ca, mode='rb') as ca:
    rootca = ca.read()
    tls_options.override_default_trust_store(rootca)
    
#Generando el contexto TLS a partir de las opciones TLS
tls_context = io.ClientTlsContext(tls_options)

#Creando el objeto cliente MQTT
mqtt_client = mqtt.Client(client_bootstrap, tls_context)

"""
Creando el objeto de conexion MQTT con los siguiente parametros:
- Objeto Cliente MQTT
- Direccion del endpoint de AWS (Host Name)
- Puerto 8883
- ID unico del Cliente
- callback de conexion interrumpida
- callback de reconeccion
"""
mqtt_connection = mqtt.Connection(
            client=mqtt_client,
            host_name="a1uouo1ra6gx7j-ats.iot.us-west-2.amazonaws.com",
            port=8883,
            client_id=client,
            on_connection_interrupted=on_connection_interrupted,
            on_connection_resumed=on_connection_resumed)

#Diccionario de recepcion de mensajes
receive = {'flag':False} #Inicializa el flag de recepcion en Falso

#Callback de subscripcion
def callback(topic, payload, dup, qos, retain, **kwargs):
    global receive
    receive['topic'] = topic #Topico
    receive['message'] = payload.decode() #Mensaje
    receive['dup'] = dup #DUP Flag (no es utilizado)
    receive['qos'] = qos #Quality of Service (no se utiliza)
    receive['retain'] = retain #Flag de retencion (no se utiliza)
    receive['flag'] = True #Flag de recepcion 

#Conecta el cliente a AWS
#Retorna [‘session_present’ : True] si se esta resumiendo una sesion previa
#Retorna [‘session_present’ : True] si se esta iniciando una sesion nueva
def mqtt_connect():
    return mqtt_connection.connect().result()

#Deconecta el cliente a AWS
#Retorna un diccionario vacio
def mqtt_disconnect():
    return mqtt_connection.disconnect().result()

#Subscribe el cliente a un topico y ejecuta el callback dado
#Para ver lo que retorna, ir a https://awslabs.github.io/aws-crt-python/api/mqtt.html#awscrt.mqtt.Connection.subscribe
def mqtt_subscribe(TOPIC, sub_callback):
    qos = mqtt.QoS.AT_LEAST_ONCE
    subscribe_future, subscribe_packet_id = mqtt_connection.subscribe(
        topic=TOPIC,
        qos=qos,
        callback=sub_callback)
    return subscribe_future.result()

#Publica un mensaje a un topico
#Para ver lo que retorna, ir a https://awslabs.github.io/aws-crt-python/api/mqtt.html#awscrt.mqtt.Connection.publish
def mqtt_publish(TOPIC, MESSAGE):
    publish_future, publish_packet_id = mqtt_connection.publish(
        topic=TOPIC,
        payload=MESSAGE,
        qos=mqtt.QoS.AT_LEAST_ONCE)
    return publish_future.result()

class Subscription:
    def __init__(self, topic):
        self.sub_dic = {'flag':False}
        self.topic = topic
        
    def subscribe(self):
        mqtt_subscribe(self.topic, self.callback)
        
    def callback(self, topic, payload, dup, qos, retain, **kwargs):
        self.sub_dic['topic'] = topic #Topico
        self.sub_dic['message'] = payload.decode() #Mensaje
        self.sub_dic['dup'] = dup #DUP Flag (no es utilizado)
        self.sub_dic['qos'] = qos #Quality of Service (no se utiliza)
        self.sub_dic['retain'] = retain #Flag de retencion (no se utiliza)
        self.sub_dic['flag'] = True #Flag de recepcion 

def query(query_topic, query, reception_dic, confirmation_topic, confirmation, timeout=5):
    #Publica la solicitud de informacion
    mqtt_publish(query_topic, query)
    
    #Espera el flag de recepcion o timeout
    reception_dic['flag'] = False
    a = time.time()
    while not reception_dic['flag']:
        if time.time() - a > timeout:
            break
    
    if reception_dic['flag']:
        mqtt_publish(confirmation_topic, confirmation) #Envia confirmacion
        return reception_dic['message'] #Retorna el mensaje
    else:
        return "TIMEOUT" #Retorna timeout
    
def command(command_topic, command, confirmation_dic, timeout=5):
    #Publica el command_topic
    mqtt_publish(command_topic, command)
    
    #Espera el flag de confirmacion o timeout
    confirmation_dic['flag'] = False
    a = time.time()
    while not confirmation_dic['flag']:
        if time.time() - a > timeout:
            break
    
    return confirmation_dic['flag']
    
