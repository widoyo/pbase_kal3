import datetime
from flask import Blueprint, render_template, abort, request, flash, redirect
from flask_login import login_required

from apps import db
from apps.models import Lokasi, Periodik
from apps.forms import LokasiForm

bp = Blueprint('pos', __name__, template_folder='templates')

@bp.route('/')
@login_required
def index():
    all_lokasi = Lokasi.query.all()
    return render_template('pos/index.html', all_lokasi=all_lokasi)


@bp.route('/<lokasi_id>/delete', methods=['GET', 'POST'])
@login_required
def delete(lokasi_id):
    pos = Lokasi.query.get(lokasi_id)
    form = LokasiForm(obj=pos)
    if form.validate_on_submit():
        db.session.delete(pos)
        db.session.commit()
        flash("Sukses menghapus")
        return redirect('/pos')
    return render_template('pos/delete.html', pos=pos, form=form)



@bp.route('/<lokasi_id>/edit', methods=['GET', 'POST'])
@login_required
def edit(lokasi_id):
    pos = Lokasi.query.get(lokasi_id)
    form = LokasiForm(obj=pos)
    if form.validate_on_submit():
        pos.nama = form.nama.data
        pos.ll = form.ll.data
        db.session.commit()
        flash("Sukses mengedit")
        return redirect('/pos')
    return render_template('pos/edit.html', form=form)



@bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    form = LokasiForm()
    if form.validate_on_submit():
        lokasi = Lokasi(nama=form.nama.data, ll=form.ll.data)
        db.session.add(lokasi)
        db.session.commit()
        flash("Sukses menambah Lokasi Pos")
        return redirect('/pos')
    return render_template('pos/add.html', form=form)


@bp.route('/<lokasi>')
@login_required
def show(lokasi):
    sampling = datetime.date.today()
    lokasi = Lokasi.query.filter_by(id=lokasi).first_or_404()
    template_name = 'show_ch.html'
    hourly_rain = {}
    try:
        lokasi.hujan_hari(sampling).popitem()[1].get('hourly')
    except:
        pass
    periodik = [(k, v) for k, v in hourly_rain.items()]
    if lokasi.jenis == '2':
        template_name = 'show_tma.html'
        periodik = lokasi.periodik[0:30]
    return render_template('pos/' + template_name,
                           sampling=sampling,
                           lokasi=lokasi, periodik=periodik)
