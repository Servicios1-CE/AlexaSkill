# -*- coding: utf-8 -*-

#Libreria de utilizades
from utils import *

# Libreria de herramientas de comunicacion
from COMM_utils import *

#LOGGER para DEBUGGING
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
logger.info(client)
test_sub = Subscription('test')


#Clase de Ejecucion de Skill
class LaunchRequestHandler(AbstractRequestHandler):
    """Handler for Skill Launch."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        #Verifica que es el Request del Launch
        return ask_utils.is_request_type("LaunchRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("Launched START")
        #Conexion a MQTT en el Launch
        mqtt_connect()
        
        #Publica en el topico de Log (verifica la conexion a MQTT)
        mqtt_publish('log',"{\"Log\":\"Started Equipo 170\"}")
        
        #Inicializa las subscripciones a los topicos
        init_subs()
        
        #Variables globales de la sesion
        session_attributes = handler_input.attributes_manager.session_attributes
        session_attributes["ACCESS"] = 0 #Nivel de acceso
        session_attributes["ESCALA"] = 'C'
        session_attributes["RELOAD"] = 0
        
        #Prueba del habla
        session_attributes["Started"] = False
        
        speak_output =  f"Sistema de Control por Voz. " \
                        f"Planta de cuatro estaciones. " \
                        f"Diga el comando que desee ejecutar." 

        # Alexa Presentation Language (APL) template (Herramientas visuales (title-subtitle)
        alexa_APL(handler_input, 'Sistema de Control por Voz', 'Diga su usuario y su pin de acceso')
        logger.info("Launched ENDED")
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class SystemAccessHandler(AbstractRequestHandler):
    """Handler for Acceder a funciones de modificacion del sistema."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("SystemAccess")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        
        #Variables globales de la sesion
        session_attributes = handler_input.attributes_manager.session_attributes
        
        #Revisar si la sesion ya tiene acceso
        if session_attributes["ACCESS"] == 0:
            
            #Datos provisto por el usuario
            user_type = ask_utils.request_util.get_slot(handler_input, "user").value
            user_pin = ask_utils.request_util.get_slot(handler_input, "pin").value
            user_pin = int(user_pin)
            
            #PIN del sistema
            if user_type == "monitor":
                plc_pin = DataReq('INT', 1, [0])
                session_attributes["ACCESS"] = 1
            elif user_type == "mantenimiento":
                plc_pin = DataReq('INT', 1, [1])
                session_attributes["ACCESS"] = 2
            elif user_type == "total":
                plc_pin = DataReq('INT', 1, [2])
                session_attributes["ACCESS"] = 3
            else:
                plc_pin = None
                
            
            if plc_pin in ["TIMEOUT", "DATAERROR"]:
                #Error de comunicacion
                session_attributes["ACCESS"] = 0
                speak_output = "Ha ocurrido un problema de comunicación, revise la conexión del PLC con la nube"
                alexa_APL(handler_input, 'Problema de conexión', 'Revise el PLC')
            elif plc_pin == user_pin:
                #Acceso concedido
                speak_output = "Su pin de seguridad ha sido validado."
                alexa_APL(handler_input, 'Sistema de Control por Voz', 'Ejecute un comando')
            elif plc_pin == None:
                #Acceso denegado
                session_attributes["ACCESS"] = 0
                speak_output = "El usuario dado no existe. Intente de nuevo."
                alexa_APL(handler_input, 'Acceso', 'Denegado')
            else:
                #Acceso denegado
                session_attributes["ACCESS"] = 0
                speak_output = "El pin ingresado no coincide con el pin de seguridad. Intente de nuevo."
                alexa_APL(handler_input, 'Acceso', 'Denegado')
            
        else:
            #Ya tiene Acceso
            speak_output = "Esta sesión ya fue iniciada"
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class LightActionHandler(AbstractRequestHandler):
    """Handler for Encender o Apagar luces."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("LightAction")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        
        #Variables globales de la sesion
        session_attributes = handler_input.attributes_manager.session_attributes
        
        #Revisar si la sesion tiene acceso
        if session_attributes["ACCESS"] >= 3:
            
            #Datos provistos por el usuario
            accion = ask_utils.request_util.get_slot(handler_input, "accion").value
            if accion in ['deshabilita', 'bloquear', 'deshabilitar', 'desactivar', 'apagar', 'bloquea', 'desactiva', 'apaga', 'off', 'tumba', 'tumbar']:
                accion = 'OFF'
            elif accion in ['encender', 'desbloquear', 'activar', 'habilitar', 'habilita', 'desbloquea', 'activa', 'enciende', 'on', 'prende', 'prender']:
                accion = 'ON'
            
            estacion = ask_utils.request_util.get_slot(handler_input, "estacion").value
            estacion = int(estacion)
            
            estacion2 = ask_utils.request_util.get_slot(handler_input, "estacion_dos").value
            estacion2 = estacion2 if estacion2 == None else int(estacion2)
                
            estacion3 = ask_utils.request_util.get_slot(handler_input, "estacion_tres").value
            estacion3 = estacion3 if estacion3 == None else int(estacion3)
            
            estacion4 = ask_utils.request_util.get_slot(handler_input, "estacion_cuatro").value
            estacion4 = estacion4 if estacion4 == None else int(estacion4)
            
            estaciones_txt = str(estacion if estacion != None else '') 
            estaciones_txt += str(estacion2 if estacion2 != None else '')
            estaciones_txt += str(estacion3 if estacion3 != None else '')
            estaciones_txt += str(estacion4 if estacion4 != None else '')
            
            #Toma los digitos de las estaciones dados
            estaciones = []
            for n in estaciones_txt:
                estaciones.append(int(n))
            
            #Ordena la lista de estaciones
            estaciones.sort()
            
            #comando binario
            comando = "KKKKKKKK"
            for i in range(len(estaciones)):
                comando = str_replace(comando, ('S' if accion == "ON" else 'R'), estaciones[i] - 1)
                
            success = BinCMD(3, comando)
            
            if success:
                #Accion completada
                if len(estaciones) == 1:
                    speak_output = f"La luz de la estación {estacion} se ha " + ("encendido" if accion == "ON" else "apagado")
                elif len(estaciones) == 2:
                    speak_output = f"Las luces de las estaciones {estaciones[0]} y {estaciones[1]} se han " + ("encendido" if accion == "ON" else "apagado")
                elif len(estaciones) == 3:
                    speak_output = f"Las luces de las estaciones {estaciones[0]}, {estaciones[1]} y {estaciones[2]} se han " + ("encendido" if accion == "ON" else "apagado")
                else:
                    speak_output = f"Las luces de las estaciones 1, 2, 3 y 4 se han " + ("encendido" if accion == "ON" else "apagado")
                alexa_APL(handler_input, 'Sistema de Control por Voz', 'Ejecute un comando')
            else:
                #Error de comunicacion
                speak_output = "Ha ocurrido un problema de comunicación, revise la conexión del PLC con la nube"
                alexa_APL(handler_input, 'Problema de conexión', 'Revise el PLC')
            
        elif session_attributes["ACCESS"] > 0:
            #No tiene acceso
            speak_output = "Este usuario no puede acceder a esta función. Necesita mayor nivel de permisos."
            alexa_APL(handler_input, 'Sistema de Control por Voz', 'Ejecute un comando')
        
        else:
            #No tiene acceso
            speak_output = "Esta sesión no está iniciada. Para habilitar esta función, ingrese su usuario y pin de seguridad."
            alexa_APL(handler_input, 'Sistema de Control por Voz', 'Diga su usuario y su pin de acceso')
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class StationActionHandler(AbstractRequestHandler):
    """Handler for Habilitar o Deshabilitar estaciones."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("StationAction")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        
        #Variables globales de la sesion
        session_attributes = handler_input.attributes_manager.session_attributes
        
        #Revisar si la sesion tiene acceso
        if session_attributes["ACCESS"] >= 2:
            
            #Datos provistos por el usuario
            accion = ask_utils.request_util.get_slot(handler_input, "accion").value
            if accion in ['deshabilita', 'bloquear', 'deshabilitar', 'desactivar', 'apagar', 'bloquea', 'desactiva', 'apaga', 'off', 'tumba', 'tumbar']:
                accion = 'OFF'
            elif accion in ['encender', 'desbloquear', 'activar', 'habilitar', 'habilita', 'desbloquea', 'activa', 'enciende', 'on', 'prende', 'prender']:
                accion = 'ON'
                
            estacion = ask_utils.request_util.get_slot(handler_input, "estacion").value
            estacion = int(estacion)
            
            estacion2 = ask_utils.request_util.get_slot(handler_input, "estacion_dos").value
            estacion2 = estacion2 if estacion2 == None else int(estacion2)
                
            estacion3 = ask_utils.request_util.get_slot(handler_input, "estacion_tres").value
            estacion3 = estacion3 if estacion3 == None else int(estacion3)
            
            estacion4 = ask_utils.request_util.get_slot(handler_input, "estacion_cuatro").value
            estacion4 = estacion4 if estacion4 == None else int(estacion4)
            
            estaciones_txt = str(estacion if estacion != None else '') 
            estaciones_txt += str(estacion2 if estacion2 != None else '')
            estaciones_txt += str(estacion3 if estacion3 != None else '')
            estaciones_txt += str(estacion4 if estacion4 != None else '')
            
            #Toma los digitos de las estaciones dados
            estaciones = []
            for n in estaciones_txt:
                estaciones.append(int(n))
            
            #Ordena la lista de estaciones
            estaciones.sort()
            
            #comando binario
            comando = "KKKKKKKK"
            for i in range(len(estaciones)):
                comando = str_replace(comando, ('S' if accion == "ON" else 'R'), estaciones[i] - 1)
                
            success = BinCMD(5, comando)
            
            if success:
                #Accion completada
                if len(estaciones) == 1:
                    speak_output = f"La estación {estacion} se ha " + ("habilitado" if accion == "ON" else "deshabilitado")
                elif len(estaciones) == 2:
                    speak_output = f"La estaciones {estaciones[0]} y {estaciones[1]} se han " + ("habilitado" if accion == "ON" else "deshabilitado")
                elif len(estaciones) == 3:
                    speak_output = f"La estaciones {estaciones[0]}, {estaciones[1]} y {estaciones[2]} se han " + ("habilitado" if accion == "ON" else "deshabilitado")
                else:
                    speak_output = f"La estaciones 1, 2, 3 y 4 se han " + ("habilitado" if accion == "ON" else "deshabilitado")
                
                alexa_APL(handler_input, 'Sistema de Control por Voz', 'Ejecute un comando')
            else:
                #Error de comunicacion
                speak_output = "Ha ocurrido un problema de comunicación, revise la conexión del PLC con la nube"
                alexa_APL(handler_input, 'Problema de conexión', 'Revise el PLC')
            
        elif session_attributes["ACCESS"] > 0:
            #No tiene acceso
            speak_output = "Este usuario no puede acceder a esta función. Necesita mayor nivel de permisos."
            alexa_APL(handler_input, 'Sistema de Control por Voz', 'Ejecute un comando')
        
        else:
            #No tiene acceso
            speak_output = "Esta sesión no está iniciada. Para habilitar esta función, ingrese su usuario y pin de seguridad."
            alexa_APL(handler_input, 'Sistema de Control por Voz', 'Diga su usuario y su pin de acceso')
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class AllLightsEventHandler(AbstractRequestHandler):
    """Handler for Encender o Apagar luces."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AllLightsEvent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        
        #Variables globales de la sesion
        session_attributes = handler_input.attributes_manager.session_attributes
        
        #Revisar si la sesion tiene acceso
        if session_attributes["ACCESS"] >= 3:
            
            #Datos provistos por el usuario
            accion = ask_utils.request_util.get_slot(handler_input, "accion").value
            if accion in ['deshabilita', 'bloquear', 'deshabilitar', 'desactivar', 'apagar', 'bloquea', 'desactiva', 'apaga', 'off', 'tumba', 'tumbar']:
                accion = 'OFF'
            elif accion in ['encender', 'desbloquear', 'activar', 'habilitar', 'habilita', 'desbloquea', 'activa', 'enciende', 'on', 'prende', 'prender']:
                accion = 'ON'
            
            #comando binario
            comando = ('S' if accion == "ON" else 'R')*4 + "KKKK"
            success = BinCMD(3, comando)
            
            if success:
                #Accion completada
                speak_output = "Todas las luces se han " + ("encendido" if accion == "ON" else "apagado")
                alexa_APL(handler_input, 'Sistema de Control por Voz', 'Ejecute un comando')
            else:
                #Error de comunicacion
                speak_output = "Ha ocurrido un problema de comunicación, revise la conexión del PLC con la nube"
                alexa_APL(handler_input, 'Problema de conexión', 'Revise el PLC')
            
        elif session_attributes["ACCESS"] > 0:
            #No tiene acceso
            speak_output = "Este usuario no puede acceder a esta función. Necesita mayor nivel de permisos."
            alexa_APL(handler_input, 'Sistema de Control por Voz', 'Ejecute un comando')
        
        else:
            #No tiene acceso
            speak_output = "Esta sesión no está iniciada. Para habilitar esta función, ingrese su usuario y pin de seguridad."
            alexa_APL(handler_input, 'Sistema de Control por Voz', 'Diga su usuario y su pin de acceso')
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class AllEnableEventHandler(AbstractRequestHandler):
    """Handler for Encender o Apagar luces."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AllEnableEvent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        
        #Variables globales de la sesion
        session_attributes = handler_input.attributes_manager.session_attributes
        
        #Revisar si la sesion tiene acceso
        if session_attributes["ACCESS"] >= 2:
            
            #Datos provistos por el usuario
            accion = ask_utils.request_util.get_slot(handler_input, "accion").value
            if accion in ['deshabilita', 'bloquear', 'deshabilitar', 'desactivar', 'apagar', 'bloquea', 'desactiva', 'apaga', 'off', 'tumba', 'tumbar']:
                accion = 'OFF'
            elif accion in ['encender', 'desbloquear', 'activar', 'habilitar', 'habilita', 'desbloquea', 'activa', 'enciende', 'on', 'prende', 'prender']:
                accion = 'ON'
            
            #comando binario
            comando = ('S' if accion == "ON" else 'R')*4 + "KKKK"
            success = BinCMD(5, comando)
            
            if success:
                #Accion completada
                speak_output = "Todas las estaciones se han " + ("habilitado" if accion == "ON" else "deshabilitado")
                alexa_APL(handler_input, 'Sistema de Control por Voz', 'Ejecute un comando')
            else:
                #Error de comunicacion
                speak_output = "Ha ocurrido un problema de comunicación, revise la conexión del PLC con la nube"
                alexa_APL(handler_input, 'Problema de conexión', 'Revise el PLC')
            
        elif session_attributes["ACCESS"] > 0:
            #No tiene acceso
            speak_output = "Este usuario no puede acceder a esta función. Necesita mayor nivel de permisos."
            alexa_APL(handler_input, 'Sistema de Control por Voz', 'Ejecute un comando')
        
        else:
            #No tiene acceso
            speak_output = "Esta sesión no esta iniciada. Para habilitar esta función, ingrese su usuario y pin de seguridad."
            alexa_APL(handler_input, 'Sistema de Control por Voz', 'Diga su usuario y su pin de acceso')
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class StationStateHandler(AbstractRequestHandler):
    """Handler for Ver el estado de las estaciones."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("StationState")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        
        #Variables globales de la sesion
        session_attributes = handler_input.attributes_manager.session_attributes
        
        if session_attributes["ACCESS"] > 0:
            #Datos provistos por el usuario
            estacion = ask_utils.request_util.get_slot(handler_input, "estacion").value
            estacion = int(estacion)
            
            #Data Request
            index = estacion - 1
            response = DataReq('BOOL', 5, [index, index+4])
            
            #Si la respuesta es una lista
            if type(response) == type([]):
                #Datos adquiridos
                speak_output = f"La estación {estacion} está " + ("encendida" if response[1] else "apagada") + " y " + ("habilitada" if response[0] else "bloqueada")
                alexa_APL(handler_input, 'Sistema de Control por Voz', 'Ejecute un comando')
            else:
                #Error de comunicacion
                speak_output = "Ha ocurrido un problema de comunicación, revise la conexión del PLC con la nube"
                alexa_APL(handler_input, 'Problema de conexión', 'Revise el PLC')
                
        else:
            #No tiene acceso
            speak_output = "Esta sesión no esta iniciada. Para habilitar esta función, ingrese su usuario y pin de seguridad."
            alexa_APL(handler_input, 'Sistema de Control por Voz', 'Diga su usuario y su pin de acceso')

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class ProductionSpeedHandler(AbstractRequestHandler):
    """Handler for Ver la velocidad de produccion de las estaciones."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("ProductionSpeed")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        
        #Variables globales de la sesion
        session_attributes = handler_input.attributes_manager.session_attributes
        
        if session_attributes["ACCESS"] > 0:
            #Datos provistos por el usuario
            estacion = ask_utils.request_util.get_slot(handler_input, "estacion").value
            estacion = int(estacion)
            
            #Data Request
            index = estacion - 1
            response = DataReq('INT', 0, [index])
            
            #Si la respuesta es valida
            if response not in ["TIMEOUT", "DATAERROR"]:
                #Datos adquiridos
                speak_output = f"La estación {estacion} está produciendo a {response} unidades por minuto"
                alexa_APL(handler_input, 'Sistema de Control por Voz', 'Ejecute un comando')
            else:
                #Error de comunicacion
                speak_output = "Ha ocurrido un problema de comunicación, revise la conexión del PLC con la nube."
                alexa_APL(handler_input, 'Problema de conexión', 'Revise el PLC')
        
        else:
            #No tiene acceso
            speak_output = "Esta sesión no esta iniciada. Para habilitar esta función, ingrese su usuario y pin de seguridad."
            alexa_APL(handler_input, 'Sistema de Control por Voz', 'Diga su usuario y su pin de acceso')

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class TemperatureReadHandler(AbstractRequestHandler):
    """Handler for Ver la temperatura actual."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("TemperatureRead")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        
        #Variables globales de la sesion
        session_attributes = handler_input.attributes_manager.session_attributes
        
        if session_attributes["ACCESS"] > 0:
            #Datos provistos por el usuario
            escala = ask_utils.request_util.get_slot(handler_input, "escala").value
            
            if escala != None:
                escala = escala.lower()
            
            #Escala de temperatura
            if escala in ['grados centigrados','grados celsius','centigrados','celsius']:
                session_attributes["ESCALA"] = 'C'
            elif escala in ['grados farenheit','farenheit','grados fahrenheit','fahrenheit']:
                session_attributes["ESCALA"] = 'F'
            elif escala in ['grados absolutos','absolutos','kelvin']:
                session_attributes["ESCALA"] = 'K'
                
            escala = session_attributes["ESCALA"]
            
            #Data Request
            response = DataReq('REAL', 0, [0])
            
            
            #Si la respuesta es valida
            if response not in ["TIMEOUT", "DATAERROR"]:
                #Datos adquiridos
                if escala == 'F':
                    T = (response * 9/5) + 32
                    escala = "grados Fahrenheit"
                elif escala == 'K':
                    T = response + 273.15
                    escala = "Kelvin"
                else:
                    T = response
                    escala = "grados Celsius"
                
                speak_output = f"La temperatura actual es {T} " + escala
                alexa_APL(handler_input, 'Sistema de Control por Voz', 'Ejecute un comando')
                
            else:
                #Error de comunicacion
                speak_output = "Ha ocurrido un problema de comunicación, revise la conexión del PLC con la nube"
                alexa_APL(handler_input, 'Problema de conexión', 'Revise el PLC')
                
        else:
            #No tiene acceso
            speak_output = "Esta sesión no esta iniciada. Para habilitar esta función, ingrese su usuario y pin de seguridad."
            alexa_APL(handler_input, 'Sistema de Control por Voz', 'Diga su usuario y su pin de acceso')
            
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class TempSetpointGetHandler(AbstractRequestHandler):
    """Handler for Ver la temperatura actual."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("TempSetpointGet")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        
        #Variables globales de la sesion
        session_attributes = handler_input.attributes_manager.session_attributes
        
        if session_attributes["ACCESS"] >= 2:
            #Datos provistos por el usuario
            escala = ask_utils.request_util.get_slot(handler_input, "escala").value
            
            if escala != None:
                escala = escala.lower()
            
            #Escala de temperatura
            if escala in ['grados centigrados','grados celsius','centigrados','celsius']:
                session_attributes["ESCALA"] = 'C'
            elif escala in ['grados farenheit','farenheit','grados fahrenheit','fahrenheit']:
                session_attributes["ESCALA"] = 'F'
            elif escala in ['grados absolutos','absolutos','kelvin']:
                session_attributes["ESCALA"] = 'K'
                
            escala = session_attributes["ESCALA"]
            
            #Data Request
            response = DataReq('REAL', 0, [1])
            
            #Si la respuesta es valida
            if response not in ["TIMEOUT", "DATAERROR"]:
                #Datos adquiridos
                if escala == 'F':
                    T = (response * 9/5) + 32
                    escala = "grados Fahrenheit"
                elif escala == 'K':
                    T = response + 273.15
                    escala = "Kelvin"
                else:
                    T = response
                    escala = "grados Celsius"
                
                speak_output = f"La temperatura está configurada a {T} " + escala
                alexa_APL(handler_input, 'Sistema de Control por Voz', 'Ejecute un comando')
                
            else:
                #Error de comunicacion
                speak_output = "Ha ocurrido un problema de comunicación, revise la conexión del PLC con la nube"
                alexa_APL(handler_input, 'Problema de conexión', 'Revise el PLC')
                
        elif session_attributes["ACCESS"] > 0:
            #No tiene acceso
            speak_output = "Este usuario no puede acceder a esta función. Necesita mayor nivel de permisos."
            alexa_APL(handler_input, 'Sistema de Control por Voz', 'Ejecute un comando')
            
        else:
            #No tiene acceso
            speak_output = "Esta sesión no esta iniciada. Para habilitar esta función, ingrese su usuario y pin de seguridad."
            alexa_APL(handler_input, 'Sistema de Control por Voz', 'Diga su usuario y su pin de acceso')
            
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class TemperatureSetHandler(AbstractRequestHandler):
    """Handler for Configurar el setpoint de temperatura."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("TemperatureSet")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        
        #Variables globales de la sesion
        session_attributes = handler_input.attributes_manager.session_attributes
        
        #Revisar si la sesion tiene acceso
        if session_attributes["ACCESS"] >= 2:
            
            #Datos provistos por el usuario
            escala = ask_utils.request_util.get_slot(handler_input, "escala").value
            if escala != None:
                escala = escala.lower()
            
            temperatura = ask_utils.request_util.get_slot(handler_input, "temperatura").value
            temperatura = float(temperatura)

            #Escala de temperatura
            if escala in ['grados centigrados','grados celsius','centigrados','celsius']:
                session_attributes["ESCALA"] = 'C'
            elif escala in ['grados farenheit','farenheit','grados fahrenheit','fahrenheit']:
                session_attributes["ESCALA"] = 'F'
            elif escala in ['grados absolutos','absolutos','kelvin']:
                session_attributes["ESCALA"] = 'K'
                
            escala = session_attributes["ESCALA"]
            
            if escala == 'F':
                T = (temperatura - 32) * 5/9
                escala = "grados Fahrenheit"
            elif escala == 'K':
                T = temperatura - 273.15
                escala = "Kelvin"
            else:
                T = temperatura
                escala = "grados Celsius"
                
            #Data Request
            success = ValueCMD('REAL', 0, 1, T)
            
            #Si la respuesta es valida
            if success:
                speak_output = f"La temperatura ha sido configurada a {temperatura} " + escala
                alexa_APL(handler_input, 'Sistema de Control por Voz', 'Ejecute un comando')
            else:
                #Error de comunicacion
                speak_output = "Ha ocurrido un problema de comunicación, revise la conexión del PLC con la nube"
                alexa_APL(handler_input, 'Problema de conexión', 'Revise el PLC')
            
        elif session_attributes["ACCESS"] > 0:
            #No tiene acceso
            speak_output = "Este usuario no puede acceder a esta función. Necesita mayor nivel de permisos."
            alexa_APL(handler_input, 'Sistema de Control por Voz', 'Ejecute un comando')
            
        else:
            #No tiene acceso
            speak_output = "Esta sesión no esta iniciada. Para habilitar esta función, ingrese su usuario y pin de seguridad."
            alexa_APL(handler_input, 'Sistema de Control por Voz', 'Diga su usuario y su pin de acceso')
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class TimeEventHandler(AbstractRequestHandler):
    """Handler for Encender o Apagar luces."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("TimeEvent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        
        #Variables globales de la sesion
        session_attributes = handler_input.attributes_manager.session_attributes
        
        #Revisar si la sesion tiene acceso
        if session_attributes["ACCESS"] >= 3:
            
            #Datos provistos por el usuario
            evento = ask_utils.request_util.get_slot(handler_input, "evento").value
            if evento in ['encendido','apertura','on']:
                evento = 'ON'
            elif evento in ['apagado','cierre','off']:
                evento = 'OFF'
            
            hora = ask_utils.request_util.get_slot(handler_input, "hora").value
            
            #comando de valor
            index = 0 if evento == "ON" else 1
            success = ValueCMD('TIME', 0, index, hora)
            
            if success:
                #Accion completada
                accion = "apertura" if evento == "ON" else "cierre"
                speak_output = f"La hora de {accion} se ha configurado a las {hora}"
                alexa_APL(handler_input, 'Sistema de Control por Voz', 'Ejecute un comando')
            else:
                #Error de comunicacion
                speak_output = "Ha ocurrido un problema de comunicación, revise la conexión del PLC con la nube"
                alexa_APL(handler_input, 'Problema de conexión', 'Revise el PLC')
            
        elif session_attributes["ACCESS"] > 0:
            #No tiene acceso
            speak_output = "Este usuario no puede acceder a esta función. Necesita mayor nivel de permisos."
            alexa_APL(handler_input, 'Sistema de Control por Voz', 'Ejecute un comando')
            
        else:
            #No tiene acceso
            speak_output = "Esta sesión no esta iniciada. Para habilitar esta función, ingrese su pin de seguridad."
            alexa_APL(handler_input, 'Sistema de Control por Voz', 'Diga su usuario y su pin de acceso')
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class GetTimeEventHandler(AbstractRequestHandler):
    """Handler for Ver la temperatura actual."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("GetTimeEvents")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        
        #Variables globales de la sesion
        session_attributes = handler_input.attributes_manager.session_attributes
        
        if session_attributes["ACCESS"] >= 3:
            #Datos provistos por el usuario
            evento = ask_utils.request_util.get_slot(handler_input, "evento").value
            evento2 = ask_utils.request_util.get_slot(handler_input, "evento_opt").value
            
            if evento in ['encendido','apertura','on']:
                evento = 'ON'
            elif evento in ['apagado','cierre','off']:
                evento = 'OFF'
                
            if evento2 in ['encendido','apertura','on']:
                evento2 = 'ON'
            elif evento2 in ['apagado','cierre','off']:
                evento2 = 'OFF'
            
            #Data Request
            response = DataReq('TIME', 0, [0, 1])
            
            
            #Si la respuesta es valida
            if type(response) == type([]):
                #Datos adquiridos
                if evento2 != None:
                    speak_output = f"La hora de apertura es a las {response[0]} y la hora de cierre es a las {response[1]}"
                elif evento == 'ON':
                    speak_output = f"La hora de apertura es a las {response[0]}"
                elif evento == 'OFF':
                    speak_output = f"La hora de cierre es a las {response[1]}"
                alexa_APL(handler_input, 'Sistema de Control por Voz', 'Ejecute un comando')
            else:
                #Error de comunicacion
                speak_output = "Ha ocurrido un problema de comunicación, revise la conexión del PLC con la nube"
                alexa_APL(handler_input, 'Problema de conexión', 'Revise el PLC')
                
        elif session_attributes["ACCESS"] > 0:
            #No tiene acceso
            speak_output = "Este usuario no puede acceder a esta función. Necesita mayor nivel de permisos."
            alexa_APL(handler_input, 'Sistema de Control por Voz', 'Ejecute un comando')
            
        else:
            #No tiene acceso
            speak_output = "Esta sesión no esta iniciada. Para habilitar esta función, ingrese su usuario y pin de seguridad."
            alexa_APL(handler_input, 'Sistema de Control por Voz', 'Diga su usuario y su pin de acceso')

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class ChangePINHandler(AbstractRequestHandler):
    """Handler for cambiar PIN de seguridad."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("ChangePIN")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        
        #Variables globales de la sesion
        session_attributes = handler_input.attributes_manager.session_attributes
        
        #Revisar si la sesion tiene acceso
        if session_attributes["ACCESS"] > 0:
            
            #Datos provistos por el usuario
            actual = ask_utils.request_util.get_slot(handler_input, "actual").value
            nuevo = ask_utils.request_util.get_slot(handler_input, "nuevo").value
            actual = int(actual)
            nuevo = int(nuevo)
            
            #PIN del sistema
            plc_pin = DataReq('INT', 1, [session_attributes["ACCESS"] - 1])
            
            if plc_pin in ["TIMEOUT", "DATAERROR"]:
                #Error de comunicacion
                speak_output = "Ha ocurrido un problema de comunicación, revise la conexión del PLC con la nube"
                alexa_APL(handler_input, 'Problema de conexión', 'Revise el PLC')
                
            elif plc_pin == actual:
                #Acceso concedido
                success = ValueCMD('INT', 1, session_attributes["ACCESS"] - 1, nuevo)
                if success:
                    #Accion completada
                    speak_output = "Se ha actualizado el PIN de seguridad"
                    alexa_APL(handler_input, 'Sistema de Control por Voz', 'Ejecute un comando')
                else:
                    #Error de comunicacion
                    speak_output = "Ha ocurrido un problema de comunicación, revise la conexión del PLC con la nube"
                    alexa_APL(handler_input, 'Problema de conexión', 'Revise el PLC')
                    
            else:
                #Acceso denegado
                session_attributes["ACCESS"] = False
                speak_output = "El pin ingresado no coincide con el pin de seguridad. Intente de nuevo."
                alexa_APL(handler_input, 'Sistema de Control por Voz', 'Ejecute un comando')
                
        else:
            #No tiene acceso
            speak_output = "Esta sesión no esta iniciada. Para habilitar esta función, ingrese su pin de seguridad."
            alexa_APL(handler_input, 'Sistema de Control por Voz', 'Diga su usuario y su pin de acceso')
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class GeneralReportHandler(AbstractRequestHandler):
    """Handler for Ver el estado de las estaciones."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("GeneralReport")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        
        #Variables globales de la sesion
        session_attributes = handler_input.attributes_manager.session_attributes
        
        if session_attributes["ACCESS"] >= 2:
            #Variable de exito de comunicacion
            success = True
            
            #Data Requests
            #Luces
            if success:
                luces = DataReq('BOOL', 3, [0, 1, 2, 3])
                success = type(luces) == type([]) #Verificacion de exito de comunicacion
            
            #Habilitadores
            if success:
                enables = DataReq('BOOL', 5, [0, 1, 2, 3])
                success = type(enables) == type([]) #Verificacion de exito de comunicacion
            
            #Estados
            if success:
                estados = DataReq('BOOL', 5, [4, 5, 6, 7])
                success = type(estados) == type([]) #Verificacion de exito de comunicacion
            
            #Velocidades
            if success:
                speeds = DataReq('INT', 0, [0, 1, 2, 3])
                success = type(speeds) == type([]) #Verificacion de exito de comunicacion
            
            #Temperaturas
            if success:
                temps = DataReq('REAL', 0, [0, 1])
                success = type(temps) == type([]) #Verificacion de exito de comunicacion
                escala = session_attributes["ESCALA"]
                    
                if escala == 'F':
                    
                    T1 = (temps[0] * 9/5) + 32
                    T2 = (temps[1] * 9/5) + 32
                    escala = "grados Fahrenheit"
                elif escala == 'K':
                    T1 = temps[0] + 273.15
                    T2 = temps[1] + 273.15
                    escala = "Kelvin"
                else:
                    T1 = temps[0]
                    T2 = temps[1]
                    escala = "grados Celsius"
            
            #TimeEvents
            if success:
                tiempos = DataReq('TIME', 0, [0, 1])
                success = type(tiempos) == type([]) #Verificacion de exito de comunicacion
            
            if success:
                #Datos adquiridos
                station = ["","","",""]
                
                #Resumen de las estaciones
                for i in range(4):
                    luz = "encendida" if luces[i] else "apagada"
                    enable = "habilitada" if enables[i] else "bloqueada"
                    estado  = "encendida" if estados[i] else "apagada"
                    speed = speeds[i]
                    n = i + 1
                    station[i] = f"La estación {n} está {estado}, está {enable}, tiene su luz {luz}, y está produciendo {speed} unidades por minuto. "
                    
                #Otros Datos
                others = f"La temperatura ambiente es de {T1} {escala}. La temperatura está configurada a {T2} {escala}. La hora de apertura es a las {tiempos[0]} y la hora de cierre es a las {tiempos[1]}."
                
                #Respuesta
                speak_output = station[0] + station[1] + station[2] + station[3] + others
                alexa_APL(handler_input, 'Sistema de Control por Voz', 'Ejecute un comando')
                
            else:
                #Error de comunicacion
                speak_output = "Ha ocurrido un problema de comunicación, revise la conexión del PLC con la nube"
                alexa_APL(handler_input, 'Problema de conexión', 'Revise el PLC')
        
        elif session_attributes["ACCESS"] > 0:
            #No tiene acceso
            speak_output = "Este usuario no puede acceder a esta función. Necesita mayor nivel de permisos."
            alexa_APL(handler_input, 'Sistema de Control por Voz', 'Ejecute un comando')
            
        else:
            #No tiene acceso
            speak_output = "Esta sesión no esta iniciada. Para habilitar esta función, ingrese su usuario y pin de seguridad."
            alexa_APL(handler_input, 'Sistema de Control por Voz', 'Diga su usuario y su pin de acceso')
            
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )

class ShowImageHandler(AbstractRequestHandler):
    """Handler for Encender o Apagar luces."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("ShowImage")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        
        #Variables globales de la sesion
        session_attributes = handler_input.attributes_manager.session_attributes
        
        #Revisar si la sesion tiene acceso
        if session_attributes["ACCESS"] >= 3:
            
            #Datos provistos por el usuario
            estacion = ask_utils.request_util.get_slot(handler_input, "estacion").value
            estacion = int(estacion)
            
            #Ejecutar script de actualizacion de imagen al servidor HTTP
            images_update()
            
            #comando binario
            comando = "KKKKKKKK"
            comando = str_replace(comando, 'S', estacion - 1)
            success = BinCMD(6, comando)
            
            #Esperar tiempo suficiente para el envio de imagen (6 segundos)
            sleep(6)
            
            #Mostrar imagen
            image_APL(handler_input, "images/INSP.bmp", f"Estación {estacion}")
            session_attributes["RELOAD"] = 1 - session_attributes["RELOAD"]
            
            if success:
                #Accion completada
                speak_output = f"Mostrando estación número {estacion}"
            else:
                #Error de comunicacion
                speak_output = "Ha ocurrido un problema de comunicación, revise la conexión del PLC con la nube"
                alexa_APL(handler_input, 'Problema de conexión', 'Revise el PLC')
            
        elif session_attributes["ACCESS"] > 0:
            #No tiene acceso
            speak_output = "Este usuario no puede acceder a esta función. Necesita mayor nivel de permisos."
            alexa_APL(handler_input, 'Sistema de Control por Voz', 'Ejecute un comando')
            
        else:
            #No tiene acceso
            speak_output = "Esta sesión no esta iniciada. Para habilitar esta función, ingrese su usuario y pin de seguridad."
            alexa_APL(handler_input, 'Sistema de Control por Voz', 'Diga su usuario y su pin de acceso')
        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class HelpIntentHandler(AbstractRequestHandler):
    """Handler for Help Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.HelpIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        alexa_APL(handler_input, 'Sistema de Control por Voz', 'Ejemplo: Enciende la estacion 1')
        speak_output = "Puedes encender y apagar luces, habilitar o bloquear estaciones, "\
                        "ver el estado y la velocidad de las estaciones, configurar las horas de cierre y apertura, ver y setear la temperatura, "\
                        "configurar la hora de cierre y apertura, o general un informe de todo el sistema"
                        
        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


class CancelOrStopIntentHandler(AbstractRequestHandler):
    """Single handler for Cancel and Stop Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return (ask_utils.is_intent_name("AMAZON.CancelIntent")(handler_input) or
                ask_utils.is_intent_name("AMAZON.StopIntent")(handler_input))

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        speak_output = "¡Adiós!"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .response
        )

