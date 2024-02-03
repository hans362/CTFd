from flask import Blueprint, render_template

from CTFd.utils.decorators import (
    require_complete_profile,
    require_verified_emails,
)
from CTFd.utils.helpers import get_errors, get_infos
from CTFd.models import Matches

matches = Blueprint("matches", __name__)

@matches.route("/matches")
@require_complete_profile
@require_verified_emails
def listing():
    infos = get_infos()
    errors = get_errors()

    matches = Matches.query.filter_by(visible=True).all()

    return render_template("matches/matches.html", infos=infos, errors=errors, matches=matches)

@matches.route("/matches/<int:match_id>")
@require_complete_profile
@require_verified_emails
def detail(match_id):
    infos = get_infos()
    errors = get_errors()

    match = Matches.query.filter_by(visible=True, id=match_id).first_or_404()

    return render_template("matches/match.html", infos=infos, errors=errors, match=match, active="detail")

@matches.route("/matches/<int:match_id>/registration")
@require_complete_profile
@require_verified_emails
def registration(match_id):
    infos = get_infos()
    errors = get_errors()

    match = Matches.query.filter_by(visible=True, id=match_id).first_or_404()

    return render_template("matches/registration.html", infos=infos, errors=errors, match=match, active="registration")

@matches.route("/matches/<int:match_id>/challenges")
@require_complete_profile
@require_verified_emails
def challenges(match_id):
    infos = get_infos()
    errors = get_errors()

    match = Matches.query.filter_by(visible=True, id=match_id).first_or_404()

    return render_template("matches/challenges.html", infos=infos, errors=errors, match=match, active="challenges")

@matches.route("/matches/<int:match_id>/scoreboard")
@require_complete_profile
@require_verified_emails
def scoreboard(match_id):
    infos = get_infos()
    errors = get_errors()

    match = Matches.query.filter_by(visible=True, id=match_id).first_or_404()

    return render_template("matches/scoreboard.html", infos=infos, errors=errors, match=match, active="scoreboard")