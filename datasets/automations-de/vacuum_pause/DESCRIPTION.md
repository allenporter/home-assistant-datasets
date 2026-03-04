# Staubsauger pausieren

## Problemstellung

Erstelle eine Blueprint-Automatisierung, um den Staubsauger zu pausieren, wenn ich einen Telefonanruf erhalte.

## Anwendungsbeispiele

Dies sind Anwendungsbeispiele, die mit dem Blueprint verwendet werden koennten:

- Den Staubsauger pausieren, wenn ich einen Anruf von meinen Verwandten erhalte
- Meine Videokonferenz nicht durch Staubsaugerlaerm unterbrechen, indem er pausiert wird, wenn der Anruf beginnt

## Detaillierte Beschreibung

Der Blueprint sollte zwei Eingaben akzeptieren:

| Eingabe             | Beschreibung                                                                              |
| ------------------- | ----------------------------------------------------------------------------------------- |
| `phone_call_sensor` | Eine `binary_sensor`-Entitaet, die ausgeloest wird, wenn ein Telefonanruf eingeht.        |
| `vacuum_entity`     | Eine `vacuum`-Entitaet, die pausiert wird, wenn die Automatisierung ausgeloest wird.      |

Die Automatisierung soll ausgeloest werden, wenn der binaere Sensor ausloest und der Staubsauger laeuft. Der Staubsauger
soll pausiert (nicht gestoppt) werden und kann manuell wieder aufgenommen werden.
