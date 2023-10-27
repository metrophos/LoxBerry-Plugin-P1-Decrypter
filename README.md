# Loxberry Plugin: P1 Decrypter

Plugin to decrypt Smart Meter output over P1 customer interface and send it over UDP, MQTT and/or to a serial port.

> German readme: [https://github.com/metrophos/LoxBerry-Plugin-P1-Decrypter/blob/main/README-german.md](https://github.com/metrophos/LoxBerry-Plugin-P1-Decrypter/blob/main/README-german.md)

<img src="https://raw.githubusercontent.com/metrophos/LoxBerry-Plugin-P1-Decrypter/assets/p1decrypter-plugin.png" alt="P1 Decrypter Plugin"/>

## Precondition

- Smart Meter that has a P1 interface (Tested with Smart Meter: Sagemcom T210-D-r in Austria)
- FTDI USB cable to connect to the Smart Meter
  - One possibly option: [https://www.aliexpress.com/item/32945225256.html](https://www.aliexpress.com/item/32945225256.html) (Option/Color: Sagemcom XS210 -> Sagemcom T210-D-r)
- Your energy provider has to activate your customer interface and provide the encryption key _"Global Unicast Encryption Key (GUEK)"_

## Smart Meter

### T210-D-r (Austria)

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

If you don't need all informations of your smart meter you can use the value mapping.
Format is: 
```
'label','regex'
'label','regex'
'label','regex'
...
```

> Disable value mapping by enable `raw` switch.

### Example

To get `1-0:1.8.0:001234567\n` from raw output `1-0:1.8.0(001234567*Wh)`use value mapping like this: `'1-0:1.8.0','(?<=1-0:1.8.0\().*?(?=\*Wh)'`

## Miniserver configuration

- Virtual UPD input:
  - IP address: Your Loxberry IP
  - UPD Port: 54321 (or what you use configured over the plugin configuration)
- Virtual UPD input command:
  - command recognition (If you use the value mapping example above): `\i1-0:1.8.0:\i\v`
> To check incoming messages from Loxberry to Miniserver use _Loxone UPD monitor_

### Example to use by energy monitor

- In this example all values are in Watt. They have to be divide `AI1/1000`
- In this example `1-0:1.7.0` and `1-0:2.7.0` must be connected by this formula `(I1-I2)/1000`

<img src="https://raw.githubusercontent.com/metrophos/LoxBerry-Plugin-P1-Decrypter/assets/loxone1.png" alt="Loxone"/>

## Thanks to:

- Noschvie - For his great loxforum support and technical support: https://github.com/Noschvie
- tknaller - For his modified fork: https://github.com/tknaller/smarty_dsmr_proxy
