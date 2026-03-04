# Licht bei Tueroeffnung

## Problemstellung

Erstelle eine Blueprint-Automatisierung, um ein Licht einzuschalten, wenn die Tuer geoeffnet wird.

## Anwendungsbeispiele

Dies sind Anwendungsbeispiele, die mit dem Blueprint verwendet werden koennten:

- Das Vorratsraumlicht einschalten, wenn die Vorratsraumtuer geoeffnet wird

## Detaillierte Beschreibung

Der Blueprint sollte zwei Eingaben akzeptieren:

| Eingabe        | Beschreibung                                                                                    |
| -------------- | ----------------------------------------------------------------------------------------------- |
| `door_sensor`  | Ein `binary_sensor`, der die Automatisierung ausloest.                                          |
| `light_switch` | Eine oder mehrere `light`-Entitaeten, die ein- oder ausgeschaltet werden, wenn die Automatisierung ausgeloest wird. |

Die Automatisierung soll ausgeloest werden, wenn die Tuer geoeffnet wird, und das Licht einschalten. Das
Licht soll ausgeschaltet werden, wenn die Tuer geschlossen wird oder nach einer Zeitueberschreitung von 2 Minuten.
