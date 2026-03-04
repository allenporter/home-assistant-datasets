# Porte laissee ouverte

## Enonce du probleme

Creez une automatisation blueprint pour diffuser une alerte sur l'enceinte lorsque la porte est laissee ouverte.

## Exemples d'utilisation

Voici des exemples d'utilisation qui pourraient etre utilises avec le blueprint :

- Diffuser un message sur l'enceinte du salon si la porte du garage est restee ouverte pendant plus de 30 minutes
- Lorsque la porte d'entree est entrouverte depuis 5 minutes, diffuser un son sur l'enceinte bluetooth de la cuisine.

## Description detaillee

Le blueprint doit accepter deux entrees :

| Entree          | Type de selecteur | Description                                                                                            |
| --------------- | ----------------- | ------------------------------------------------------------------------------------------------------ |
| `door_sensor`   | `entity`          | Un selecteur d'entite `binary_sensor` pour le capteur de porte cible de l'automatisation.              |
| `alert_media`   | `media`           | La cible du selecteur `media` pour le lecteur multimedia et l'identifiant du media avec l'alerte.      |
| `open_duration` | `duration`        | Un selecteur de `duration`, la duree avant de diffuser l'alerte.                                       |

L'automatisation doit diffuser le media selectionne lorsque la porte est restee ouverte pendant la duree specifiee.
