import click
import requests
import datetime
import json
import daemonocle
import paho.mqtt.subscribe as subscribe

from sqlalchemy.exc import IntegrityError

from apps import app, db
from apps.models import Device, Raw, Periodik

my_auth = ("bwskal3", "kal31029")

URL = "https://prinus.net/api/sensor"
MQTT_HOST = "mqtt.bbws-bsolo.net"
MQTT_PORT = 14983
MQTT_TOPIC = "bws-kal3"
MQTT_CLIENT = ""


@app.cli.command()
@click.argument('command')
def listen(command):
    daemon = daemonocle.Daemon(worker=subscribe_topic,
                              pidfile='listener.pid')
    daemon.do_action(command)


def on_mqtt_message(client, userdata, msg):
    data = json.loads(msg.payload.decode('utf-8'))
    with open('/tmp/data.json', 'w+') as f:
        f.write(data)
    raw2periodic(data)


def subscribe_topic():
    subscribe.callback(on_mqtt_message, MQTT_TOPIC,
                       hostname=MQTT_HOST, port=MQTT_PORT,
                       client_id=MQTT_CLIENT)


@app.cli.command()
def fetch_logger():
    res = requests.get(URL, auth=my_auth)

    if res.status_code == 200:
        logger = json.loads(res.text)
        local_logger = [d.sn for d in Device.query.all()]
        if len(local_logger) != len(logger):
            for l in logger:
                if l.get('sn') not in local_logger:
                    new_logger = Device(sn=l.get('sn'))
                    db.session.add(new_logger)
                    db.session.commit()
                    print('Tambah:', new_logger.sn)
    else:
        print(res.status_code)


@app.cli.command()
@click.argument('sn')
@click.option('-s', '--sampling', default='', help='Awal waktu sampling')
def fetch_periodic(sn, sampling):
    sampling_param = ''
    if sampling:
        sampling_param = '&sampling=' + sampling
    res = requests.get(URL + '/' + sn + '?robot=1' + sampling_param,
                       auth=my_auth)
    data = json.loads(res.text)
    for d in data:
        content = Raw(content=d)
        db.session.add(content)
        try:
            db.session.commit()
            raw2periodic(d)
        except Exception as e:
            db.session.rollback()
            print("ERROR:", e)
        print(d.get('sampling'), d.get('temperature'))


def raw2periodic(raw):
    '''Menyalin data dari Raw ke Periodik'''
    sn = raw.get('device').split('/')[1]
    session = db.session
    session.rollback()
    device = session.query(Device).filter_by(sn=sn).first()
    obj = {'device_sn': device.sn, 'lokasi_id': device.lokasi.id if
           device.lokasi else None}
    if raw.get('tick'):
        rain = (device.tipp_fac or 0.2) * raw.get('tick')
        obj.update({'rain': rain})
    if raw.get('distance'):
        # dianggap distance dalam milimeter
        # 'distance' MB7366(mm) di centimeterkan
        wlev = (device.ting_son or 100) - raw.get('distance') * 0.1
        obj.update({'wlev': wlev})
    time_to = {'sampling': 'sampling',
               'up_since': 'up_s',
               'time_set_at': 'ts_a'}
    direct_to = {'altitude': 'mdpl',
                 'signal_quality': 'sq',
                 'pressure': 'apre'}
    apply_to = {'humidity': 'humi',
                'temperature': 'temp',
                'battery': 'batt'}
    for k, v in time_to.items():
        obj.update({v: datetime.datetime.fromtimestamp(raw.get(k))})
    for k, v in direct_to.items():
        obj.update({v: raw.get(k)})
    for k, v in apply_to.items():
        corr = getattr(device, v + '_cor', 0)
        obj.update({v: raw.get(k) + corr})
    #print(obj.device_sn, obj.lokasi_id, obj.sampling)
    try:
        d = Periodik(**obj)
        db.session.add(d)
        db.session.commit()
    except IntegrityError:
        print(obj.get('device_sn'), obj.get('lokasi_id'), obj.get('sampling'))
        db.session.rollback()
