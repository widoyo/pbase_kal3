import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from flask_login import UserMixin

from apps import login
from apps import db
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import relationship
from sqlalchemy import desc


class Raw(db.Model):
    __tablename__ = 'raw'

    id = db.Column(db.Integer, primary_key=True)
    content = db.Column(JSONB, unique=True)
    received = db.Column(db.DateTime, default=datetime.datetime.utcnow)


class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(12), index=True, unique=True, nullable=False)
    password = db.Column(db.String(128))

    def set_password(self, password):
        self.password = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password, password)

    def __repr__(self):
        return '<User %r>' % self.username


@login.user_loader
def load_user(id):
    return User.query.get(int(id))


class Device(db.Model):
    __tablename__ = 'device'

    id = db.Column(db.Integer, primary_key=True)
    sn = db.Column(db.String(8), index=True, unique=True, nullable=False)
    tipe = db.Column(db.String(12), default="arr")
    lokasi_id = db.Column(db.Integer, db.ForeignKey('lokasi.id'), nullable=True)
    periodik = db.relationship('Periodik', back_populates='device', lazy='dynamic')
    temp_cor = db.Column(db.Float)
    humi_cor = db.Column(db.Float)
    batt_cor = db.Column(db.Float)
    tipp_fac = db.Column(db.Float)
    ting_son = db.Column(db.Float) # dalam centi, tinggi sonar thd dasar sungai

    lokasi = relationship('Lokasi', back_populates='devices')

    def periodik_latest(self):
        return self.periodik.order_by(Periodik.id.desc()).first()

    def icon(self):
        return 'arr' == self.tipe and 'cloud-download' or 'upload'

    def __repr__(self):
        return '<Device {}>'.format(self.sn)


class Lokasi(db.Model):
    __tablename__ = 'lokasi'

    id = db.Column(db.Integer, primary_key=True)
    nama = db.Column(db.String(50), index=True, unique=True)
    ll = db.Column(db.String(35))
    jenis = db.Column(db.String(1)) # 1 CH, 2 TMA, 3 Bendungan, 4 Klim
    devices = relationship('Device', back_populates='lokasi')
    periodik = relationship('Periodik', back_populates='lokasi')

    def __repr__(self):
        return '<Lokasi {}>'.format(self.nama)

    def hujan_hari(self, tanggal):
        '''Return dict(jam: hujan)
        Mengambil data hujan sampling tanggal, akumulasi per jam'''
        now = datetime.datetime.now()
        start_pattern = '%Y-%m-%d 07:00:00'
        date_pattern = '%Y-%m-%d %H:%M:%S'
        mulai = datetime.datetime.strptime(
            tanggal.strftime(start_pattern), date_pattern)
        if tanggal != now.date() or now.hour <= 23:
            mulai -= datetime.timedelta(days=1)
            akhir = datetime.datetime.strptime(
                tanggal.strftime(start_pattern), date_pattern)
        else:
            akhir = now
        ret = dict()
        hours = [mulai + datetime.timedelta(hours=i) for i in range(24)]
        for device in self.devices:
            if device.tipe == 'arr':
                rst = device.periodik.filter(
                    Periodik.sampling.between(
                        mulai, akhir)).order_by(Periodik.sampling)
                dict_rst = dict([(r.sampling, r.rain or 0) for r in rst])
                data = dict([(h, []) for h in hours])
                dt = [data[t].append(v) for t, l in data.items() for k, v in
                      dict_rst.items() if k.hour == t.hour]
                ret[device.sn] = {'count': rst.count(),
                                  'hourly': data}

        return ret

class Periodik(db.Model):
    __tablename__ = 'periodik'

    id = db.Column(db.Integer, primary_key=True)
    sampling = db.Column(db.DateTime, index=True)
    device_sn = db.Column(db.String(8), db.ForeignKey('device.sn'))
    lokasi_id = db.Column(db.Integer, db.ForeignKey('lokasi.id'), nullable=True)
    mdpl = db.Column(db.Float)
    apre = db.Column(db.Float)
    sq = db.Column(db.Integer)
    temp = db.Column(db.Float)
    humi = db.Column(db.Float)
    batt = db.Column(db.Float)
    rain = db.Column(db.Float) # hujan dalam mm
    wlev = db.Column(db.Float) # TMA dalam centi
    up_s = db.Column(db.DateTime) # Up Since
    ts_a = db.Column(db.DateTime) # Time Set at
    received = db.Column(db.DateTime, default=datetime.datetime.utcnow)
    device = relationship("Device", back_populates="periodik")
    lokasi = relationship("Lokasi", back_populates="periodik")
    __table_args__ = (db.UniqueConstraint('device_sn', 'sampling',
                                          name='_device_sampling'),)

    def __repr__(self):
        return '<Periodik {} Device {}>'.format(self.sampling, self.device_sn)
    @classmethod
    def temukan_hujan(self, sejak=None):
        '''return periodik yang rain > 0'''
        dari = 30 # hari lalu
        if not sejak:
            sejak = datetime.datetime.now() - datetime.timedelta(days=dari)
            sejak = sejak.replace(minute=0, hour=7)
        data = [d for d in self.query.filter(self.sampling >=
                                             sejak).order_by(self.sampling)]
        lokasi_hari_hujan = [d.lokasi_id for d in data if (d.rain or 0) > 0]
        print(lokasi_hujan)
