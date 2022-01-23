# Loxberry Plugin: P1 Decrypter

Dieses Plugin ermöglicht es verschlüsselte Daten von einem Smart Meter über die Kundenschnittstelle P1 zu entschlüssen und an den Miniserver über UDP und/oder an einen seriellen Port am Loxberry zu senden.

> English readme: [https://github.com/metrophos/LoxBerry-Plugin-P1-Decrypter/blob/main/README.md](https://github.com/metrophos/LoxBerry-Plugin-P1-Decrypter/blob/main/README.md)

<img src="https://raw.githubusercontent.com/metrophos/LoxBerry-Plugin-P1-Decrypter/assets/p1decrypter-plugin.png" alt="P1 Decrypter Plugin"/>

## Voraussetzung

- Smart Meter mit P1 Schnittstelle (Aktuell wurde das Plugin getestet mit dem Smart Meter: Sagemcom T210-D-r in Österreich)
- FTDI USB Kabel zum verbinden des Smart Meter mit Loxberry. 
  - Zum Beispiel: [https://www.aliexpress.com/item/32945225256.html](https://www.aliexpress.com/item/32945225256.html) (Option/Color: Sagemcom XS210 -> Sagemcom T210-D-r)
- Der Netzbetreiber muss die Kundenschnittstelle aktivieren und einen Key _"Global Unicast Encryption Key (GUEK)"_ zur Verfügung stellen
  - Normalerweise kann über die Weboberfläche des Netzbetreibers die Kundenschnittstelle aktiviert und der Key angezeigt werden
  - Das Aktivieren über die Weboberfläche des Netzbetreibers kann etwas Zeit in Anspruch nehmen

## Smart Meter

### T210-D-r (Österreich)

<img src="https://raw.githubusercontent.com/metrophos/LoxBerry-Plugin-P1-Decrypter/assets/Sagemcom-T210-D-r.png" alt="Sagemcom T210-D-r"/>

| OBIS-Code | Einheit      | Beschreibung                                            |
|-----------|--------------|---------------------------------------------------------|
| 1-3:0.2.8 | int          | P1 port DSMR version                                    |
| 0-0:1.0.0 | YYMMDDhhmmss | Impuls Datum und Zeit                                   |
| 1-0:1.8.0 | Wh           | Zählerstand +P (Wirkenergie Bezug)                      |
| 1-0:1.8.1 | Wh           | Active energy import (+A) rate 1                        |
| 1-0:1.8.2 | Wh           | Active energy import (+A) rate 2                        |
| 1-0:1.7.0 | W            | aktuelle Leistung +P (momentane Wirkleistung Bezug)     |
| 1-0:2.8.0 | Wh           | Zählerstand -P (Wirkenergie Lieferung)                  |
| 1-0:2.8.1 | Wh           | Active energy export (-A) rate 1                        |
| 1-0:2.8.2 | Wh           | Active energy export (-A) rate 2                        |
| 1-0:2.7.0 | W            | Aktuelle Leistung -P (momentane Wirkleistung Lieferung) |
| 1-0:3.8.0 | varh         | Blindenergie +R (Blindenergie Bezug)                    |
| 1-0:3.8.1 | varh         | Reactive energy import (+R) rate 1                      |
| 1-0:3.8.2 | varh         | Reactive energy import (+R) rate 2                      |
| 1-0:3.7.0 | var          | Momentanleistung +Q (var)                               |
| 1-0:4.8.0 | varh         | Blindenergie Lieferung -R (Wh)                          |
| 1-0:4.8.1 | varh         | Reactive energy export (-R) rate 1                      |
| 1-0:4.8.2 | varh         | Reactive energy export (-R) rate 2                      |
| 1-0:4.7.0 | var          | Momentanleistung -Q (var)                               |

## Value mapping

Das value mapping reduziert die information welche vom Smart Meter kommen.

Format ist: 
```
'label','regex'
'label','regex'
'label','regex'
...
```
> Das value mapping kann mittels `raw` switch deaktiviert werden.

### Beispiel

Um folgenden Wert `1-0:1.8.0:001234567` vom Original output `1-0:1.8.0(001234567*Wh)` zu erhalten
kann das value mapping wie folgt aussehen: `'1-0:1.8.0','(?<=1-0:1.8.0\().*?(?=\*Wh)'`

## Miniserver Konfiguration

- Virtueller UPD Eingang:
  - Senderadresse: Deine Loxberry IP
  - UPD Empfangsport: 54321 (Bzw. welcher im Plugin konfiguiert wurde)
- Virtueller UPD Einfang Befehl:
  - Befehlserkennung (Wenn die Daten wie im Value Mapping Beispiel geschickt werden): `\i1-0:1.8.0:\i\v`
> Zur Analyse der UPD Meldungen von Loxberry zum Miniserver benutze den _Loxone UPD Monitor_

### Beispiel für den Energiemonitor

- Die Werte kommen im Beispiel in Watt und müssen noch in Kilowatt umgerechnet werden `AI1/1000`
- Im Beispiel muss der Wert `1-0:1.7.0` und `1-0:2.7.0` mit folgender Formel verbunden werden `(I1-I2)/1000`

<img src="https://raw.githubusercontent.com/metrophos/LoxBerry-Plugin-P1-Decrypter/assets/loxone1.png" alt="Loxone"/>

## Danke an:

- tknaller - Für seinen modifizierten fork: https://github.com/tknaller/smarty_dsmr_proxy