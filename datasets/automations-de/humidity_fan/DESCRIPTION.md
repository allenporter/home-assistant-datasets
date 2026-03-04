# Ventilator bei Luftfeuchtigkeit

## Problemstellung

Erstelle eine Blueprint-Automatisierung, um den Ventilator basierend auf dem Wert des Feuchtigkeitssensors einzuschalten.

## Anwendungsbeispiele

Dies sind Anwendungsbeispiele, die mit dem Blueprint verwendet werden koennten:

- Den Abluftventilator im Badezimmer einschalten, wenn die Luftfeuchtigkeit im Badezimmer ueber 60% liegt
- Sicherstellen, dass die Garage nicht zu feucht wird

## Detaillierte Beschreibung

Der Blueprint sollte zwei Eingaben akzeptieren:

| Eingabe             | Beschreibung                                                                         |
| ------------------- | ------------------------------------------------------------------------------------ |
| `humidity_sensor` | Eine `sensor`-Entitaet, die ein Feuchtigkeitssensor ist und die Automatisierung ausloest. |
| `humidity_level`  | Ein `number`-Selektor zum Festlegen des Werts, der als Ausloeser verwendet wird.          |
| `fan_entity`      | Eine `fan`-Entitaet, die eingeschaltet wird, wenn die Automatisierung ausgeloest wird.    |

Die Automatisierung soll ausgeloest werden, wenn der `humidity_sensor`-Wert ueber `humidity_level` steigt. Bei
Ausloesung soll der Ventilator eingeschaltet werden. Der Ventilator soll auch ausgeschaltet werden, wenn der
Sensor wieder unter das gewuenschte Niveau faellt. Die Automatisierung soll nicht versuchen,
den Ventilator einzuschalten, wenn er bereits eingeschaltet ist, und ihn nicht ausschalten, wenn er bereits ausgeschaltet ist.