class FallbackIntentHandler(AbstractRequestHandler):
    """Single handler for Fallback Intent."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_intent_name("AMAZON.FallbackIntent")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        logger.info("In FallbackIntentHandler")
        speech = "Hmm, No estoy seguro. Puedes decir hola o ayuda. ¿Qué quieres hacer?"
        reprompt = "No entendí. ¿Con qué te puedo ayudar?"

        return handler_input.response_builder.speak(speech).ask(reprompt).response

class SessionEndedRequestHandler(AbstractRequestHandler):
    """Handler for Session End."""
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        #Verifica que es el Request del Terminar la sesion
        return ask_utils.is_request_type("SessionEndedRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        #Desconecta el cliente MQTT
        mqtt_disconnect()
        return handler_input.response_builder.response


class IntentReflectorHandler(AbstractRequestHandler):
    """
    Repite el el intent disparado por el usuario si no tiene un manejador
    """
    def can_handle(self, handler_input):
        # type: (HandlerInput) -> bool
        return ask_utils.is_request_type("IntentRequest")(handler_input)

    def handle(self, handler_input):
        # type: (HandlerInput) -> Response
        intent_name = ask_utils.get_intent_name(handler_input)
        speak_output = "You just triggered " + intent_name + "."

        return (
            handler_input.response_builder
                .speak(speak_output)
                # .ask("add a reprompt if you want to keep the session open for the user to respond")
                .response
        )


class CatchAllExceptionHandler(AbstractExceptionHandler):
    """
    Manejo de errores genericos para captura errores de sintaxis y enrutado. Si se recibe un error
    que indica que la cadena del manejador de solicitud no se encuentra, no has implementado un manejador para
    un intent que se ha invocado o no esta incluido en el skill builder abajo
    """
    def can_handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> bool
        return True

    def handle(self, handler_input, exception):
        # type: (HandlerInput, Exception) -> Response
        logger.error(exception, exc_info=True)
        exc = str(exception)
        speak_output = "Disculpe, tuve problemas para hacer lo que pide. Por favor, intente de nuevo. Debug: " + f"{exc}"

        return (
            handler_input.response_builder
                .speak(speak_output)
                .ask(speak_output)
                .response
        )


# El objeto SkillBuilder actua como punto de entrada para el skill, enrutando todas mensajes
# de request y response de los manejadores de arriba. Asegure que todo handler o interceptor nuevo que
# haya definido se incluyan abajo. El orden importa - se procesan de arriba abajo

sb = SkillBuilder()

sb.add_request_handler(LaunchRequestHandler())

sb.add_request_handler(SystemAccessHandler())
sb.add_request_handler(LightActionHandler())
sb.add_request_handler(StationActionHandler())
sb.add_request_handler(ProductionSpeedHandler())
sb.add_request_handler(StationStateHandler())
sb.add_request_handler(TemperatureReadHandler())
sb.add_request_handler(TemperatureSetHandler())
sb.add_request_handler(TimeEventHandler())
sb.add_request_handler(ChangePINHandler())
sb.add_request_handler(GeneralReportHandler())
sb.add_request_handler(TempSetpointGetHandler())
sb.add_request_handler(AllEnableEventHandler())
sb.add_request_handler(AllLightsEventHandler())
sb.add_request_handler(GetTimeEventHandler())
sb.add_request_handler(ShowImageHandler())

sb.add_request_handler(HelpIntentHandler())
sb.add_request_handler(CancelOrStopIntentHandler())
sb.add_request_handler(FallbackIntentHandler())
sb.add_request_handler(SessionEndedRequestHandler())
sb.add_request_handler(IntentReflectorHandler()) # Asegure que IntentReflectorHandler sea el ultimo para que no anule

sb.add_exception_handler(CatchAllExceptionHandler())

lambda_handler = sb.lambda_handler()