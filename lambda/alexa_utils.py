import logging
import ask_sdk_core.utils as ask_utils
import json
from ask_sdk_model.interfaces.alexa.presentation.apl import (RenderDocumentDirective)

from ask_sdk_core.skill_builder import SkillBuilder
from ask_sdk_core.dispatch_components import AbstractRequestHandler
from ask_sdk_core.dispatch_components import AbstractExceptionHandler
from ask_sdk_core.dispatch_components import AbstractRequestInterceptor
from ask_sdk_core.handler_input import HandlerInput

from ask_sdk_model import Response

def alexa_APL(handler_input, title, subtitle, image = "", footer = ""):
    # Alexa Presentation Language (APL) template (Herramientas visuales (title-subtitle)
    with open("./documents/APL_simple.json") as apl_doc:
        apl_simple = json.load(apl_doc)
        
        if ask_utils.get_supported_interfaces(handler_input).alexa_presentation_apl is not None:
            handler_input.response_builder.add_directive(
                RenderDocumentDirective(
                    document=apl_simple,
                    datasources={
                        "myData": {
                            #====================================================================
                            # Set a headline and subhead to display on the screen if there is one
                            #====================================================================
                            "Title": title,
                            "Subtitle": subtitle,
                            "Type": "AlexaHeadline",
                            "ImageSource": image,
                            "Footer": footer
                        }
                    }
                )
            )