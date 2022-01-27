import socket
import serial
import binascii
import argparse
import re
import logging
import sys
import os
import configparser
import json
import base64
import paho.mqtt.client as mqtt
from Cryptodome.Cipher import AES


class P1decrypter:
    def __init__(self):

        self.STATE_IGNORING = 0
        self.STATE_STARTED = 1
        self.STATE_HAS_SYSTEM_TITLE_LENGTH = 2
        self.STATE_HAS_SYSTEM_TITLE = 3
        self.STATE_HAS_SYSTEM_TITLE_SUFFIX = 4
        self.STATE_HAS_DATA_LENGTH = 5
        self.STATE_HAS_SEPARATOR = 6
        self.STATE_HAS_FRAME_COUNTER = 7
        self.STATE_HAS_PAYLOAD = 8
        self.STATE_DONE = 9

        # Command line arguments
        self._args = {}

        # Serial connection to p1 smart meter interface
        self._connection = None

        # Initial empty values. These will be filled as content is read
        # and they will be reset each time we go back to the initial state.
        self._state = self.STATE_IGNORING
        self._buffer = ""
        self._buffer_length = 0
        self._next_state = 0
        self._system_title_length = 0
        self._system_title = b""
        self._data_length_bytes = b""  # length of "remaining data" in bytes
        self._data_length = 0  # length of "remaining data" as an integer
        self._frame_counter = b""
        self._payload = b""
        self._gcm_tag = b""

        self.LBSCONFIG = ""
        self.miniserver_id = ""
        self.general_json = {}
        self.mqtt_use_gateway = False
        self.mqtt_connected = False
        self.mqtt_client = {}

    def main(self):
        self.args()

    def args(self):
        parser = argparse.ArgumentParser()
        parser.add_argument('key', help="Global Unicast Encryption Key (GUEK)")

        parser.add_argument('-iport', '--serial-input-port', required=False, default="/dev/ttyUSB0",
                            help="Serial input port. Default: /dev/ttyUSB0")
        parser.add_argument('-ibaudrate', '--serial-input-baudrate', required=False, type=int, default=115200,
                            help="Serial input baudrate. Default: 115200")
        parser.add_argument('-iparity', '--serial-input-parity', required=False, default=serial.PARITY_NONE,
                            help="Serial input parity. Default: None")
        parser.add_argument('-istopbits', '--serial-input-stopbits', required=False, type=int,
                            default=serial.STOPBITS_ONE,
                            help="Serial input stopbits. Default: 1")

        parser.add_argument('-m', '--mapping', required=False,
                            default="'1-0:1.8.0','(?<=1-0:1.8.0\().*?(?=\*Wh)'\n'1-0:1.7.0','(?<=1-0:1.7.0\().*?(?=\*W)'\n'1-0:2.8.0','(?<=1-0:2.8.0\().*?(?=\*Wh)'\n'1-0:2.7.0','(?<=1-0:2.7.0\().*?(?=\*W)'",
                            help="Value mapping. Default: '1-0:1.8.0','(?<=1-0:1.8.0\().*?(?=\*Wh)',\\n'1-0:1.7.0','(?<=1-0:1.7.0\().*?(?=\*W)'\\n'1-0:2.8.0','(?<=1-0:2.8.0\().*?(?=\*Wh)'\\n'1-0:2.7.0','(?<=1-0:2.7.0\().*?(?=\*W)'")

        parser.add_argument('-a', '--aad', required=False, default="3000112233445566778899AABBCCDDEEFF",
                            help="Additional authenticated data. Default: 3000112233445566778899AABBCCDDEEFF")

        parser.add_argument('-u', '--send-to-udp', required=False, default=False, action='store_true',
                            help="Send data over UDP. Default: false")
        parser.add_argument('-ui', '--udp-host', help="UDP IP / Host")
        parser.add_argument('-up', '--udp-port', type=int, help="UDP port. Default: 54321")

        parser.add_argument('-q', '--send-mqtt', required=False, default=False, action='store_true',
                            help="Send data over MQTT. Default: false")
        parser.add_argument('-qb', '--mqtt-broker', help="MQTT Broker")
        parser.add_argument('-qu', '--mqtt-broker-username', help="MQTT Broker Username")
        parser.add_argument('-qw', '--mqtt-broker-password', help="MQTT Broker Password")
        parser.add_argument('-qp', '--mqtt-broker-port', default="1883", type=int, help="MQTT port. Default: 1883")
        parser.add_argument('-qt', '--mqtt-topic-prefix', default="p1decrypter",
                            help="MQTT Topic prefix. Default: p1decrypter")
        parser.add_argument('-qq', '--mqtt-topic-qos', type=int, default=1, help="MQTT QOS Default: 1")

        parser.add_argument('-s', '--send-to-serial-port', required=False, default=False, action='store_true',
                            help="Send data to output serial port. Use socat to generate virtual port e.g.: socat -d -d pty,raw,echo=0,link=/dev/p1decrypterI pty,raw,echo=0,link=/dev/p1decrypterO")
        parser.add_argument('-oport', '--serial-output-port', required=False, default="/dev/t210dr",
                            help="Serial output port. Default: /dev/p1decrypter")
        parser.add_argument('-obaudrate', '--serial-output-baudrate', required=False, type=int, default=115200,
                            help="Serial output baudrate. Default: 115200")
        parser.add_argument('-oparity', '--serial-output-parity', required=False, default=serial.PARITY_NONE,
                            help="Serial output parity. Default: None")
        parser.add_argument('-ostopbits', '--serial-output-stopbits', required=False, type=int,
                            default=serial.STOPBITS_ONE,
                            help="Serial output stopbits. Default: 1")

        parser.add_argument('-r', '--raw', required=False, default=False, action='store_true',
                            help="Output raw, without mapping")
        parser.add_argument('-v', "--verbose", required=False, default=False, action='store_true', help="Verbose mode")
        parser.add_argument('-l', '--logfile', required=False, help="Logfile path")
        parser.add_argument('-c', "--configfile", required=False, help="Configfile path")

        self._args = parser.parse_args()

        self.config()

    def config(self):

        if self._args.logfile:
            logging.basicConfig(filename=self._args.logfile,
                                filemode='w',
                                level=logging.INFO,
                                format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                                datefmt='%Y-%m-%d %H:%M:%S')
        else:
            logging.basicConfig(level=logging.INFO,
                                format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                                datefmt='%Y-%m-%d %H:%M:%S',
                                handlers=[logging.StreamHandler()])

        logging.info("Process arguments and config")

        if self._args.configfile:
            logging.info("Read config file and overwrite arguments")
            if not os.path.exists(self._args.configfile):
                logging.critical("Configuration file not exsits {0}".format(self._args.configfile))
                sys.exit(-1)

            pluginconfig = configparser.ConfigParser()
            pluginconfig.read(self._args.configfile)

            self.LBSCONFIG = os.getenv("LBSCONFIG", os.getcwd())
            self.miniserver_id = pluginconfig.get('P1DECRYPTER', 'MINISERVER_ID')
            self.mqtt_use_gateway = bool(int(pluginconfig.get('P1DECRYPTER', 'MQTT_USE_GATEWAY')))

            self._args.enabled = bool(int(pluginconfig.get('P1DECRYPTER', 'ENABLED')))
            self._args.key = pluginconfig.get('P1DECRYPTER', 'KEY')
            self._args.serial_input_port = pluginconfig.get('P1DECRYPTER', 'SERIAL_INPUT_PORT')
            self._args.serial_input_baudrate = int(pluginconfig.get('P1DECRYPTER', 'SERIAL_INPUT_BAUDRATE'))
            self._args.serial_input_parity = pluginconfig.get('P1DECRYPTER', 'SERIAL_INPUT_PARITY')
            self._args.serial_input_stopbits = int(pluginconfig.get('P1DECRYPTER', 'SERIAL_INPUT_STOPBITS'))
            self._args.mapping = base64.b64decode(
                pluginconfig.get('P1DECRYPTER', 'MAPPING').replace('\\n', '').encode('ascii')
            ).decode('ascii')
            self._args.aad = pluginconfig.get('P1DECRYPTER', 'AAD')

            self._args.send_to_udp = bool(int(pluginconfig.get('P1DECRYPTER', 'SEND_TO_UDP')))
            self._args.udp_host = pluginconfig.get('P1DECRYPTER', 'UDP_HOST')
            self._args.udp_port = int(pluginconfig.get('P1DECRYPTER', 'UDP_PORT'))

            self._args.send_mqtt = bool(int(pluginconfig.get('P1DECRYPTER', 'SEND_MQTT')))
            self._args.mqtt_broker = pluginconfig.get('P1DECRYPTER', 'MQTT_BROKER')
            self._args.mqtt_broker_username = pluginconfig.get('P1DECRYPTER', 'MQTT_BROKER_USERNAME')
            self._args.mqtt_broker_password = pluginconfig.get('P1DECRYPTER', 'MQTT_BROKER_PASSWORD')
            self._args.mqtt_broker_port = int(pluginconfig.get('P1DECRYPTER', 'MQTT_BROKER_PORT'))
            self._args.mqtt_topic_prefix = pluginconfig.get('P1DECRYPTER', 'MQTT_TOPIC_PREFIX')
            self._args.mqtt_topic_qos = int(pluginconfig.get('P1DECRYPTER', 'MQTT_TOPIC_QOS'))

            self._args.send_to_serial_port = bool(int(pluginconfig.get('P1DECRYPTER', 'SEND_TO_SERIAL_PORT')))
            self._args.serial_output_port = pluginconfig.get('P1DECRYPTER', 'SERIAL_OUTPUT_PORT')
            self._args.serial_output_baudrate = int(pluginconfig.get('P1DECRYPTER', 'SERIAL_OUTPUT_BAUDRATE'))
            self._args.serial_output_parity = pluginconfig.get('P1DECRYPTER', 'SERIAL_OUTPUT_PARITY')
            self._args.serial_output_stopbits = int(pluginconfig.get('P1DECRYPTER', 'SERIAL_OUTPUT_STOPBITS'))

            self._args.raw = bool(int(pluginconfig.get('P1DECRYPTER', 'RAW')))
            self._args.verbose = bool(int(pluginconfig.get('P1DECRYPTER', 'VERBOSE')))
        else:
            self._args.enabled = 1

        if self._args.verbose:
            logging.getLogger().setLevel(logging.DEBUG)

        if self._args.enabled == "0":
            logging.critical("P1 Decrypter is not enabled in configuration file. exit")
            sys.exit(-1)

        if not self.mqtt_use_gateway and self._args.mqtt_broker == "" and self._args.send_mqtt:
            logging.critical("No MQTT Broker defined. exit")
            sys.exit(-1)

        self.loxberry()

    def loxberry(self):

        set_udp = not self._args.udp_host and self._args.send_to_udp

        if set_udp or self.mqtt_use_gateway:
            config_path = os.path.join(self.LBSCONFIG, "general.json")
            logging.info("Try load Miniserver system configuration file {0}".format(config_path))
            with open(config_path, "r") as config_path_handle:
                self.general_json = json.load(config_path_handle)

            # get miniserver ip
            if set_udp and not self.miniserver_id:
                logging.error("No UDP Host or Miniserver ID is set.")
                sys.exit(-1)
            else:
                logging.info("Check if miniserver exists in {0}".format(config_path))
                if not self.miniserver_id in self.general_json["Miniserver"].keys():
                    logging.critical("Miniserver with id {0} is not configured in {1}. exit"
                                     .format(self.miniserver_id, config_path))
                    sys.exit(-1)

                self._args.udp_host = self.general_json["Miniserver"][self.miniserver_id]["Ipaddress"]
                logging.info("Miniserver ip address: {0}".format(self._args.udp_host))

            # get mqtt settings
            if self.mqtt_use_gateway:
                logging.info("MQTT Gateway settings enabled")
                if not "Mqtt" in self.general_json:
                    logging.critical("MQTT Gateway settings not available. exit"
                                     .format(self.miniserver_id, config_path))
                    sys.exit(-1)

                self._args.mqtt_broker = self.general_json["Mqtt"]["Brokerhost"]
                self._args.mqtt_broker_username = self.general_json["Mqtt"]["Brokeruser"]
                self._args.mqtt_broker_password = self.general_json["Mqtt"]["Brokerpass"]
                self._args.mqtt_broker_port = int(self.general_json["Mqtt"]["Brokerport"])

        # debug log of config
        if self._args.verbose:
            key = self._args.key
            aad = self._args.aad
            mqtt_broker_password = self._args.mqtt_broker_password
            self._args.key = 'KEY_WILL_NOT_SHOWN_IN_LOGFILE'
            self._args.aad = 'AAD_WILL_NOT_SHOWN_IN_LOGFILE'
            self._args.mqtt_broker_password = 'PASSWORD_WILL_NOT_SHOWN_IN_LOGFILE'
            logging.debug("Config processed: {0}".format(self._args))
            self._args.key = key
            self._args.aad = aad
            self._args.mqtt_broker_password = mqtt_broker_password

        self.connect()
        logging.info("Start processing incoming data.")
        while True:
            self.process()

    def connect(self):
        logging.info("Connect to serial input port")

        try:
            self._connection = serial.Serial(
                port=self._args.serial_input_port,
                baudrate=self._args.serial_input_baudrate,
                parity=self._args.serial_input_parity,
                stopbits=self._args.serial_input_stopbits
            )
        except Exception as e:
            logging.critical("Connection to serial input port failed: {0}. exit".format(e))
            sys.exit(-1)

    def process(self):
        hex_input = binascii.hexlify(self._connection.read())

        if self._state == self.STATE_IGNORING:
            logging.debug("STATE_IGNORING: Wait for start byte, got: ({0})".format(hex_input))
            if hex_input == b'db':
                logging.debug("STATE_IGNORING: Start byte has been detected: ({0})".format(hex_input))
                self._state = self.STATE_STARTED
                self._buffer = b""
                self._buffer_length = 1
                self._system_title_length = 0
                self._system_title = b""
                self._data_length = 0
                self._data_length_bytes = b""
                self._frame_counter = b""
                self._payload = b""
                self._gcm_tag = b""
            else:
                return
        elif self._state == self.STATE_STARTED:
            self._state = self.STATE_HAS_SYSTEM_TITLE_LENGTH
            self._system_title_length = int(hex_input, 16)
            self._buffer_length = self._buffer_length + 1
            self._next_state = 2 + self._system_title_length  # start bytes + system title length
            logging.debug("STATE_STARTED: Length of system title: ({0})".format(self._system_title_length))
        elif self._state == self.STATE_HAS_SYSTEM_TITLE_LENGTH:
            if self._buffer_length > self._next_state:
                self._system_title += hex_input
                self._state = self.STATE_HAS_SYSTEM_TITLE
                self._next_state = self._next_state + 2  # read two more bytes
                logging.debug("STATE_HAS_SYSTEM_TITLE_LENGTH: System title: ({0})".format(self._system_title))
            else:
                self._system_title += hex_input
        elif self._state == self.STATE_HAS_SYSTEM_TITLE:
            if hex_input == b'82':
                self._next_state = self._next_state + 1
                self._state = self.STATE_HAS_SYSTEM_TITLE_SUFFIX  # Ignore separator byte
                logging.debug("STATE_HAS_SYSTEM_TITLE: Additional byte after system title: ({0})".format(hex_input))
            else:
                logging.warning("Expected 0x82 separator byte not found, dropping frame")
                logging.debug("Buffer ({0})".format(self._buffer))
                self._state = self.STATE_IGNORING
        elif self._state == self.STATE_HAS_SYSTEM_TITLE_SUFFIX:
            if self._buffer_length > self._next_state:
                self._data_length_bytes += hex_input
                self._data_length = int(self._data_length_bytes, 16)
                self._state = self.STATE_HAS_DATA_LENGTH
                logging.debug("STATE_HAS_SYSTEM_TITLE_SUFFIX: Length of remaining data: ({0})"
                              .format(self._data_length_bytes))
            else:
                self._data_length_bytes += hex_input
        elif self._state == self.STATE_HAS_DATA_LENGTH:
            logging.debug("STATE_HAS_DATA_LENGTH: Additional byte after data: ({0})".format(hex_input))
            self._state = self.STATE_HAS_SEPARATOR  # Ignore separator byte
            self._next_state = self._next_state + 1 + 4  # separator byte + 4 bytes for framecounter
        elif self._state == self.STATE_HAS_SEPARATOR:
            if self._buffer_length > self._next_state:
                self._frame_counter += hex_input
                self._state = self.STATE_HAS_FRAME_COUNTER
                self._next_state = self._next_state + self._data_length - 17
                logging.debug("STATE_HAS_DATA_LENGTH: Frame counter: ({0})".format(self._frame_counter))
            else:
                self._frame_counter += hex_input
        elif self._state == self.STATE_HAS_FRAME_COUNTER:
            if self._buffer_length > self._next_state:
                self._payload += hex_input
                self._state = self.STATE_HAS_PAYLOAD
                self._next_state = self._next_state + 12
                logging.debug("STATE_HAS_FRAME_COUNTER: Payload: ({0})".format(self._payload))
            else:
                self._payload += hex_input
        elif self._state == self.STATE_HAS_PAYLOAD:
            if self._buffer_length > self._next_state:
                self._gcm_tag += hex_input
                self._state = self.STATE_DONE
                logging.debug("STATE_HAS_PAYLOAD: GCM Tag: {0}".format(self._gcm_tag))
                logging.debug("STATE_HAS_PAYLOAD: Switch back to STATE_IGNORING and wait for a new telegram")
            else:
                self._gcm_tag += hex_input

        self._buffer += hex_input
        self._buffer_length = self._buffer_length + 1

        if self._state == self.STATE_DONE:
            self.decrypt()
            self._state = self.STATE_IGNORING

    def decrypt(self):
        logging.debug("Full telegram received, start decryption of: {0}".format(self._buffer))

        cipher = AES.new(
            binascii.unhexlify(self._args.key),
            AES.MODE_GCM,
            binascii.unhexlify(self._system_title + self._frame_counter),
            mac_len=12
        )
        cipher.update(binascii.unhexlify(self._args.aad))
        self.mapping(cipher.decrypt(binascii.unhexlify(self._payload)))

    def mapping(self, decryption):
        logging.debug("Decryption done. Extract data by mapping configuration: {0}".format(decryption))

        decryption_decoded = decryption.decode()
        mapped_values_string = ""

        if self._args.raw:
            logging.debug("Raw output is enabled. Mapping extraction stopped. Send complete telegram")
            mapped_values_string = decryption_decoded
            mapped_values_array = decryption_decoded
        else:
            input_multi_array = []
            mapped_values_array = []
            for i in self._args.mapping.splitlines():
                input_multi_array.append([i.split(',')[0].strip().strip("'"), i.split(',')[1].strip().strip("'")])

            for i in input_multi_array:
                value = re.search(i[1], decryption_decoded).group(0)
                mapped_values_string += i[0] + ":" + value + "\n"
                mapped_values_array.append([i[0], value])

            mapped_values_string = mapped_values_string

        if self._args.send_to_udp:
            self.send_to_udb(mapped_values_string)

        if self._args.send_to_serial_port:
            self.send_to_serial_port(mapped_values_string)

        if self._args.send_mqtt:
            self.send_mqtt(mapped_values_array)

    def send_to_serial_port(self, output):
        logging.debug("Send the decrypted data to output serial port: {0}".format(output.decode()))
        serial_port = serial.Serial(
            port=self._args.serial_output_port,
            baudrate=self._args.serial_output_baudrate,
            parity=self._args.serial_output_parity,
            stopbits=self._args.serial_output_stopbits
        )
        serial_port.write(output.encode())
        serial_port.close()

    def send_to_udb(self, output):
        logging.debug("Send the decrypted data over udp: {0}".format(output))
        connection = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        res = connection.sendto(output.encode(), (self._args.udp_host, self._args.udp_port))
        connection.close()

        if res != output.encode().__len__():
            logging.error("Sent bytes not matching. Expected {0} to be {1}".format(output.__len__(), res))

    def send_mqtt(self, output):
        def get_mqtt_client():
            if not self.mqtt_connected:
                logging.info("Try to connect to MQTT Broker: {0}".format(self._args.mqtt_broker))
                self.mqtt_connected = True

                def on_connect(client, userdata, flags, rc):
                    if rc == 0:
                        logging.info("Connected to MQTT Broker: {0}".format(self._args.mqtt_broker))
                    else:
                        self.mqtt_connected = False
                        logging.error("MQTT connection failed {0}".format(rc))

                def on_disconnect():
                    self.mqtt_connected = False
                    logging.error("MQTT disconnected")

                self.mqtt_client = mqtt.Client()
                if self._args.mqtt_broker_username or self._args.mqtt_broker_password:
                    self.mqtt_client.username_pw_set(self._args.mqtt_broker_username, self._args.mqtt_broker_password)
                else:
                    logging.info("MQTT Broker username and password not set")

                self.mqtt_client.on_connect = on_connect
                self.mqtt_client.on_disconnect = on_disconnect

                self.mqtt_client.connect(self._args.mqtt_broker, self._args.mqtt_broker_port)
                return self.mqtt_client
            else:
                return self.mqtt_client

        mqtt_client = get_mqtt_client()
        if self._args.raw:
            logging.debug(
                "Send decrypted data over mqtt: {0} -> {1}".format(self._args.mqtt_topic_prefix + "/raw", output))
            mqtt_client.publish(self._args.mqtt_topic_prefix + "/raw", output, qos=self._args.mqtt_topic_qos)
        else:
            for i in output:
                logging.debug(
                    "Send decrypted data over mqtt: {0} -> {1}".format(self._args.mqtt_topic_prefix + "/" + i[0], i[1]))
                mqtt_client.publish(self._args.mqtt_topic_prefix + "/" + i[0], i[1], qos=self._args.mqtt_topic_qos)
        mqtt_client.loop()


if __name__ == '__main__':
    smarty_proxy = P1decrypter()
    smarty_proxy.main()
