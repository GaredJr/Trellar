from flask import Flask, abort, render_template

app = Flask(__name__, template_folder="Templates")

BOARDS = [
    {
        "slug": "product-roadmap",
        "name": "Product Roadmap",
        "description": "Plan features, milestones, and releases for the next quarter.",
        "members": 6,
    },
    {
        "slug": "marketing-sprint",
        "name": "Marketing Sprint",
        "description": "Coordinate campaign tasks, creative reviews, and launch timelines.",
        "members": 4,
    },
    {
        "slug": "engineering-backlog",
        "name": "Engineering Backlog",
        "description": "Track improvements, bug fixes, and technical debt in one place.",
        "members": 8,
    },
]

BOARD_DETAILS = {
    "product-roadmap": {
        "name": "Product Roadmap",
        "description": "Q2 planning board for high-impact initiatives.",
        "lanes": [
            {
                "name": "Backlog",
                "cards": [
                    {"title": "Audit onboarding drop-off points", "meta": "Research - 2d"},
                    {"title": "Draft release notes template", "meta": "Docs - 1d"},
                    {"title": "Collect feedback from design review", "meta": "Design - 3h"},
                ],
            },
            {
                "name": "In Progress",
                "cards": [
                    {"title": "Build dashboard usage report", "meta": "Analytics - 1d"},
                    {"title": "Refine billing settings flow", "meta": "Frontend - 2d"},
                ],
            },
            {
                "name": "Review",
                "cards": [
                    {"title": "QA test automation alerts", "meta": "QA - Today"},
                    {"title": "Security checklist update", "meta": "Platform - 5h"},
                ],
            },
            {
                "name": "Done",
                "cards": [
                    {"title": "Migrate legacy team permissions", "meta": "Backend - Complete"},
                    {"title": "Refresh board performance budget", "meta": "Ops - Complete"},
                ],
            },
        ],
    },
    "marketing-sprint": {
        "name": "Marketing Sprint",
        "description": "Two-week campaign execution workflow.",
        "lanes": [
            {
                "name": "Ideas",
                "cards": [
                    {"title": "Landing page variant test", "meta": "Growth - 1w"},
                    {"title": "Partner webinar concept", "meta": "Brand - 4d"},
                ],
            },
            {
                "name": "Doing",
                "cards": [
                    {"title": "Write social teaser copy", "meta": "Content - 1d"},
                ],
            },
            {
                "name": "Done",
                "cards": [
                    {"title": "Publish April campaign brief", "meta": "PMM - Complete"},
                ],
            },
        ],
    },
    "engineering-backlog": {
        "name": "Engineering Backlog",
        "description": "Shared triage and delivery board for core platform work.",
        "lanes": [
            {
                "name": "Triage",
                "cards": [
                    {"title": "Rate-limit login endpoint", "meta": "Security - 3h"},
                    {"title": "Investigate flaky CI suite", "meta": "Infra - 5h"},
                ],
            },
            {
                "name": "Planned",
                "cards": [
                    {"title": "Add board activity filters", "meta": "API - 2d"},
                    {"title": "Optimize lane query payload", "meta": "Backend - 1d"},
                ],
            },
            {
                "name": "Shipped",
                "cards": [
                    {"title": "Cache avatar lookups", "meta": "Perf - Complete"},
                ],
            },
        ],
    },
}

ACTIVITY_ITEMS = [
    {
        "title": "Moved \"Refine billing settings flow\" to Review",
        "meta": "Product Roadmap - 12 minutes ago",
    },
    {
        "title": "Added card \"Rate-limit login endpoint\"",
        "meta": "Engineering Backlog - 1 hour ago",
    },
    {
        "title": "Completed \"Publish April campaign brief\"",
        "meta": "Marketing Sprint - 2 hours ago",
    },
    {
        "title": "Updated board permissions",
        "meta": "Workspace Admin - Yesterday",
    },
]


@app.route("/")
def home():
    return render_template(
        "home.html",
        title="Home | Trellar",
        active_page="home",
        boards=BOARDS,
    )


@app.route("/user")
def user():
    return render_template("user.html", title="User | Trellar", active_page="user")


@app.route("/boards")
def boards():
    return render_template(
        "boards.html",
        title="Boards | Trellar",
        active_page="boards",
        boards=BOARDS,
    )


@app.route("/board")
def board_alias():
    return board("product-roadmap")


@app.route("/boards/<slug>")
def board(slug):
    board_data = BOARD_DETAILS.get(slug)
    if board_data is None:
        abort(404)

    return render_template(
        "board.html",
        title=f"{board_data['name']} | Trellar",
        active_page="boards",
        board=board_data,
        board_slug=slug,
    )


@app.route("/settings")
def settings():
    return render_template("settings.html", title="Settings | Trellar", active_page="settings")


@app.route("/activity")
def activity():
    return render_template(
        "activity.html",
        title="Activity | Trellar",
        active_page="activity",
        activity_items=ACTIVITY_ITEMS,
    )


if __name__ == "__main__":
    app.run(debug=True)
