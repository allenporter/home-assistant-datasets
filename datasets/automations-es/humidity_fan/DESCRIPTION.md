# Ventilador por humedad

## Planteamiento del problema

Crea una automatizacion blueprint para encender el ventilador segun el valor del sensor de humedad.

## Ejemplos de uso

Estos son ejemplos de uso que podrian utilizarse con el blueprint:

- Encender el extractor del bano cuando la humedad del bano supere el 60%
- Asegurarse de que el garaje no se humedezca demasiado

## Descripcion detallada

El blueprint debe aceptar dos entradas:

| Entrada             | Descripcion                                                                      |
| ------------------- | -------------------------------------------------------------------------------- |
| `humidity_sensor` | Una entidad `sensor` que es un sensor de humedad que activa la automatizacion.     |
| `humidity_level`  | Un selector `number` para establecer el valor utilizado como activador.             |
| `fan_entity`      | Una entidad `fan` para encender cuando se active la automatizacion.                |

La automatizacion debe activarse cuando el nivel de `humidity_sensor` supere `humidity_level`. Cuando
se active, el ventilador debe encenderse. El ventilador tambien debe apagarse cuando el
sensor baje por debajo del nivel deseado. La automatizacion no debe intentar
encender el ventilador si ya esta encendido, ni apagarlo cuando ya esta apagado.
