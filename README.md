# Proyecto Taller

Integrantes:
- Estrada Agustin
- Chaves Claudio
- Conti Viola Matias
- Ponce Braian
- Ortiz Julian

## Justificacion de la UML

En nuestro diagrama UML utilizamos los patrones de diseño *Strategy* y el *Factory Method*. El Factory Method lo utilizamos para poder desacoplar la creacion de Respuesta con la de Autor, ya que como dice el enunciado, la plataforma de preguntas necesita poder generar respuestas tanto de usuarios como de inteligencia artificial, por eso mismo el "*CreadorRepuesta*" esta relacionado con "*Usuario*" y con "*TagHelpIA*". Este ultima clase la creamos debido que en los requerimientos funcionales nos comentaba que cuando un Usuario(autor de una pregunta) utilizaba cierto tag en su pregunta, este generaba una respuesta asistida por IA. Por otro lado, el *Strategy* lo utilizamos para poder desacoplar la creacion de respuestas con IA para poder asi incluir mas tipos de Inteligencia Artificial sin necesidad de tener que mano en el codigo de la clase "*CreadoraIA*"