from flask import Blueprint, render_template
from flask_login import login_required

bp = Blueprint('fluxograma', __name__)

@bp.route('/fluxograma')
@login_required
def fluxograma():
    return render_template('fluxograma.html')
