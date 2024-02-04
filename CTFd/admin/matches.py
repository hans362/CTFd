from flask import redirect, render_template, request, url_for

from CTFd.admin import admin
from CTFd.models import Challenges, MatchTeams, Matches, db
from CTFd.plugins import bypass_csrf_protection
from CTFd.utils.decorators import admins_only


@admin.route("/admin/matches")
@admins_only
def matches_listing():
    matches = Matches.query.all()
    return render_template("admin/matches/matches.html", matches=matches)

@admin.route("/admin/matches/create", methods=["GET", "POST"])
@admins_only
def matches_create():
    if request.method == "POST":
        name = request.form["name"]
        description = request.form["description"]
        start = request.form["start"]
        end = request.form["end"]
        max_team_size = request.form["max_team_size"]
        registration_deadline = request.form["registration_deadline"]
        visible = request.form["visible"] == "1"
        match = Matches(name=name, description=description, start=start, end=end, max_team_size=max_team_size, registration_deadline=registration_deadline, visible=visible)
        db.session.add(match)
        db.session.commit()
        return redirect(url_for("admin.matches_detail", match_id=match.id))
    else:
        return render_template("admin/matches/create.html")

@admin.route("/admin/matches/<int:match_id>", methods=["GET", "POST"])
@admins_only
def matches_detail(match_id):
    match = Matches.query.filter_by(id=match_id).first_or_404()
    if request.method == "POST":
        match.name = request.form["name"]
        match.description = request.form["description"]
        match.start = request.form["start"]
        match.end = request.form["end"]
        match.max_team_size = request.form["max_team_size"]
        match.registration_deadline = request.form["registration_deadline"]
        match.visible = request.form["visible"] == "1"
        db.session.commit()
        return redirect(url_for("admin.matches_detail", match_id=match.id))
    else:
        challenges = Challenges.query.filter(Challenges.id.notin_([c.id for c in match.challenges])).all()
        matchteams = MatchTeams.query.filter_by(match_id=match.id).all()
        return render_template("admin/matches/match.html", match=match, challenges=challenges, matchteams=matchteams)
    
@admin.route("/admin/matches/<int:match_id>/delete", methods=["POST"])
@admins_only
def matches_delete(match_id):
    match = Matches.query.filter_by(id=match_id).first_or_404()
    db.session.delete(match)
    db.session.commit()
    return redirect(url_for("admin.matches_listing"))

@admin.route("/admin/matches/<int:match_id>/challenges/add", methods=["POST"])
@admins_only
def matches_challenges_add(match_id):
    match = Matches.query.filter_by(id=match_id).first_or_404()
    challenge_id = request.form["challenge_id"]
    challenge = Challenges.query.filter_by(id=challenge_id).first_or_404()
    match.challenges.append(challenge)
    db.session.commit()
    return redirect(url_for("admin.matches_detail", match_id=match.id))

@admin.route("/admin/matches/<int:match_id>/challenges/remove", methods=["POST"])
@admins_only
def matches_challenges_remove(match_id):
    match = Matches.query.filter_by(id=match_id).first_or_404()
    challenge_id = request.form["challenge_id"]
    challenge = Challenges.query.filter_by(id=challenge_id).first_or_404()
    match.challenges.remove(challenge)
    db.session.commit()
    return redirect(url_for("admin.matches_detail", match_id=match.id))

@admin.route("/admin/matches/<int:match_id>/matchteams/delete", methods=["POST"])
@admins_only
def matches_matchteams_delete(match_id):
    matchteam_id = request.form["matchteam_id"]
    matchteam = MatchTeams.query.filter_by(id=matchteam_id, match_id=match_id).first_or_404()
    db.session.delete(matchteam)
    db.session.commit()
    return redirect(url_for("admin.matches_detail", match_id=match_id))