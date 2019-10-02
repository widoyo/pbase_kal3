"""
Informasi Curah Hujan untuk Publik (Web Internet)
"""
import datetime
from flask import Blueprint, render_template, abort, request, flash, redirect

from apps import db
from apps.models import Periodik, Lokasi

bp = Blueprint('curahhujan', __name__, template_folder='templates')

@bp.route('/')
def index():
    return render_template('curahhujan/index.html',
                           all_lokasi=Lokasi.query.all())
