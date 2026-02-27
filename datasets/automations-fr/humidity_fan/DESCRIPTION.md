# Ventilateur selon l'humidite

## Enonce du probleme

Creez une automatisation blueprint pour allumer le ventilateur en fonction de la valeur du capteur d'humidite.

## Exemples d'utilisation

Voici des exemples d'utilisation qui pourraient etre utilises avec le blueprint :

- Allumer l'extracteur de la salle de bain lorsque l'humidite de la salle de bain depasse 60%
- S'assurer que le garage ne devienne pas trop humide

## Description detaillee

Le blueprint doit accepter deux entrees :

| Entree              | Description                                                                            |
| ------------------- | -------------------------------------------------------------------------------------- |
| `humidity_sensor` | Une entite `sensor` qui est un capteur d'humidite declenchant l'automatisation.          |
| `humidity_level`  | Un selecteur `number` pour definir la valeur utilisee comme declencheur.                  |
| `fan_entity`      | Une entite `fan` a allumer lorsque l'automatisation se declenche.                        |

L'automatisation doit se declencher lorsque le niveau de `humidity_sensor` depasse `humidity_level`. Lorsqu'elle
se declenche, le ventilateur doit s'allumer. Le ventilateur doit egalement s'eteindre lorsque le
capteur redescend en dessous du niveau souhaite. L'automatisation ne doit pas essayer
d'allumer le ventilateur s'il est deja allume, ni de l'eteindre s'il est deja eteint.
