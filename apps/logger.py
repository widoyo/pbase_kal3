'''
logger module

Widoyo <widoyo@gmail.com>
'''
import datetime

from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required

from sqlalchemy import text, func

from apps.models import Device, Periodik, Lokasi
from apps.forms import LoggerSettingForm
from apps import db

bp = Blueprint('logger', __name__)


@bp.route('/')
@login_required
def index():
    '''Showing all logger'''
    all_devices = Device.query.order_by('sn').all()
    return render_template('logger/index.html', all_devices=all_devices)

@bp.route('/sehat')
@login_required
def sehat():
    '''Showing number incoming data each hour'''
    all_devices = []
    sql = text("SELECT sampling::date, date_part('hour', sampling) AS hour, COUNT(*) \
               FROM periodik \
               WHERE device_sn=:sn AND sampling::date=:sampling \
               GROUP BY sampling::date, date_part('hour', sampling) \
               ORDER BY sampling")
    sampling = datetime.datetime.strptime(request.args.get('sampling'),
                                          '%Y-%m-%d').date() if request.args.get('sampling') else datetime.date.today()
    prev = sampling - datetime.timedelta(days=1)
    i_next = sampling + datetime.timedelta(days=1)
    for d in Device.query.filter(Device.lokasi!=None).order_by('sn'):
        res = db.engine.execute(sql, sn=d.sn, sampling=str(sampling))
        hourly = dict([r[1:] for r in res])
        hourly_count = [(i, hourly.get(i, 0)) for i in range(0, 24)]
        all_devices.append({'device': d, 'hourly_count': hourly_count})
    return render_template('logger/sehat.html', sampling=sampling, 
                           all_devices=all_devices, prev=prev,
                          next=i_next)

@bp.route('/<sn>/sampling')
@login_required
def sampling(sn):
    '''Showing specific Periodic data on such logger'''
    device = Device.query.filter_by(sn=sn).first_or_404()
    return render_template('logger/sampling.html', device=device)

@bp.route('/<sn>', methods=["GET", "POST"])
@login_required
def show(sn):
    page = int(request.args.get('p', 1))
    per_page = int(request.args.get('n', 25))
    device = Device.query.filter_by(sn=sn).first_or_404()
    now = datetime.datetime.now()
    paginate = Periodik.query.filter(
        Periodik.device_sn == device.sn,
        Periodik.sampling <= now).order_by(
            Periodik.sampling.desc()).paginate(page, per_page)
    init_data = {'temp_cor': device.temp_cor or 0,
                 'humi_cor': device.humi_cor or 0,
                 'batt_cor': device.batt_cor or 0}
    if device.tipe == 'arr':
        init_data.update({'tipp_fac': device.tipp_fac or 1})
    form = LoggerSettingForm(obj=device)
    form.lokasi_id.choices = [(l.id, l.nama) for l in Lokasi.query.all()]
    monthly_download_list = db.engine.execute(text(
        "SELECT DISTINCT(TO_CHAR(sampling, 'YYYY-mm-01')) \
        FROM periodik \
        WHERE device_sn=:sn"), sn=device.sn)
    #print('monthly_download_list:', [r[0] for r in monthly_download_list])
    if form.validate_on_submit():
        if device.tipe == 'arr':
            device.tipp_fac = form.tipp_fac.data
        else:
            device.ting_son = form.ting_son.data
        device.temp_cor = form.temp_cor.data
        device.humi_cor = form.humi_cor.data
        device.batt_cor = form.batt_cor.data
        device.lokasi_id = int(form.lokasi_id.data)
        db.session.commit()
        return redirect(url_for('logger.show', sn=sn))
    return render_template('logger/show.html', device=device, form=form, 
                           pagination=paginate,
                           month_list=[r[0] for r in monthly_download_list])

@bp.route('/add')
def add():
    return render_template('logger/add.html')
