# Puerta dejada abierta

## Planteamiento del problema

Crea una automatizacion blueprint para reproducir una alerta en el altavoz cuando la puerta se deja abierta.

## Ejemplos de uso

Estos son ejemplos de uso que podrian utilizarse con el blueprint:

- Reproducir un mensaje en el altavoz del salon si la puerta del garaje se ha dejado abierta durante mas de 30 minutos
- Cuando la puerta principal esta entreabierta durante 5 minutos, reproducir un sonido en el altavoz bluetooth de la cocina.

## Descripcion detallada

El blueprint debe aceptar dos entradas:

| Entrada         | Tipo de selector | Descripcion                                                                                        |
| --------------- | ---------------- | -------------------------------------------------------------------------------------------------- |
| `door_sensor`   | `entity`         | Un selector de entidad `binary_sensor` para el sensor de puerta objetivo de la automatizacion.     |
| `alert_media`   | `media`          | El objetivo del selector `media` para el reproductor multimedia y el id del medio con la alerta.   |
| `open_duration` | `duration`       | Un selector de `duration`, la cantidad de tiempo antes de reproducir la alerta.                    |

La automatizacion debe reproducir el medio seleccionado cuando la puerta ha estado abierta durante el tiempo especificado.
