import math

from core.config import REPLAY_MAX_EVENTS, REPLAY_MAX_POINTS, REPLAY_MAX_STROKES
from schemas.data import Game, ReplayAction, ReplayEvent, ReplayPoint, ReplayStroke


def clamp_coordinate(value: float) -> float:
    return max(0.0, min(1.0, value))


def parse_point(value: object) -> ReplayPoint | None:
    if not isinstance(value, dict):
        return None

    x = value.get("x")
    y = value.get("y")
    if not isinstance(x, (int, float)) or not isinstance(y, (int, float)):
        return None
    if not math.isfinite(x) or not math.isfinite(y):
        return None

    return ReplayPoint(x=clamp_coordinate(float(x)), y=clamp_coordinate(float(y)))


def sanitize_drawing(value: object) -> list[ReplayStroke]:
    if not isinstance(value, list):
        return []

    strokes = []
    point_count = 0

    for raw_stroke in value[:REPLAY_MAX_STROKES]:
        if point_count >= REPLAY_MAX_POINTS:
            break
        if not isinstance(raw_stroke, dict):
            continue

        raw_points = raw_stroke.get("points")
        if not isinstance(raw_points, list):
            continue

        points = []
        for raw_point in raw_points:
            if point_count >= REPLAY_MAX_POINTS:
                break
            point = parse_point(raw_point)
            if point is None:
                continue
            points.append(point)
            point_count += 1

        if points:
            strokes.append(ReplayStroke(points=points))

    return strokes


def create_initial_replay_timeline() -> list[ReplayEvent]:
    return [
        ReplayEvent(
            elapsed=0,
            score=0,
            action=ReplayAction.REPLACE,
            strokes=[],
        )
    ]


def get_replay_timeline(game: Game, username: str) -> list[ReplayEvent]:
    timeline = game.replay_timelines.get(username)
    if timeline is None:
        timeline = create_initial_replay_timeline()
        game.replay_timelines[username] = timeline
    return timeline


def points_start_with(points: list[ReplayPoint], prefix: list[ReplayPoint]) -> bool:
    return len(points) >= len(prefix) and points[: len(prefix)] == prefix


def create_drawing_event(
    previous: list[ReplayStroke],
    current: list[ReplayStroke],
    elapsed: float,
    score: float,
) -> ReplayEvent | None:
    if previous == current:
        return None
    if not current:
        return ReplayEvent(elapsed=elapsed, score=score, action=ReplayAction.CLEAR)
    if len(current) + 1 == len(previous) and current == previous[:-1]:
        return ReplayEvent(
            elapsed=elapsed,
            score=score,
            action=ReplayAction.REMOVE_STROKE,
        )
    if len(current) == len(previous) + 1 and current[:-1] == previous:
        return ReplayEvent(
            elapsed=elapsed,
            score=score,
            action=ReplayAction.APPEND_STROKE,
            points=list(current[-1].points),
        )
    if (
        len(current) == len(previous)
        and current[:-1] == previous[:-1]
        and points_start_with(current[-1].points, previous[-1].points)
    ):
        return ReplayEvent(
            elapsed=elapsed,
            score=score,
            action=ReplayAction.APPEND_POINTS,
            points=list(current[-1].points[len(previous[-1].points) :]),
        )
    return ReplayEvent(
        elapsed=elapsed,
        score=score,
        action=ReplayAction.REPLACE,
        strokes=list(current),
    )


def append_replay_event(game: Game, username: str, event: ReplayEvent | None) -> None:
    if event is None:
        return
    timeline = get_replay_timeline(game, username)
    if len(timeline) < REPLAY_MAX_EVENTS:
        timeline.append(event)


def record_drawing_change(
    game: Game,
    username: str,
    drawing: list[ReplayStroke],
    elapsed: float,
) -> None:
    previous = game.drawings.get(username, [])
    score = game.scores.get(username, 0)
    event = create_drawing_event(previous, drawing, elapsed, score)
    game.drawings[username] = drawing
    append_replay_event(game, username, event)


def record_score_change(game: Game, username: str, elapsed: float) -> None:
    timeline = get_replay_timeline(game, username)
    score = game.scores.get(username, 0)
    if timeline and timeline[-1].score == score:
        return
    append_replay_event(
        game,
        username,
        ReplayEvent(elapsed=elapsed, score=score, action=ReplayAction.SCORE),
    )


def finalize_replay_timeline(game: Game, username: str, elapsed: float) -> None:
    timeline = get_replay_timeline(game, username)
    event = ReplayEvent(
        elapsed=elapsed,
        score=game.scores.get(username, 0),
        action=ReplayAction.REPLACE,
        strokes=list(game.drawings.get(username, [])),
    )
    if len(timeline) >= REPLAY_MAX_EVENTS:
        timeline[-1] = event
    else:
        timeline.append(event)
