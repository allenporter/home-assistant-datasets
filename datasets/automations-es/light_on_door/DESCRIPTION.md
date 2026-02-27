# Luz al abrir la puerta

## Planteamiento del problema

Crea una automatizacion blueprint para encender una luz cuando se abre la puerta.

## Ejemplos de uso

Estos son ejemplos de uso que podrian utilizarse con el blueprint:

- Encender la luz de la despensa cuando se abre la puerta de la despensa

## Descripcion detallada

El blueprint debe aceptar dos entradas:

| Entrada        | Descripcion                                                                              |
| -------------- | ---------------------------------------------------------------------------------------- |
| `door_sensor`  | Un `binary_sensor` que activa el inicio de la automatizacion.                            |
| `light_switch` | Una o mas entidades `light` objetivo para encender o apagar cuando se active la automatizacion. |

La automatizacion debe activarse cuando se abre la puerta y encender la luz. La
luz debe apagarse cuando se cierre la puerta o despues de un tiempo de espera de 2 minutos.
