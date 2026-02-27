# Pausar el aspirador

## Planteamiento del problema

Crea una automatizacion blueprint para pausar el aspirador cuando recibo una llamada telefonica.

## Ejemplos de uso

Estos son ejemplos de uso que podrian utilizarse con el blueprint:

- Pausar el aspirador cuando recibo una llamada de mis familiares
- No interrumpir mi videoconferencia de trabajo con el ruido del aspirador pausandolo cuando comience la llamada

## Descripcion detallada

El blueprint debe aceptar dos entradas:

| Entrada             | Descripcion                                                                           |
| ------------------- | ------------------------------------------------------------------------------------- |
| `phone_call_sensor` | Una entidad `binary_sensor` que se activa cuando se recibe una llamada telefonica.    |
| `vacuum_entity`     | Una entidad `vacuum` para pausar cuando se active la automatizacion.                  |

La automatizacion debe activarse cuando el sensor binario se dispare y el aspirador este en funcionamiento. El aspirador
debe pausarse (no detenerse) y puede reanudarse manualmente.
