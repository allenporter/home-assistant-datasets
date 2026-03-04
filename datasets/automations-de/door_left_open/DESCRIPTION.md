# Tuer offen gelassen

## Problemstellung

Erstelle eine Blueprint-Automatisierung, um einen Alarm auf dem Lautsprecher abzuspielen, wenn die Tuer offen gelassen wird.

## Anwendungsbeispiele

Dies sind Anwendungsbeispiele, die mit dem Blueprint verwendet werden koennten:

- Eine Nachricht auf dem Wohnzimmerlautsprecher abspielen, wenn die Garagentuer laenger als 30 Minuten offen gelassen wurde
- Wenn die Haustuer 5 Minuten lang angelehnt ist, einen Ton auf dem Bluetooth-Lautsprecher in der Kueche abspielen.

## Detaillierte Beschreibung

Der Blueprint sollte zwei Eingaben akzeptieren:

| Eingabe         | Selektortyp   | Beschreibung                                                                                     |
| --------------- | ------------- | ------------------------------------------------------------------------------------------------ |
| `door_sensor`   | `entity`      | Ein `binary_sensor`-Entitaetsselektor fuer den Tuersensor, der Ziel der Automatisierung ist.     |
| `alert_media`   | `media`       | Das Ziel des `media`-Selektors fuer den Mediaplayer und die Medien-ID mit dem Alarm.             |
| `open_duration` | `duration`    | Ein `duration`-Selektor, die Zeitspanne bevor der Alarm abgespielt wird.                         |

Die Automatisierung soll das ausgewaehlte Medium abspielen, wenn die Tuer fuer die angegebene Dauer offen war.
