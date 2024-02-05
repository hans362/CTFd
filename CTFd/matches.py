import datetime
from flask import Blueprint, json, redirect, render_template, request, url_for

from CTFd.utils.decorators import (
    authed_only,
    require_complete_profile,
    require_verified_emails,
)
from CTFd.utils.helpers import get_errors, get_infos
from CTFd.models import Challenges, MatchTeams, Matches, Solves, db
from CTFd.utils.user import get_current_user

matches = Blueprint("matches", __name__)
    
def match_started(match):
    return match.start < datetime.datetime.now()

def match_ended(match):
    return match.end < datetime.datetime.now()

def match_registration_open(match):
    return match.registration_deadline > datetime.datetime.now()

def user_registered(match):
    user = get_current_user()
    matchteams = MatchTeams.query.filter_by(match_id=match.id).all()
    for matchteam in matchteams:
        if user in matchteam.users:
            return True
    return False

def get_user_matchteam(match):
    user = get_current_user()
    matchteams = MatchTeams.query.filter_by(match_id=match.id).all()
    for matchteam in matchteams:
        if user in matchteam.users:
            return matchteam
    return None

def get_solve_ids_for_matchteam(matchteam):
    solve_ids = set()
    for user in matchteam.users:
        user_solve_ids = (
            Solves.query.with_entities(Solves.challenge_id)
            .filter(Solves.account_id == user.account_id, Solves.date >= matchteam.match.start, Solves.date <= matchteam.match.end, Solves.challenge_id.in_([challenge.id for challenge in matchteam.match.challenges]))
            .all()
        )
        user_solve_ids = {value for value, in user_solve_ids}
        solve_ids = solve_ids.union(user_solve_ids)
    return solve_ids

def get_solves_for_matchteam(matchteam):
    solves = []
    for user in matchteam.users:
        user_solves = (
            Solves.query.filter(Solves.account_id == user.account_id, Solves.date >= matchteam.match.start, Solves.date <= matchteam.match.end, Solves.challenge_id.in_([challenge.id for challenge in matchteam.match.challenges]))
            .all()
        )
        solves.extend(user_solves)
    solves.sort(key=lambda x: (x.challenge_id, x.id))
    solves = [solves[i] for i in range(len(solves)) if i == 0 or solves[i].challenge_id != solves[i-1].challenge_id]
    solves.sort(key=lambda x: x.id)
    return solves

@matches.route("/matches")
@authed_only
@require_complete_profile
@require_verified_emails
def listing():
    infos = get_infos()
    errors = get_errors()
    matches = Matches.query.filter_by(visible=True).all()
    return render_template("matches/matches.html", infos=infos, errors=errors, matches=matches)

@matches.route("/matches/<int:match_id>")
@authed_only
@require_complete_profile
@require_verified_emails
def detail(match_id):
    infos = get_infos()
    errors = get_errors()
    match = Matches.query.filter_by(visible=True, id=match_id).first_or_404()
    return render_template("matches/match.html", infos=infos, errors=errors, match=match, active="detail")

@matches.route("/matches/<int:match_id>/registration", methods=["GET", "POST"])
@authed_only
@require_complete_profile
@require_verified_emails
def registration(match_id):
    infos = get_infos()
    errors = get_errors()
    match = Matches.query.filter_by(visible=True, id=match_id).first_or_404()
    matchteam = get_user_matchteam(match)
    if matchteam:
        infos.append(f"您已成功报名")
    elif not match_registration_open(match):
        errors.append("报名已结束")
    elif request.method == "POST":
        user = get_current_user()
        if request.form.get("team_token"):
            token = request.form.get("team_token")
            matchteam = MatchTeams.query.filter_by(token=token, match_id=match.id).first()
            if matchteam:
                if len(matchteam.users) >= match.max_team_size:
                    errors.append("队伍人数已达上限")
                    matchteam = None
                else:
                    matchteam.users.append(user)
                    db.session.commit()
                    return redirect(url_for("matches.registration", match_id=match_id))
            else:
                errors.append("无效的队伍邀请码")
        else:
            name = request.form.get("team_name")
            description = request.form.get("team_description")
            if not name:
                errors.append("队伍名称不能为空")
            elif not description:
                errors.append("队伍描述不能为空")
            else:
                matchteam = MatchTeams(name=name, description=description, match_id=match.id)
                matchteam.users.append(user)
                db.session.add(matchteam)
                db.session.commit()
                return redirect(url_for("matches.registration", match_id=match_id))
    else:
        infos.append("请先完成报名")
    return render_template("matches/registration.html", infos=infos, errors=errors, match=match, matchteam=matchteam, active="registration")

@matches.route("/matches/<int:match_id>/challenges")
@authed_only
@require_complete_profile
@require_verified_emails
def challenges(match_id):
    infos = get_infos()
    errors = get_errors()
    match = Matches.query.filter_by(visible=True, id=match_id).first_or_404()
    solve_ids = set()
    if not user_registered(match):
        return redirect(url_for("matches.registration", match_id=match_id))
    challenges = {}
    if not match_started(match):
        infos.append("比赛未开始")
    elif match_ended(match):
        infos.append("比赛已结束")
    else:
        for challenge in match.challenges:
            if challenge.category not in challenges:
                challenges[challenge.category] = []
            challenges[challenge.category].append(challenge)
        matchteam = get_user_matchteam(match)
        solve_ids = get_solve_ids_for_matchteam(matchteam)
    return render_template("matches/challenges.html", infos=infos, errors=errors, match=match, challenges=challenges, solve_ids=solve_ids, active="challenges")

@matches.route("/matches/<int:match_id>/scoreboard", methods=["GET", "POST"])
@authed_only
@require_complete_profile
@require_verified_emails
def scoreboard(match_id):
    infos = get_infos()
    errors = get_errors()
    match = Matches.query.filter_by(visible=True, id=match_id).first_or_404()
    if not user_registered(match):
        return redirect(url_for("matches.registration", match_id=match_id))
    matchteams = MatchTeams.query.filter_by(match_id=match.id).all()
    scoreboard = {}
    graph = {}
    if request.method == "POST":
        for matchteam in matchteams:
            solves = get_solves_for_matchteam(matchteam)
            score = 0
            graph[matchteam.name] = [(match.start.timestamp()*1000, 0)]
            for solve in solves:
                score += solve.challenge.value
                graph[matchteam.name].append((solve.date.replace(tzinfo=datetime.timezone.utc).timestamp()*1000, score))
        return json.dumps(graph)
    else:
        for matchteam in matchteams:
            solves = get_solves_for_matchteam(matchteam)
            scoreboard[matchteam] = {'score': 0, 'solve_count': 0, 'last_solve_date': None}
            for solve in solves:
                scoreboard[matchteam]['score'] += solve.challenge.value
            scoreboard[matchteam]['solve_count'] = len(solves)
            scoreboard[matchteam]['last_solve_date'] = solves[-1].date if solves else None
        scoreboard = dict(sorted(scoreboard.items(), key=lambda item: (item[1]['score'], -item[1]['last_solve_date'].timestamp()), reverse=True))
    return render_template("matches/scoreboard.html", infos=infos, errors=errors, match=match, scoreboard=scoreboard, active="scoreboard")