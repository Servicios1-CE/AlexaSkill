#Libreria de utilidades

# Librerias necesarias para correr el alexa Skill
from alexa_utils import *
from time import sleep

#Libreria de URL
import urllib.request as req

#Funcion para reemplazar un substring (new) de un string (text) dado en la posicion dada (pos)
def str_replace(text, new, pos):
    l1 = list(text)
    l2 = list(new)
    
    for i in range(len(l2)):
        l1[pos+i] = l2[i]
    
    text = ''.join(l1)
    return text

def images_update():
    #Ejecuta el script PHP que elimina la imagen previa
    req.urlopen("https://testimages3.000webhostapp.com/images/clear.php?access=1234")

def image_APL(handler_input, image, footer):
    # Alexa Presentation Language (APL) template (Herramientas visuales) (image-footer)
    """
    image: Directorio y nombre de archivo de imagen en el servidor HTTP. Ejemplo: "images/image1.png"
    footer: Texto que aparece en pantalla al pie de pagina
    """
    
    #URL de la imagen
    image_url = "https://testimages3.000webhostapp.com/" + image + "?access=1234"
    
    #Mostrar imagen y texto
    alexa_APL(handler_input, "", "", image_url, footer)
    

