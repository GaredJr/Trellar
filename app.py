from __future__ import annotations

import csv
from copy import deepcopy
from datetime import datetime, timezone
from hmac import compare_digest
from io import StringIO
from typing import Any
from urllib.parse import urlparse
import os
import re
import secrets

from flask import (
    Flask,
    abort,
    flash,
    jsonify,
    make_response,
    redirect,
    render_template,
    request,
    send_from_directory,
    session,
    url_for,
)
from werkzeug.security import check_password_hash, generate_password_hash

try:
    from supabase import Client, create_client
except Exception:  # pragma: no cover - optional dependency for local/demo mode
    Client = Any  # type: ignore[assignment]
    create_client = None


def load_env_file(path: str = ".env") -> None:
    env_path = os.path.join(os.path.dirname(__file__), path)
    if not os.path.exists(env_path):
        return

    try:
        with open(env_path, encoding="utf-8") as env_file:
            lines = env_file.readlines()
    except OSError:
        return

    for raw_line in lines:
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        if not key or key in os.environ:
            continue

        parsed_value = value.strip()
        if len(parsed_value) >= 2 and parsed_value[0] == parsed_value[-1] and parsed_value[0] in {"'", '"'}:
            parsed_value = parsed_value[1:-1]
        os.environ[key] = parsed_value


load_env_file()

app = Flask(__name__, template_folder="Templates")
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "trellar-dev-secret-change-me")

AVAILABLE_LANGUAGES = ("en", "nb", "ar")
RTL_LANGUAGES = {"ar"}

TRANSLATIONS = {
    "en": {
        "brand.name": "Trellar",
        "skip.main": "Skip to main content",
        "skip.nav": "Skip to navigation",
        "skip.board": "Skip to board lanes",
        "nav.menu": "Menu",
        "nav.home": "Home",
        "nav.boards": "Boards",
        "nav.activity": "Activity",
        "nav.user": "User",
        "nav.settings": "Settings",
        "nav.help": "Help",
        "nav.login": "Login",
        "nav.signup": "Sign up",
        "nav.logout": "Logout",
        "topnav.swipe_hint": "Tip: on small screens, swipe to see all navigation tabs.",
        "lang.label": "Language",
        "lang.submit": "Apply",
        "lang.name.en": "English",
        "lang.name.nb": "Norsk Bokmal",
        "lang.name.ar": "Arabic",
        "prefs.title": "Display",
        "prefs.description": "Personal display preferences are saved on this device.",
        "prefs.theme": "Theme",
        "prefs.theme.system": "System",
        "prefs.theme.dark": "Dark",
        "prefs.theme.light": "Light",
        "prefs.contrast": "Contrast",
        "prefs.contrast.default": "Default",
        "prefs.contrast.more": "More contrast",
        "prefs.text": "Text size",
        "prefs.text.default": "Default",
        "prefs.text.large": "Large",
        "prefs.motion": "Motion",
        "prefs.motion.default": "Default",
        "prefs.motion.reduce": "Reduce motion",
        "prefs.save": "Save preferences",
        "common.close": "Close",
        "common.search": "Search",
        "common.sort": "Sort",
        "common.filter": "Filter",
        "common.required": "Required",
        "common.save": "Save",
        "common.reset": "Reset",
        "common.cancel": "Cancel",
        "common.view": "View",
        "common.open": "Open",
        "common.export": "Export",
        "common.create": "Create",
        "common.load_more": "Load more",
        "common.undo": "Undo",
        "breadcrumbs.home": "Home",
        "breadcrumbs.boards": "Boards",
        "breadcrumbs.activity": "Activity",
        "breadcrumbs.user": "User",
        "breadcrumbs.settings": "Settings",
        "breadcrumbs.help": "Help",
        "footer.tagline": "Accessible project workspace",
        "footer.privacy": "Activity privacy",
        "footer.checklist": "UU checklist",
        "footer.budget": "Performance budget",
        "flash.language_updated": "Language updated.",
        "flash.csrf_error": "Security token expired. Please try again.",
        "flash.profile_saved": "Profile details saved.",
        "flash.settings_saved": "Workspace settings saved.",
        "flash.validation_error": "Please correct the highlighted fields.",
        "flash.login_success": "Signed in.",
        "flash.login_failed": "Invalid email or password.",
        "flash.logged_out": "Signed out.",
        "flash.signup_success": "Account created. You are now signed in.",
        "flash.signup_confirm": "Account created. Check your email to confirm your account.",
        "flash.signup_failed": "Could not create account right now.",
        "flash.supabase_not_configured": "Supabase is not configured on this server yet.",
        "meta.home": "Home | Trellar",
        "meta.login": "Login | Trellar",
        "meta.signup": "Sign up | Trellar",
        "meta.user": "User | Trellar",
        "meta.boards": "Boards | Trellar",
        "meta.settings": "Settings | Trellar",
        "meta.activity": "Activity | Trellar",
        "meta.help": "Help | Trellar",
        "meta.not_found": "Page Not Found | Trellar",
        "meta.server_error": "Server Error | Trellar",
        "home.eyebrow": "Workspace Overview",
        "home.title": "Plan faster with boards that stay focused.",
        "home.lead": "Trellar keeps your team aligned with clean, readable boards and a calm workflow.",
        "home.open_boards": "Open boards",
        "home.open_sample": "Open sample board",
        "home.recent_title": "Recent boards",
        "home.view_all": "View all",
        "home.quick_title": "Quick actions",
        "home.quick_help": "Use the Help page to learn keyboard navigation and card movement shortcuts.",
        "home.quick_link": "Open keyboard help",
        "boards.eyebrow": "Workspace",
        "boards.title": "Boards",
        "boards.lead": "All active boards in your workspace.",
        "boards.create": "Create board",
        "boards.create_prompt_name": "Board name",
        "boards.create_prompt_description": "Board description (optional)",
        "boards.create_error": "Could not create board right now.",
        "boards.filters": "Board filters",
        "boards.toggle_filters": "Show filters",
        "boards.search_label": "Search boards",
        "boards.search_placeholder": "Search by board name or description",
        "boards.sort_label": "Sort boards",
        "boards.sort.name_asc": "Name A-Z",
        "boards.sort.name_desc": "Name Z-A",
        "boards.sort.members_desc": "Members high to low",
        "boards.sort.members_asc": "Members low to high",
        "boards.member_label": "Team size",
        "boards.member.all": "All",
        "boards.member.small": "Small (1-4)",
        "boards.member.medium": "Medium (5-6)",
        "boards.member.large": "Large (7+)",
        "boards.status": "Showing {count} board(s). Sorted by {sort_label}.",
        "boards.empty_title": "No boards found",
        "boards.empty_text": "Try a different search phrase or filter.",
        "boards.members": "{count} members",
        "boards.open": "Open board",
        "board.eyebrow": "Board",
        "board.filter": "Filter",
        "board.invite": "Invite",
        "board.add_card": "Add card",
        "board.add_prompt_title": "Card title",
        "board.add_prompt_meta": "Card details (optional)",
        "board.add_error": "Could not add card right now.",
        "board.added": "Added \"{title}\" to {lane}.",
        "board.lane_scroll_help": "Board lanes are horizontally scrollable. Swipe, Shift+wheel, or arrow-key scroll to reach more lanes.",
        "board.card_actions": "Card actions",
        "board.move_left": "Move left",
        "board.move_right": "Move right",
        "board.archive": "Archive",
        "board.add_to_lane": "Add a card to {lane}",
        "board.cards_count": "{count} cards",
        "board.status_prefix": "Status",
        "board.shortcuts_title": "Keyboard shortcuts",
        "board.shortcuts_text": "Focus a card and press Alt + Left/Right to move it between lanes.",
        "board.shortcuts_link": "Open full shortcuts help",
        "board.moved": "Moved \"{title}\" to {lane}.",
        "board.archived": "Archived \"{title}\".",
        "board.undo_done": "Action undone.",
        "board.confirm_archive": "Archive this card? You can undo right after.",
        "user.title": "User profile",
        "user.subtitle": "Workspace owner and project coordination",
        "user.profile": "Profile",
        "user.display_name": "Display name",
        "user.display_name_help": "The name shown to teammates across all boards.",
        "user.email": "Email",
        "user.email_help": "Used for account alerts and activity summaries.",
        "user.about": "About",
        "user.about_help": "Add a short description that helps collaborators identify your role.",
        "user.stats.boards": "Boards",
        "user.stats.open_cards": "Open cards",
        "user.stats.active": "Last active",
        "user.stats.boards_value": "12",
        "user.stats.open_cards_value": "24",
        "user.stats.active_value": "20m ago",
        "settings.eyebrow": "Workspace",
        "settings.title": "Settings",
        "settings.lead": "Manage team preferences, notifications, and board defaults.",
        "settings.general": "General",
        "settings.workspace_name": "Workspace name",
        "settings.workspace_help": "Shown in board headers and workspace invitations.",
        "settings.default_visibility": "Default visibility",
        "settings.visibility_help": "Controls how new boards are shared by default.",
        "settings.visibility.private": "Private",
        "settings.visibility.workspace": "Workspace",
        "settings.visibility.public": "Public",
        "settings.notifications": "Notifications",
        "settings.digest": "Email digest frequency",
        "settings.digest_help": "Choose how often workspace summaries are sent.",
        "settings.digest.daily": "Daily",
        "settings.digest.weekly": "Weekly",
        "settings.digest.off": "Off",
        "settings.channel": "Channel",
        "settings.channel_help": "Default destination for automated project updates.",
        "settings.automation": "Automation",
        "settings.card_template": "Card template",
        "settings.card_template_help": "Applied when new cards are created from templates.",
        "settings.template_default": "Owner - Due date - Acceptance criteria",
        "activity.eyebrow": "Workspace",
        "activity.title": "Activity",
        "activity.lead": "Recent board and card activity from your team.",
        "activity.export": "Export log",
        "activity.feed_title": "Activity feed",
        "activity.privacy_title": "Activity privacy",
        "activity.privacy_text": "Only workspace members can view this activity feed. Exports should be stored according to your team privacy policy.",
        "activity.loaded": "Loaded {count} activities.",
        "activity.empty_title": "No activity yet",
        "activity.empty_text": "Actions on boards and cards will appear here.",
        "help.title": "Keyboard help",
        "help.lead": "Use these shortcuts for faster navigation and accessible board management.",
        "help.section_nav": "Navigation",
        "help.section_board": "Board actions",
        "help.section_forms": "Forms",
        "help.key": "Shortcut",
        "help.action": "Action",
        "help.nav_tab": "Tab / Shift+Tab",
        "help.nav_tab_action": "Move focus forward/backward",
        "help.nav_skip": "Skip links",
        "help.nav_skip_action": "Jump to main content or navigation",
        "help.board_move": "Alt + Left/Right",
        "help.board_move_action": "Move focused card to previous/next lane",
        "help.board_menu": "Enter on card menu",
        "help.board_menu_action": "Open contextual card actions",
        "help.forms_submit": "Enter",
        "help.forms_submit_action": "Submit form",
        "help.forms_reset": "Reset button",
        "help.forms_reset_action": "Triggers a confirmation dialog",
        "login.title": "Sign in",
        "login.subtitle": "Use your workspace account to continue.",
        "login.email": "Email",
        "login.email_help": "Use the email address for your Trellar account.",
        "login.password": "Password",
        "login.password_help": "Enter your account password.",
        "login.submit": "Sign in",
        "login.create_account": "Create account",
        "login.demo_hint": "Demo login: {email} / {password}",
        "signup.title": "Create account",
        "signup.subtitle": "Sign up with email and password to start using Trellar.",
        "signup.email": "Email",
        "signup.password": "Password",
        "signup.password_help": "Use at least 8 characters.",
        "signup.password_confirm": "Confirm password",
        "signup.submit": "Create account",
        "signup.already_have": "Already have an account?",
        "error.required": "This field is required.",
        "error.max_length": "Use {max} characters or fewer.",
        "error.invalid_email": "Enter a valid email address.",
        "error.invalid_option": "Choose one of the available options.",
        "error.password_mismatch": "Passwords do not match.",
        "error.password_length": "Password must be at least {min} characters.",
        "error.summary_title": "Please fix the following",
        "error.not_found_title": "Page not found",
        "error.not_found_text": "The page may have moved, or the address is incorrect.",
        "error.server_title": "Something went wrong",
        "error.server_text": "Try again in a moment. If the issue continues, contact support.",
        "error.go_home": "Go to home",
        "error.go_boards": "Go to boards",
        "confirm.title": "Please confirm",
        "confirm.accept": "Confirm",
        "confirm.cancel": "Cancel",
        "status.saving": "Saving...",
    },
    "nb": {
        "brand.name": "Trellar",
        "skip.main": "Hopp til hovedinnhold",
        "skip.nav": "Hopp til navigasjon",
        "skip.board": "Hopp til board-kolonner",
        "nav.menu": "Meny",
        "nav.home": "Hjem",
        "nav.boards": "Boards",
        "nav.activity": "Aktivitet",
        "nav.user": "Bruker",
        "nav.settings": "Innstillinger",
        "nav.help": "Hjelp",
        "nav.login": "Logg inn",
        "nav.signup": "Registrer",
        "nav.logout": "Logg ut",
        "topnav.swipe_hint": "Tips: pa sma skjermer kan du swipe for a se alle faner.",
        "lang.label": "Sprak",
        "lang.submit": "Bruk",
        "lang.name.en": "Engelsk",
        "lang.name.nb": "Norsk bokmal",
        "lang.name.ar": "Arabisk",
        "prefs.title": "Visning",
        "prefs.description": "Visningsvalg lagres pa denne enheten.",
        "prefs.theme": "Tema",
        "prefs.theme.system": "System",
        "prefs.theme.dark": "Mork",
        "prefs.theme.light": "Lys",
        "prefs.contrast": "Kontrast",
        "prefs.contrast.default": "Standard",
        "prefs.contrast.more": "Hoy kontrast",
        "prefs.text": "Tekststorrelse",
        "prefs.text.default": "Standard",
        "prefs.text.large": "Stor",
        "prefs.motion": "Bevegelse",
        "prefs.motion.default": "Standard",
        "prefs.motion.reduce": "Redusert",
        "prefs.save": "Lagre visning",
        "common.close": "Lukk",
        "common.search": "Sok",
        "common.sort": "Sorter",
        "common.filter": "Filter",
        "common.required": "Pamkrevd",
        "common.save": "Lagre",
        "common.reset": "Nullstill",
        "common.cancel": "Avbryt",
        "common.view": "Vis",
        "common.open": "Apne",
        "common.export": "Eksporter",
        "common.create": "Opprett",
        "common.load_more": "Last flere",
        "common.undo": "Angre",
        "breadcrumbs.home": "Hjem",
        "breadcrumbs.boards": "Boards",
        "breadcrumbs.activity": "Aktivitet",
        "breadcrumbs.user": "Bruker",
        "breadcrumbs.settings": "Innstillinger",
        "breadcrumbs.help": "Hjelp",
        "footer.tagline": "Tilgjengelig prosjektarbeidsflate",
        "footer.privacy": "Personvern for aktivitet",
        "footer.checklist": "UU-sjekkliste",
        "footer.budget": "Ytelsesbudsjett",
        "flash.language_updated": "Sprak oppdatert.",
        "flash.csrf_error": "Sikkerhetstoken utlop. Prov igjen.",
        "flash.profile_saved": "Profil lagret.",
        "flash.settings_saved": "Innstillinger lagret.",
        "flash.validation_error": "Rett feltene som er markert.",
        "flash.login_success": "Logget inn.",
        "flash.login_failed": "Ugyldig e-post eller passord.",
        "flash.logged_out": "Logget ut.",
        "flash.signup_success": "Konto opprettet. Du er na logget inn.",
        "flash.signup_confirm": "Konto opprettet. Sjekk e-post for a bekrefte kontoen.",
        "flash.signup_failed": "Kunne ikke opprette konto na.",
        "flash.supabase_not_configured": "Supabase er ikke satt opp pa serveren enda.",
        "meta.home": "Hjem | Trellar",
        "meta.login": "Logg inn | Trellar",
        "meta.signup": "Registrer | Trellar",
        "meta.user": "Bruker | Trellar",
        "meta.boards": "Boards | Trellar",
        "meta.settings": "Innstillinger | Trellar",
        "meta.activity": "Aktivitet | Trellar",
        "meta.help": "Hjelp | Trellar",
        "meta.not_found": "Side ikke funnet | Trellar",
        "meta.server_error": "Serverfeil | Trellar",
        "home.eyebrow": "Oversikt",
        "home.title": "Planlegg raskere med boards som holder fokus.",
        "home.lead": "Trellar holder teamet samlet med lesbare boards og rolig flyt.",
        "home.open_boards": "Apne boards",
        "home.open_sample": "Apne eksempelboard",
        "home.recent_title": "Nylige boards",
        "home.view_all": "Se alle",
        "home.quick_title": "Hurtigvalg",
        "home.quick_help": "Bruk hjelpesiden for tastaturnavigasjon og flytting av kort.",
        "home.quick_link": "Apne tastaturhjelp",
        "boards.eyebrow": "Arbeidsomrade",
        "boards.title": "Boards",
        "boards.lead": "Alle aktive boards i arbeidsomradet.",
        "boards.create": "Opprett board",
        "boards.create_prompt_name": "Navn pa board",
        "boards.create_prompt_description": "Beskrivelse av board (valgfri)",
        "boards.create_error": "Kunne ikke opprette board na.",
        "boards.filters": "Board-filtre",
        "boards.toggle_filters": "Vis filtre",
        "boards.search_label": "Sok i boards",
        "boards.search_placeholder": "Sok etter navn eller beskrivelse",
        "boards.sort_label": "Sorter boards",
        "boards.sort.name_asc": "Navn A-A",
        "boards.sort.name_desc": "Navn A-A (omvendt)",
        "boards.sort.members_desc": "Flest medlemmer forst",
        "boards.sort.members_asc": "Fa medlemmer forst",
        "boards.member_label": "Teamstorrelse",
        "boards.member.all": "Alle",
        "boards.member.small": "Liten (1-4)",
        "boards.member.medium": "Medium (5-6)",
        "boards.member.large": "Stor (7+)",
        "boards.status": "Viser {count} board(s). Sortert etter {sort_label}.",
        "boards.empty_title": "Ingen boards funnet",
        "boards.empty_text": "Prov et annet sok eller filter.",
        "boards.members": "{count} medlemmer",
        "boards.open": "Apne board",
        "board.eyebrow": "Board",
        "board.filter": "Filter",
        "board.invite": "Inviter",
        "board.add_card": "Legg til kort",
        "board.add_prompt_title": "Korttittel",
        "board.add_prompt_meta": "Kortdetaljer (valgfritt)",
        "board.add_error": "Kunne ikke legge til kort na.",
        "board.added": "La til \"{title}\" i {lane}.",
        "board.lane_scroll_help": "Board-kolonner kan rulles horisontalt. Swipe, Shift+rullehjul eller piltaster.",
        "board.card_actions": "Korthandlinger",
        "board.move_left": "Flytt til venstre",
        "board.move_right": "Flytt til hoyre",
        "board.archive": "Arkiver",
        "board.add_to_lane": "Legg til kort i {lane}",
        "board.cards_count": "{count} kort",
        "board.status_prefix": "Status",
        "board.shortcuts_title": "Tastatursnarveier",
        "board.shortcuts_text": "Fokuser et kort og trykk Alt + Venstre/Hoyre for a flytte kort.",
        "board.shortcuts_link": "Apne full hjelpeside",
        "board.moved": "Flyttet \"{title}\" til {lane}.",
        "board.archived": "Arkiverte \"{title}\".",
        "board.undo_done": "Handling angret.",
        "board.confirm_archive": "Arkivere dette kortet? Du kan angre rett etter.",
        "user.title": "Brukerprofil",
        "user.subtitle": "Arbeidsomradeeier og prosjektkoordinering",
        "user.profile": "Profil",
        "user.display_name": "Visningsnavn",
        "user.display_name_help": "Navnet som vises til teamet pa alle boards.",
        "user.email": "E-post",
        "user.email_help": "Brukes til varsler og aktivitetsoppsummeringer.",
        "user.about": "Om",
        "user.about_help": "Kort beskrivelse som hjelper teamet a forsta rollen din.",
        "user.stats.boards": "Boards",
        "user.stats.open_cards": "Apne kort",
        "user.stats.active": "Sist aktiv",
        "user.stats.boards_value": "12",
        "user.stats.open_cards_value": "24",
        "user.stats.active_value": "20m siden",
        "settings.eyebrow": "Arbeidsomrade",
        "settings.title": "Innstillinger",
        "settings.lead": "Administrer teamvalg, varsler og standarder for boards.",
        "settings.general": "Generelt",
        "settings.workspace_name": "Navn pa arbeidsomrade",
        "settings.workspace_help": "Vises i board-overskrifter og invitasjoner.",
        "settings.default_visibility": "Standard synlighet",
        "settings.visibility_help": "Styrer hvordan nye boards deles.",
        "settings.visibility.private": "Privat",
        "settings.visibility.workspace": "Arbeidsomrade",
        "settings.visibility.public": "Offentlig",
        "settings.notifications": "Varsler",
        "settings.digest": "Frekvens for e-postoppsummering",
        "settings.digest_help": "Velg hvor ofte sammendrag sendes.",
        "settings.digest.daily": "Daglig",
        "settings.digest.weekly": "Ukentlig",
        "settings.digest.off": "Av",
        "settings.channel": "Kanal",
        "settings.channel_help": "Standardmal for automatiske oppdateringer.",
        "settings.automation": "Automatisering",
        "settings.card_template": "Kortmal",
        "settings.card_template_help": "Brukes nar nye kort opprettes fra mal.",
        "settings.template_default": "Eier - Frist - Godkjenningskriterier",
        "activity.eyebrow": "Arbeidsomrade",
        "activity.title": "Aktivitet",
        "activity.lead": "Siste board- og kortaktivitet fra teamet.",
        "activity.export": "Eksporter logg",
        "activity.feed_title": "Aktivitetsfeed",
        "activity.privacy_title": "Personvern for aktivitet",
        "activity.privacy_text": "Kun medlemmer i arbeidsomradet kan se aktivitetsloggen. Eksporter lagres etter teamets personvernregler.",
        "activity.loaded": "Lastet {count} aktiviteter.",
        "activity.empty_title": "Ingen aktivitet enna",
        "activity.empty_text": "Handlinger pa boards og kort vises her.",
        "help.title": "Tastaturhjelp",
        "help.lead": "Bruk disse snarveiene for raskere navigasjon og tilgjengelig board-arbeid.",
        "help.section_nav": "Navigasjon",
        "help.section_board": "Board-handlinger",
        "help.section_forms": "Skjema",
        "help.key": "Snarvei",
        "help.action": "Handling",
        "help.nav_tab": "Tab / Shift+Tab",
        "help.nav_tab_action": "Flytt fokus frem/tilbake",
        "help.nav_skip": "Hopp-lenker",
        "help.nav_skip_action": "Hopp til hovedinnhold eller navigasjon",
        "help.board_move": "Alt + Venstre/Hoyre",
        "help.board_move_action": "Flytt fokusert kort til forrige/neste kolonne",
        "help.board_menu": "Enter pa kortmeny",
        "help.board_menu_action": "Apne kontekstmeny for kort",
        "help.forms_submit": "Enter",
        "help.forms_submit_action": "Send skjema",
        "help.forms_reset": "Nullstill-knapp",
        "help.forms_reset_action": "Viser bekreftelsesdialog",
        "login.title": "Logg inn",
        "login.subtitle": "Bruk workspace-kontoen din for a fortsette.",
        "login.email": "E-post",
        "login.email_help": "Bruk e-postadressen for Trellar-kontoen din.",
        "login.password": "Passord",
        "login.password_help": "Skriv inn passordet for kontoen din.",
        "login.submit": "Logg inn",
        "login.create_account": "Opprett konto",
        "login.demo_hint": "Demo-login: {email} / {password}",
        "signup.title": "Opprett konto",
        "signup.subtitle": "Registrer deg med e-post og passord for a bruke Trellar.",
        "signup.email": "E-post",
        "signup.password": "Passord",
        "signup.password_help": "Bruk minst 8 tegn.",
        "signup.password_confirm": "Bekreft passord",
        "signup.submit": "Opprett konto",
        "signup.already_have": "Har du allerede en konto?",
        "error.required": "Dette feltet er pamkrevd.",
        "error.max_length": "Bruk maksimalt {max} tegn.",
        "error.invalid_email": "Skriv inn en gyldig e-postadresse.",
        "error.invalid_option": "Velg et gyldig alternativ.",
        "error.password_mismatch": "Passordene matcher ikke.",
        "error.password_length": "Passordet ma vare minst {min} tegn.",
        "error.summary_title": "Rett opp folgende",
        "error.not_found_title": "Fant ikke siden",
        "error.not_found_text": "Siden kan ha flyttet, eller adressen er feil.",
        "error.server_title": "Noe gikk galt",
        "error.server_text": "Prov igjen om litt. Kontakt support hvis feilen fortsetter.",
        "error.go_home": "Ga til hjem",
        "error.go_boards": "Ga til boards",
        "confirm.title": "Bekreft handling",
        "confirm.accept": "Bekreft",
        "confirm.cancel": "Avbryt",
        "status.saving": "Lagrer...",
    },
    "ar": {
        "brand.name": "Trellar",
        "nav.home": "Home",
        "nav.boards": "Boards",
        "nav.activity": "Activity",
        "nav.user": "User",
        "nav.settings": "Settings",
        "nav.help": "Help",
        "lang.name.ar": "Arabic",
        "skip.main": "Skip to main content",
    },
}


BOARDS = [
    {
        "slug": "product-roadmap",
        "name": "Product Roadmap",
        "description": "Plan features, milestones, and releases for the next quarter.",
        "members": 6,
        "created_order": 3,
    },
    {
        "slug": "marketing-sprint",
        "name": "Marketing Sprint",
        "description": "Coordinate campaign tasks, creative reviews, and launch timelines.",
        "members": 4,
        "created_order": 2,
    },
    {
        "slug": "engineering-backlog",
        "name": "Engineering Backlog",
        "description": "Track improvements, bug fixes, and technical debt in one place.",
        "members": 8,
        "created_order": 1,
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
                    {
                        "title": "Audit onboarding drop-off points",
                        "meta": "Research - 2d",
                        "status": "High priority",
                    },
                    {
                        "title": "Draft release notes template",
                        "meta": "Docs - 1d",
                        "status": "Ready",
                    },
                    {
                        "title": "Collect feedback from design review",
                        "meta": "Design - 3h",
                        "status": "Needs input",
                    },
                ],
            },
            {
                "name": "In Progress",
                "cards": [
                    {
                        "title": "Build dashboard usage report",
                        "meta": "Analytics - 1d",
                        "status": "In progress",
                    },
                    {
                        "title": "Refine billing settings flow",
                        "meta": "Frontend - 2d",
                        "status": "In review prep",
                    },
                ],
            },
            {
                "name": "Review",
                "cards": [
                    {
                        "title": "QA test automation alerts",
                        "meta": "QA - Today",
                        "status": "Awaiting QA",
                    },
                    {
                        "title": "Security checklist update",
                        "meta": "Platform - 5h",
                        "status": "Awaiting sign-off",
                    },
                ],
            },
            {
                "name": "Done",
                "cards": [
                    {
                        "title": "Migrate legacy team permissions",
                        "meta": "Backend - Complete",
                        "status": "Completed",
                    },
                    {
                        "title": "Refresh board performance budget",
                        "meta": "Ops - Complete",
                        "status": "Completed",
                    },
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
                    {
                        "title": "Landing page variant test",
                        "meta": "Growth - 1w",
                        "status": "Candidate",
                    },
                    {
                        "title": "Partner webinar concept",
                        "meta": "Brand - 4d",
                        "status": "Candidate",
                    },
                ],
            },
            {
                "name": "Doing",
                "cards": [
                    {
                        "title": "Write social teaser copy",
                        "meta": "Content - 1d",
                        "status": "In progress",
                    }
                ],
            },
            {
                "name": "Done",
                "cards": [
                    {
                        "title": "Publish April campaign brief",
                        "meta": "PMM - Complete",
                        "status": "Completed",
                    }
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
                    {
                        "title": "Rate-limit login endpoint",
                        "meta": "Security - 3h",
                        "status": "Urgent",
                    },
                    {
                        "title": "Investigate flaky CI suite",
                        "meta": "Infra - 5h",
                        "status": "Needs triage",
                    },
                ],
            },
            {
                "name": "Planned",
                "cards": [
                    {
                        "title": "Add board activity filters",
                        "meta": "API - 2d",
                        "status": "Scheduled",
                    },
                    {
                        "title": "Optimize lane query payload",
                        "meta": "Backend - 1d",
                        "status": "Scheduled",
                    },
                ],
            },
            {
                "name": "Shipped",
                "cards": [
                    {
                        "title": "Cache avatar lookups",
                        "meta": "Perf - Complete",
                        "status": "Completed",
                    }
                ],
            },
        ],
    },
}

ACTIVITY_ITEMS = [
    {
        "title": 'Moved "Refine billing settings flow" to Review',
        "board": "Product Roadmap",
        "time_iso": "2026-03-10T09:48:00+00:00",
    },
    {
        "title": 'Added card "Rate-limit login endpoint"',
        "board": "Engineering Backlog",
        "time_iso": "2026-03-10T09:00:00+00:00",
    },
    {
        "title": 'Completed "Publish April campaign brief"',
        "board": "Marketing Sprint",
        "time_iso": "2026-03-10T08:00:00+00:00",
    },
    {
        "title": "Updated board permissions",
        "board": "Workspace Admin",
        "time_iso": "2026-03-09T16:20:00+00:00",
    },
    {
        "title": "Reordered backlog cards",
        "board": "Product Roadmap",
        "time_iso": "2026-03-09T12:05:00+00:00",
    },
    {
        "title": "Changed workspace digest to daily",
        "board": "Workspace Admin",
        "time_iso": "2026-03-09T10:35:00+00:00",
    },
    {
        "title": 'Moved "Investigate flaky CI suite" to Planned',
        "board": "Engineering Backlog",
        "time_iso": "2026-03-08T14:42:00+00:00",
    },
]

USER_DEFAULTS = {
    "display_name": "Gard H.",
    "email": "gard@example.com",
    "about": "Building Trellar one release at a time.",
}

SETTINGS_DEFAULTS = {
    "workspace_name": "Trellar Team",
    "default_visibility": "private",
    "digest_frequency": "daily",
    "channel": "#trellar-updates",
    "card_template": "Owner - Due date - Acceptance criteria",
}

DEFAULT_DEMO_LOGIN_EMAIL = "demo@trellar.local"
DEFAULT_DEMO_LOGIN_PASSWORD = "trellar-demo"
DEMO_LOGIN_EMAIL = (os.environ.get("TRELLAR_DEMO_EMAIL", DEFAULT_DEMO_LOGIN_EMAIL).strip() or DEFAULT_DEMO_LOGIN_EMAIL).lower()
DEMO_LOGIN_PASSWORD = os.environ.get("TRELLAR_DEMO_PASSWORD", DEFAULT_DEMO_LOGIN_PASSWORD) or DEFAULT_DEMO_LOGIN_PASSWORD
SHOW_DEMO_CREDENTIALS_HINT = (
    DEMO_LOGIN_EMAIL == DEFAULT_DEMO_LOGIN_EMAIL and DEMO_LOGIN_PASSWORD == DEFAULT_DEMO_LOGIN_PASSWORD
)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "").strip()
SUPABASE_ANON_KEY = os.environ.get("SUPABASE_ANON_KEY", "").strip()
SUPABASE_SERVICE_ROLE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
TRELLAR_USE_SUPABASE = os.environ.get("TRELLAR_USE_SUPABASE", "1").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}
SUPABASE_ENABLED = bool(TRELLAR_USE_SUPABASE and SUPABASE_URL and SUPABASE_ANON_KEY and create_client is not None)

SESSION_AUTH_USER_EMAIL = "_auth_user_email"
SESSION_SB_ACCESS_TOKEN = "_sb_access_token"
SESSION_SB_REFRESH_TOKEN = "_sb_refresh_token"
SESSION_SB_USER_ID = "_sb_user_id"
SESSION_SB_USER_EMAIL = "_sb_user_email"
SESSION_SB_DISPLAY_NAME = "_sb_display_name"
MIN_PASSWORD_LENGTH = 8

AUTH_USERS: dict[str, dict[str, str]] = {
    DEMO_LOGIN_EMAIL: {
        "email": DEMO_LOGIN_EMAIL,
        "display_name": "Demo User",
        "password_hash": generate_password_hash(DEMO_LOGIN_PASSWORD),
    }
}

RUNTIME_USER_PROFILES: dict[str, dict[str, str]] = {}
RUNTIME_SETTINGS: dict[str, dict[str, str]] = {}
RUNTIME_BOARDS: dict[str, dict[str, dict[str, object]]] = {}
RUNTIME_BOARD_CATALOG: dict[str, list[dict[str, object]]] = {}
RUNTIME_ACTIVITY: dict[str, list[dict[str, str]]] = {}
RUNTIME_ARCHIVE_BUFFER: dict[str, dict[str, dict[str, object]]] = {}


EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

PUBLIC_ENDPOINTS = {
    "login",
    "signup",
    "set_language",
    "docs_file",
    "static",
}


def get_locale() -> str:
    session_lang = session.get("lang")
    if session_lang in AVAILABLE_LANGUAGES:
        return session_lang

    best = request.accept_languages.best_match(AVAILABLE_LANGUAGES)
    return best if best in AVAILABLE_LANGUAGES else "en"


def _value(source: object, key: str) -> object | None:
    if isinstance(source, dict):
        return source.get(key)
    return getattr(source, key, None)


def _to_dict(value: object) -> dict[str, object]:
    if isinstance(value, dict):
        return dict(value)
    if value is None:
        return {}
    if hasattr(value, "model_dump"):
        dumped = value.model_dump()
        return dict(dumped) if isinstance(dumped, dict) else {}
    if hasattr(value, "dict"):
        dumped = value.dict()
        return dict(dumped) if isinstance(dumped, dict) else {}
    return {}


def _extract_auth_session(auth_response: object) -> dict[str, object]:
    session_payload = _value(auth_response, "session")
    if session_payload is None:
        data_payload = _value(auth_response, "data")
        session_payload = _value(data_payload, "session")

    candidate = _to_dict(session_payload)
    if candidate:
        return candidate

    fallback = _to_dict(auth_response)
    if "access_token" in fallback and "refresh_token" in fallback:
        return fallback

    return {}


def _extract_auth_user(auth_response: object) -> dict[str, object]:
    user_payload = _value(auth_response, "user")
    if user_payload is None:
        data_payload = _value(auth_response, "data")
        user_payload = _value(data_payload, "user")
    return _to_dict(user_payload)


def _normalize_auth_user(user_payload: object) -> dict[str, str] | None:
    raw = _to_dict(user_payload)
    user_id = str(raw.get("id", "")).strip()
    email = str(raw.get("email", "")).strip().lower()
    metadata = _to_dict(raw.get("user_metadata"))
    display_name = str(
        metadata.get("display_name")
        or metadata.get("full_name")
        or raw.get("display_name")
        or email.split("@")[0]
        or "User"
    ).strip()

    if not user_id or not email:
        return None

    return {
        "id": user_id,
        "email": email,
        "display_name": display_name,
    }


def _cache_supabase_tokens(session_payload: object) -> None:
    raw = _to_dict(session_payload)
    access_token = str(raw.get("access_token", "")).strip()
    refresh_token = str(raw.get("refresh_token", "")).strip()
    if access_token and refresh_token:
        session[SESSION_SB_ACCESS_TOKEN] = access_token
        session[SESSION_SB_REFRESH_TOKEN] = refresh_token


def _cache_supabase_user(user_payload: object) -> bool:
    normalized = _normalize_auth_user(user_payload)
    if not normalized:
        return False

    session[SESSION_SB_USER_ID] = normalized["id"]
    session[SESSION_SB_USER_EMAIL] = normalized["email"]
    session[SESSION_SB_DISPLAY_NAME] = normalized["display_name"]
    return True


def _cache_supabase_auth_response(auth_response: object) -> bool:
    _cache_supabase_tokens(_extract_auth_session(auth_response))
    user_payload = _extract_auth_user(auth_response)
    if user_payload:
        return _cache_supabase_user(user_payload)
    return False


def _clear_supabase_session() -> None:
    session.pop(SESSION_SB_ACCESS_TOKEN, None)
    session.pop(SESSION_SB_REFRESH_TOKEN, None)
    session.pop(SESSION_SB_USER_ID, None)
    session.pop(SESSION_SB_USER_EMAIL, None)
    session.pop(SESSION_SB_DISPLAY_NAME, None)


def create_supabase_runtime_client(api_key: str | None = None) -> Client | None:
    if not SUPABASE_ENABLED or create_client is None:
        return None

    selected_key = (api_key or SUPABASE_ANON_KEY).strip()
    if not selected_key:
        return None

    try:
        return create_client(SUPABASE_URL, selected_key)
    except Exception:
        return None


def get_authenticated_supabase_client() -> tuple[Client | None, str | None]:
    if not SUPABASE_ENABLED:
        return None, None

    access_token = str(session.get(SESSION_SB_ACCESS_TOKEN, "")).strip()
    refresh_token = str(session.get(SESSION_SB_REFRESH_TOKEN, "")).strip()
    user_id = str(session.get(SESSION_SB_USER_ID, "")).strip()
    if not access_token or not refresh_token or not user_id:
        return None, None

    client = create_supabase_runtime_client(SUPABASE_ANON_KEY)
    if client is None:
        return None, None

    try:
        auth_response = client.auth.set_session(access_token, refresh_token)
        _cache_supabase_tokens(_extract_auth_session(auth_response))
    except Exception:
        _clear_supabase_session()
        return None, None

    return client, user_id


def get_current_user() -> dict[str, str] | None:
    if SUPABASE_ENABLED:
        access_token = str(session.get(SESSION_SB_ACCESS_TOKEN, "")).strip()
        refresh_token = str(session.get(SESSION_SB_REFRESH_TOKEN, "")).strip()
        user_id = str(session.get(SESSION_SB_USER_ID, "")).strip()
        email = str(session.get(SESSION_SB_USER_EMAIL, "")).strip().lower()
        display_name = str(session.get(SESSION_SB_DISPLAY_NAME, "")).strip()
        if access_token and refresh_token and user_id and email:
            return {
                "id": user_id,
                "email": email,
                "display_name": display_name or email.split("@")[0],
            }
        return None

    email = session.get(SESSION_AUTH_USER_EMAIL)
    if not isinstance(email, str) or not email:
        return None
    return AUTH_USERS.get(email.lower())


def is_authenticated() -> bool:
    return get_current_user() is not None


def login_user(email: str) -> None:
    session[SESSION_AUTH_USER_EMAIL] = email.lower()


def logout_user() -> None:
    session.pop(SESSION_AUTH_USER_EMAIL, None)
    _clear_supabase_session()


def get_document_dir(locale: str) -> str:
    return "rtl" if locale in RTL_LANGUAGES else "ltr"


def translate_text(key: str, locale: str | None = None, **kwargs: object) -> str:
    selected_locale = locale or get_locale()
    catalog = TRANSLATIONS.get(selected_locale, TRANSLATIONS["en"])
    fallback = TRANSLATIONS["en"].get(key, key)
    text = catalog.get(key, fallback)

    try:
        return text.format(**kwargs)
    except (KeyError, ValueError):
        return text


def build_trellar_messages(locale: str, csrf_token: str) -> dict[str, str]:
    return {
        "undo": translate_text("common.undo", locale=locale),
        "statusSaving": translate_text("status.saving", locale=locale),
        "boardMoved": translate_text("board.moved", locale=locale, title="__TITLE__", lane="__LANE__"),
        "boardArchived": translate_text("board.archived", locale=locale, title="__TITLE__"),
        "boardUndoDone": translate_text("board.undo_done", locale=locale),
        "boardAdded": translate_text("board.added", locale=locale, title="__TITLE__", lane="__LANE__"),
        "boardAddPromptTitle": translate_text("board.add_prompt_title", locale=locale),
        "boardAddPromptMeta": translate_text("board.add_prompt_meta", locale=locale),
        "boardAddError": translate_text("board.add_error", locale=locale),
        "boardCreatePromptName": translate_text("boards.create_prompt_name", locale=locale),
        "boardCreatePromptDescription": translate_text("boards.create_prompt_description", locale=locale),
        "boardCreateError": translate_text("boards.create_error", locale=locale),
        "boardCreateTitle": translate_text("boards.create", locale=locale),
        "boardCreateDescription": translate_text("boards.lead", locale=locale),
        "boardCardActions": translate_text("board.card_actions", locale=locale),
        "boardMoveLeft": translate_text("board.move_left", locale=locale),
        "boardMoveRight": translate_text("board.move_right", locale=locale),
        "boardArchive": translate_text("board.archive", locale=locale),
        "boardStatusPrefix": translate_text("board.status_prefix", locale=locale),
        "boardConfirmArchive": translate_text("board.confirm_archive", locale=locale),
        "boardAddTitle": translate_text("board.add_card", locale=locale),
        "boardAddToLane": translate_text("board.add_to_lane", locale=locale, lane="__LANE__"),
        "errorRequired": translate_text("error.required", locale=locale),
        "commonCreate": translate_text("common.create", locale=locale),
        "csrfToken": csrf_token,
    }


def get_csrf_token() -> str:
    token = session.get("_csrf_token")
    if token:
        return token

    token = secrets.token_urlsafe(32)
    session["_csrf_token"] = token
    return token


def safe_redirect_path(target: str | None) -> str:
    if not target:
        return url_for("home")

    parsed = urlparse(target)
    if parsed.scheme or parsed.netloc:
        return url_for("home")

    if not parsed.path.startswith("/"):
        return url_for("home")

    return parsed.path + (("?" + parsed.query) if parsed.query else "")


def is_api_request() -> bool:
    return request.path.startswith("/api/")


def get_client_id() -> str:
    client_id = session.get("_client_id")
    if isinstance(client_id, str) and client_id:
        return client_id

    client_id = secrets.token_hex(16)
    session["_client_id"] = client_id
    return client_id


def base_board_state() -> dict[str, dict[str, object]]:
    store = deepcopy(BOARD_DETAILS)

    for slug, board in store.items():
        lanes = board.get("lanes", [])
        for lane_index, lane in enumerate(lanes):
            lane["id"] = f"lane-{lane_index + 1}"
            cards = lane.get("cards", [])
            for card_index, card in enumerate(cards):
                card["id"] = f"{slug}-l{lane_index + 1}-c{card_index + 1}"

    return store


def base_board_catalog() -> list[dict[str, object]]:
    return [dict(item) for item in BOARDS]


def _runtime_store_key() -> str:
    if SUPABASE_ENABLED:
        user_id = str(session.get(SESSION_SB_USER_ID, "")).strip()
        if user_id:
            return f"user:{user_id}"
    return f"client:{get_client_id()}"


def _response_rows(response: object) -> list[dict[str, object]]:
    data = _value(response, "data")
    if isinstance(data, list):
        return [_to_dict(item) for item in data if _to_dict(item)]
    if data is None:
        return []
    row = _to_dict(data)
    return [row] if row else []


def _first_response_row(response: object) -> dict[str, object] | None:
    rows = _response_rows(response)
    return rows[0] if rows else None


def _safe_int(value: object, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _seed_supabase_default_workspace(client: Client, user_id: str) -> None:
    existing = _response_rows(client.table("boards").select("id").eq("owner_id", user_id).limit(1).execute())
    if existing:
        return

    for board_item in BOARDS:
        slug = str(board_item.get("slug", "board"))
        name = str(board_item.get("name", "Board"))
        description = str(board_item.get("description", ""))
        members = _safe_int(board_item.get("members"), default=1)

        board_response = client.table("boards").insert(
            {
                "owner_id": user_id,
                "slug": slug,
                "name": name,
                "description": description,
                "members": members,
            }
        ).execute()
        board_row = _first_response_row(board_response)
        board_id = str((board_row or {}).get("id", "")).strip()
        if not board_id:
            continue

        board_detail = BOARD_DETAILS.get(slug, {"lanes": default_new_board_lanes()})
        lanes = board_detail.get("lanes", [])
        for lane_index, lane in enumerate(lanes):
            lane_name = str(lane.get("name", f"Lane {lane_index + 1}"))
            lane_response = client.table("lanes").insert(
                {
                    "board_id": board_id,
                    "name": lane_name,
                    "position": lane_index,
                }
            ).execute()
            lane_row = _first_response_row(lane_response)
            lane_id = str((lane_row or {}).get("id", "")).strip()
            if not lane_id:
                continue

            cards = lane.get("cards", [])
            card_payload: list[dict[str, object]] = []
            for card_index, card in enumerate(cards):
                card_payload.append(
                    {
                        "board_id": board_id,
                        "lane_id": lane_id,
                        "title": str(card.get("title", "Card")),
                        "meta": str(card.get("meta", "")),
                        "status": str(card.get("status", "New")),
                        "position": card_index,
                        "archived": False,
                    }
                )
            if card_payload:
                client.table("cards").insert(card_payload).execute()

    seed_activity_payload: list[dict[str, object]] = []
    for item in ACTIVITY_ITEMS:
        seed_activity_payload.append(
            {
                "owner_id": user_id,
                "board_name": str(item.get("board", "")),
                "title": str(item.get("title", "")),
                "created_at": str(item.get("time_iso", datetime.now(timezone.utc).isoformat())),
            }
        )
    if seed_activity_payload:
        client.table("activity").insert(seed_activity_payload).execute()


def _load_supabase_boards_state() -> dict[str, dict[str, object]]:
    client, user_id = get_authenticated_supabase_client()
    if client is None or not user_id:
        return {}

    try:
        board_rows = _response_rows(
            client.table("boards")
            .select("id,slug,name,description,members,created_at")
            .eq("owner_id", user_id)
            .order("created_at")
            .execute()
        )
        if not board_rows:
            _seed_supabase_default_workspace(client, user_id)
            board_rows = _response_rows(
                client.table("boards")
                .select("id,slug,name,description,members,created_at")
                .eq("owner_id", user_id)
                .order("created_at")
                .execute()
            )
    except Exception:
        return {}

    state: dict[str, dict[str, object]] = {}
    for board_row in board_rows:
        board_id = str(board_row.get("id", "")).strip()
        slug = str(board_row.get("slug", "")).strip()
        if not board_id or not slug:
            continue

        lane_rows = _response_rows(
            client.table("lanes")
            .select("id,name,position")
            .eq("board_id", board_id)
            .order("position")
            .execute()
        )
        lanes_payload: list[dict[str, object]] = []
        for lane_row in lane_rows:
            lane_id = str(lane_row.get("id", "")).strip()
            if not lane_id:
                continue

            card_rows = _response_rows(
                client.table("cards")
                .select("id,title,meta,status,position")
                .eq("lane_id", lane_id)
                .eq("archived", False)
                .order("position")
                .execute()
            )
            cards_payload = [
                {
                    "id": str(card.get("id", "")),
                    "title": str(card.get("title", "Card")),
                    "meta": str(card.get("meta", "")),
                    "status": str(card.get("status", "New")),
                }
                for card in card_rows
            ]

            lanes_payload.append(
                {
                    "id": lane_id,
                    "name": str(lane_row.get("name", "Lane")),
                    "cards": cards_payload,
                }
            )

        state[slug] = {
            "id": board_id,
            "name": str(board_row.get("name", "Board")),
            "description": str(board_row.get("description", "")),
            "members": _safe_int(board_row.get("members"), default=1),
            "created_at": str(board_row.get("created_at", "")),
            "lanes": lanes_payload,
        }

    return state


def _load_supabase_activity() -> list[dict[str, str]]:
    client, user_id = get_authenticated_supabase_client()
    if client is None or not user_id:
        return []

    rows = _response_rows(
        client.table("activity")
        .select("title,board_name,created_at")
        .eq("owner_id", user_id)
        .order("created_at", desc=True)
        .execute()
    )
    return [
        {
            "title": str(row.get("title", "")),
            "board": str(row.get("board_name", "")),
            "time_iso": str(row.get("created_at", "")),
        }
        for row in rows
    ]


def get_runtime_board_catalog() -> list[dict[str, object]]:
    if SUPABASE_ENABLED:
        board_state = _load_supabase_boards_state()
        board_items = list(board_state.items())
        board_items.sort(key=lambda item: str(item[1].get("created_at", "")))
        catalog: list[dict[str, object]] = []
        for created_order, (slug, board) in enumerate(board_items, start=1):
            catalog.append(
                {
                    "slug": slug,
                    "name": str(board.get("name", "Board")),
                    "description": str(board.get("description", "")),
                    "members": _safe_int(board.get("members"), default=1),
                    "created_order": created_order,
                }
            )
        return catalog

    runtime_key = _runtime_store_key()
    if runtime_key not in RUNTIME_BOARD_CATALOG:
        RUNTIME_BOARD_CATALOG[runtime_key] = base_board_catalog()
    return RUNTIME_BOARD_CATALOG[runtime_key]


def get_runtime_boards() -> dict[str, dict[str, object]]:
    if SUPABASE_ENABLED:
        return _load_supabase_boards_state()

    runtime_key = _runtime_store_key()
    if runtime_key not in RUNTIME_BOARDS:
        RUNTIME_BOARDS[runtime_key] = base_board_state()
    return RUNTIME_BOARDS[runtime_key]


def get_runtime_activity() -> list[dict[str, str]]:
    if SUPABASE_ENABLED:
        return _load_supabase_activity()

    runtime_key = _runtime_store_key()
    if runtime_key not in RUNTIME_ACTIVITY:
        RUNTIME_ACTIVITY[runtime_key] = deepcopy(ACTIVITY_ITEMS)
    return RUNTIME_ACTIVITY[runtime_key]


def add_activity_entry(title: str, board_name: str) -> None:
    if SUPABASE_ENABLED:
        client, user_id = get_authenticated_supabase_client()
        if client is not None and user_id:
            try:
                client.table("activity").insert(
                    {
                        "owner_id": user_id,
                        "board_name": board_name,
                        "title": title,
                    }
                ).execute()
            except Exception:
                pass
        return

    activity_store = get_runtime_activity()
    activity_store.insert(
        0,
        {
            "title": title,
            "board": board_name,
            "time_iso": datetime.now(timezone.utc).isoformat(),
        },
    )


def get_runtime_archive_buffer() -> dict[str, dict[str, object]]:
    runtime_key = _runtime_store_key()
    if runtime_key not in RUNTIME_ARCHIVE_BUFFER:
        RUNTIME_ARCHIVE_BUFFER[runtime_key] = {}
    return RUNTIME_ARCHIVE_BUFFER[runtime_key]


def create_board_slug(name: str, existing_slugs: set[str]) -> str:
    base_slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "board"
    if base_slug not in existing_slugs:
        return base_slug

    suffix = 2
    while True:
        candidate = f"{base_slug}-{suffix}"
        if candidate not in existing_slugs:
            return candidate
        suffix += 1


def next_created_order(board_catalog: list[dict[str, object]]) -> int:
    return max((int(item.get("created_order", 0)) for item in board_catalog), default=0) + 1


def default_new_board_lanes() -> list[dict[str, object]]:
    lane_names = ["Backlog", "In Progress", "Done"]
    lanes: list[dict[str, object]] = []
    for index, lane_name in enumerate(lane_names, start=1):
        lanes.append(
            {
                "id": f"lane-{index}",
                "name": lane_name,
                "cards": [],
            }
        )
    return lanes


def create_card_id(board_slug: str) -> str:
    return f"{board_slug}-c{secrets.token_hex(4)}"


def find_card_location(board_data: dict[str, object], card_id: str) -> tuple[int, int] | None:
    lanes = board_data.get("lanes", [])
    for lane_index, lane in enumerate(lanes):
        cards = lane.get("cards", [])
        for card_index, card in enumerate(cards):
            if card.get("id") == card_id:
                return lane_index, card_index
    return None


def default_user_values() -> dict[str, str]:
    current_user = get_current_user()
    if SUPABASE_ENABLED and current_user:
        client, user_id = get_authenticated_supabase_client()
        if client is not None and user_id:
            profile_row = _first_response_row(
                client.table("profiles")
                .select("display_name,email,about")
                .eq("id", user_id)
                .limit(1)
                .execute()
            )
            if profile_row:
                return {
                    "display_name": str(profile_row.get("display_name", "")),
                    "email": str(profile_row.get("email", "")),
                    "about": str(profile_row.get("about", "")),
                }

            user_defaults = dict(USER_DEFAULTS)
            user_defaults["email"] = current_user.get("email", user_defaults["email"])
            user_defaults["display_name"] = current_user.get("display_name", user_defaults["display_name"])
            client.table("profiles").insert(
                {
                    "id": user_id,
                    "display_name": user_defaults["display_name"],
                    "email": user_defaults["email"],
                    "about": user_defaults["about"],
                }
            ).execute()
            return user_defaults

    runtime_key = _runtime_store_key()
    if runtime_key not in RUNTIME_USER_PROFILES:
        user_defaults = dict(USER_DEFAULTS)
        if current_user:
            user_defaults["email"] = current_user.get("email", user_defaults["email"])
            user_defaults["display_name"] = current_user.get("display_name", user_defaults["display_name"])
        RUNTIME_USER_PROFILES[runtime_key] = user_defaults
    return dict(RUNTIME_USER_PROFILES[runtime_key])


def default_settings_values() -> dict[str, str]:
    if SUPABASE_ENABLED:
        client, user_id = get_authenticated_supabase_client()
        if client is not None and user_id:
            settings_row = _first_response_row(
                client.table("user_settings")
                .select("workspace_name,default_visibility,digest_frequency,channel,card_template")
                .eq("user_id", user_id)
                .limit(1)
                .execute()
            )
            if settings_row:
                return {
                    "workspace_name": str(settings_row.get("workspace_name", "")),
                    "default_visibility": str(settings_row.get("default_visibility", "")),
                    "digest_frequency": str(settings_row.get("digest_frequency", "")),
                    "channel": str(settings_row.get("channel", "")),
                    "card_template": str(settings_row.get("card_template", "")),
                }

            defaults = dict(SETTINGS_DEFAULTS)
            client.table("user_settings").insert(
                {
                    "user_id": user_id,
                    **defaults,
                }
            ).execute()
            return defaults

    runtime_key = _runtime_store_key()
    if runtime_key not in RUNTIME_SETTINGS:
        RUNTIME_SETTINGS[runtime_key] = dict(SETTINGS_DEFAULTS)
    return dict(RUNTIME_SETTINGS[runtime_key])


def validate_user_form(data: dict[str, str], locale: str) -> dict[str, str]:
    errors: dict[str, str] = {}

    display_name = data.get("display_name", "").strip()
    email = data.get("email", "").strip()
    about = data.get("about", "").strip()

    data["display_name"] = display_name
    data["email"] = email
    data["about"] = about

    if not display_name:
        errors["display_name"] = translate_text("error.required", locale=locale)
    elif len(display_name) > 80:
        errors["display_name"] = translate_text("error.max_length", locale=locale, max=80)

    if not email:
        errors["email"] = translate_text("error.required", locale=locale)
    elif not EMAIL_RE.match(email):
        errors["email"] = translate_text("error.invalid_email", locale=locale)

    if len(about) > 280:
        errors["about"] = translate_text("error.max_length", locale=locale, max=280)

    return errors


def validate_settings_form(data: dict[str, str], locale: str) -> dict[str, str]:
    errors: dict[str, str] = {}

    workspace_name = data.get("workspace_name", "").strip()
    default_visibility = data.get("default_visibility", "")
    digest_frequency = data.get("digest_frequency", "")
    channel = data.get("channel", "").strip()
    card_template = data.get("card_template", "").strip()

    data["workspace_name"] = workspace_name
    data["default_visibility"] = default_visibility
    data["digest_frequency"] = digest_frequency
    data["channel"] = channel
    data["card_template"] = card_template

    if not workspace_name:
        errors["workspace_name"] = translate_text("error.required", locale=locale)
    elif len(workspace_name) > 100:
        errors["workspace_name"] = translate_text("error.max_length", locale=locale, max=100)

    if default_visibility not in {"private", "workspace", "public"}:
        errors["default_visibility"] = translate_text("error.invalid_option", locale=locale)

    if digest_frequency not in {"daily", "weekly", "off"}:
        errors["digest_frequency"] = translate_text("error.invalid_option", locale=locale)

    if len(channel) > 80:
        errors["channel"] = translate_text("error.max_length", locale=locale, max=80)

    if len(card_template) > 320:
        errors["card_template"] = translate_text("error.max_length", locale=locale, max=320)

    return errors


def format_relative_time(iso_value: str, locale: str) -> str:
    try:
        timestamp = datetime.fromisoformat(iso_value)
    except ValueError:
        return ""

    now = datetime.now(timezone.utc)
    delta = now - timestamp
    seconds = max(int(delta.total_seconds()), 0)

    if seconds < 60:
        return "just now" if locale == "en" else "akkurat na"

    minutes = seconds // 60
    if minutes < 60:
        if locale == "en":
            return f"{minutes} minute{'s' if minutes != 1 else ''} ago"
        return f"{minutes} min siden"

    hours = minutes // 60
    if hours < 24:
        if locale == "en":
            return f"{hours} hour{'s' if hours != 1 else ''} ago"
        return f"{hours} t siden"

    days = hours // 24
    if locale == "en":
        return f"{days} day{'s' if days != 1 else ''} ago"
    return f"{days} d siden"


def enrich_board(slug: str) -> dict[str, object] | None:
    board_data = get_runtime_boards().get(slug)
    if board_data is None:
        return None

    return deepcopy(board_data)


def board_collection(search_query: str, member_filter: str, sort_option: str) -> list[dict[str, object]]:
    boards = [dict(item) for item in get_runtime_board_catalog()]

    if search_query:
        needle = search_query.lower()
        boards = [
            board
            for board in boards
            if needle in str(board["name"]).lower() or needle in str(board["description"]).lower()
        ]

    if member_filter == "small":
        boards = [board for board in boards if int(board["members"]) <= 4]
    elif member_filter == "medium":
        boards = [board for board in boards if 5 <= int(board["members"]) <= 6]
    elif member_filter == "large":
        boards = [board for board in boards if int(board["members"]) >= 7]

    if sort_option == "name_desc":
        boards.sort(key=lambda item: str(item["name"]).lower(), reverse=True)
    elif sort_option == "members_desc":
        boards.sort(key=lambda item: int(item["members"]), reverse=True)
    elif sort_option == "members_asc":
        boards.sort(key=lambda item: int(item["members"]))
    else:
        boards.sort(key=lambda item: str(item["name"]).lower())

    return boards


def _supabase_board_by_slug(client: Client, user_id: str, slug: str) -> dict[str, object] | None:
    row = _first_response_row(
        client.table("boards")
        .select("id,slug,name,description,members")
        .eq("owner_id", user_id)
        .eq("slug", slug)
        .limit(1)
        .execute()
    )
    return row if row else None


def _supabase_lanes_for_board(client: Client, board_id: str) -> list[dict[str, object]]:
    return _response_rows(
        client.table("lanes")
        .select("id,name,position")
        .eq("board_id", board_id)
        .order("position")
        .execute()
    )


def _supabase_next_card_position(client: Client, lane_id: str) -> int:
    row = _first_response_row(
        client.table("cards")
        .select("position")
        .eq("lane_id", lane_id)
        .order("position", desc=True)
        .limit(1)
        .execute()
    )
    if not row:
        return 0
    return _safe_int(row.get("position"), default=0) + 1


def _supabase_lane_index(lanes: list[dict[str, object]], lane_id: str) -> int:
    for index, lane in enumerate(lanes):
        if str(lane.get("id", "")) == lane_id:
            return index
    return -1


@app.before_request
def require_authenticated_user() -> object | None:
    if request.endpoint is None:
        return None

    if request.endpoint in PUBLIC_ENDPOINTS:
        return None

    if is_authenticated():
        return None

    if is_api_request():
        return jsonify({"ok": False, "error": "unauthorized"}), 401

    next_target = request.full_path if request.query_string else request.path
    return redirect(url_for("login", next=next_target))


@app.before_request
def protect_post_requests() -> object | None:
    if request.method != "POST":
        return None

    if request.endpoint == "static":
        return None

    submitted = request.form.get("csrf_token", "") or request.headers.get("X-CSRF-Token", "")
    expected = session.get("_csrf_token", "")

    if not expected or not submitted or not compare_digest(submitted, expected):
        if is_api_request():
            return jsonify({"ok": False, "error": "csrf"}), 403

        flash(translate_text("flash.csrf_error"), "error")
        return redirect(safe_redirect_path(request.referrer))

    return None


@app.context_processor
def inject_template_context() -> dict[str, object]:
    locale = get_locale()
    current_user = get_current_user()
    csrf_token = get_csrf_token()

    def t(key: str, **kwargs: object) -> str:
        return translate_text(key, locale=locale, **kwargs)

    languages = [
        {
            "code": code,
            "label": translate_text(f"lang.name.{code}", locale=locale),
        }
        for code in AVAILABLE_LANGUAGES
    ]

    return {
        "t": t,
        "current_lang": locale,
        "document_lang": locale,
        "document_dir": get_document_dir(locale),
        "available_languages": languages,
        "csrf_token": csrf_token,
        "trellar_messages": build_trellar_messages(locale, csrf_token),
        "supabase_enabled": SUPABASE_ENABLED,
        "is_authenticated": current_user is not None,
        "current_user": current_user,
    }


@app.route("/set-language", methods=["POST"])
def set_language():
    selected = request.form.get("lang", "en")
    if selected in AVAILABLE_LANGUAGES:
        session["lang"] = selected
        flash(translate_text("flash.language_updated", locale=selected), "success")

    return redirect(safe_redirect_path(request.form.get("next")))


@app.route("/login", methods=["GET", "POST"])
def login():
    locale = get_locale()
    next_raw = request.form.get("next") if request.method == "POST" else request.args.get("next")
    next_target = safe_redirect_path(next_raw)

    if is_authenticated():
        return redirect(next_target)

    form_values = {
        "email": "",
    }
    errors: dict[str, str] = {}

    if request.method == "POST":
        form_values["email"] = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not form_values["email"]:
            errors["email"] = translate_text("error.required", locale=locale)
        elif not EMAIL_RE.match(form_values["email"]):
            errors["email"] = translate_text("error.invalid_email", locale=locale)

        if not password:
            errors["password"] = translate_text("error.required", locale=locale)

        if errors:
            flash(translate_text("flash.validation_error", locale=locale), "error")
        else:
            if SUPABASE_ENABLED:
                supabase = create_supabase_runtime_client(SUPABASE_ANON_KEY)
                if supabase is None:
                    errors["email"] = translate_text("flash.supabase_not_configured", locale=locale)
                    flash(translate_text("flash.supabase_not_configured", locale=locale), "error")
                else:
                    try:
                        auth_response = supabase.auth.sign_in_with_password(
                            {
                                "email": form_values["email"],
                                "password": password,
                            }
                        )
                    except Exception:
                        auth_response = None

                    auth_session = _extract_auth_session(auth_response)
                    auth_user = _extract_auth_user(auth_response)
                    if auth_session and auth_user and _cache_supabase_user(auth_user):
                        _cache_supabase_tokens(auth_session)
                        flash(translate_text("flash.login_success", locale=locale), "success")
                        return redirect(next_target)

                    errors["email"] = translate_text("flash.login_failed", locale=locale)
                    errors["password"] = translate_text("flash.login_failed", locale=locale)
                    flash(translate_text("flash.login_failed", locale=locale), "error")
            else:
                account = AUTH_USERS.get(form_values["email"])
                password_hash = str(account.get("password_hash", "")) if account else ""

                if account and check_password_hash(password_hash, password):
                    login_user(form_values["email"])
                    flash(translate_text("flash.login_success", locale=locale), "success")
                    return redirect(next_target)

                errors["email"] = translate_text("flash.login_failed", locale=locale)
                errors["password"] = translate_text("flash.login_failed", locale=locale)
                flash(translate_text("flash.login_failed", locale=locale), "error")

    return render_template(
        "login.html",
        title=translate_text("meta.login", locale=locale),
        active_page="login",
        errors=errors,
        form_values=form_values,
        next_target=next_target,
        demo_email=DEMO_LOGIN_EMAIL,
        demo_password=DEMO_LOGIN_PASSWORD,
        show_demo_hint=(not SUPABASE_ENABLED and SHOW_DEMO_CREDENTIALS_HINT),
    )


@app.route("/signup", methods=["GET", "POST"])
def signup():
    locale = get_locale()
    next_raw = request.form.get("next") if request.method == "POST" else request.args.get("next")
    next_target = safe_redirect_path(next_raw)

    if is_authenticated():
        return redirect(next_target)

    form_values = {
        "email": "",
    }
    errors: dict[str, str] = {}

    if request.method == "POST":
        form_values["email"] = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        password_confirm = request.form.get("password_confirm", "")

        if not form_values["email"]:
            errors["email"] = translate_text("error.required", locale=locale)
        elif not EMAIL_RE.match(form_values["email"]):
            errors["email"] = translate_text("error.invalid_email", locale=locale)

        if not password:
            errors["password"] = translate_text("error.required", locale=locale)
        elif len(password) < MIN_PASSWORD_LENGTH:
            errors["password"] = translate_text("error.password_length", locale=locale, min=MIN_PASSWORD_LENGTH)

        if password != password_confirm:
            errors["password_confirm"] = translate_text("error.password_mismatch", locale=locale)

        if errors:
            flash(translate_text("flash.validation_error", locale=locale), "error")
        elif not SUPABASE_ENABLED:
            flash(translate_text("flash.supabase_not_configured", locale=locale), "error")
        else:
            supabase = create_supabase_runtime_client(SUPABASE_ANON_KEY)
            if supabase is None:
                flash(translate_text("flash.supabase_not_configured", locale=locale), "error")
            else:
                try:
                    auth_response = supabase.auth.sign_up(
                        {
                            "email": form_values["email"],
                            "password": password,
                        }
                    )
                except Exception:
                    auth_response = None

                auth_user = _extract_auth_user(auth_response)
                auth_session = _extract_auth_session(auth_response)
                if auth_user and auth_session and _cache_supabase_user(auth_user):
                    _cache_supabase_tokens(auth_session)
                    flash(translate_text("flash.signup_success", locale=locale), "success")
                    return redirect(next_target)

                if auth_user:
                    flash(translate_text("flash.signup_confirm", locale=locale), "success")
                    return redirect(url_for("login"))

                errors["email"] = translate_text("flash.signup_failed", locale=locale)
                flash(translate_text("flash.signup_failed", locale=locale), "error")

    return render_template(
        "signup.html",
        title=translate_text("meta.signup", locale=locale),
        active_page="signup",
        errors=errors,
        form_values=form_values,
        next_target=next_target,
    )


@app.route("/logout", methods=["POST"])
def logout():
    locale = get_locale()
    if SUPABASE_ENABLED:
        supabase, _user_id = get_authenticated_supabase_client()
        if supabase is not None:
            try:
                supabase.auth.sign_out()
            except Exception:
                pass
    logout_user()
    flash(translate_text("flash.logged_out", locale=locale), "success")
    return redirect(url_for("login"))


@app.route("/")
def home():
    locale = get_locale()
    recent_boards = sorted(
        get_runtime_board_catalog(),
        key=lambda item: int(item.get("created_order", 0)),
        reverse=True,
    )
    return render_template(
        "home.html",
        title=translate_text("meta.home", locale=locale),
        active_page="home",
        boards=recent_boards,
    )


@app.route("/user", methods=["GET", "POST"])
def user():
    locale = get_locale()
    form_values = default_user_values()
    errors: dict[str, str] = {}
    save_message = ""

    if request.method == "POST":
        form_values = {
            "display_name": request.form.get("display_name", ""),
            "email": request.form.get("email", ""),
            "about": request.form.get("about", ""),
        }
        errors = validate_user_form(form_values, locale)

        if errors:
            save_message = translate_text("flash.validation_error", locale=locale)
            flash(save_message, "error")
        else:
            if SUPABASE_ENABLED:
                supabase, user_id = get_authenticated_supabase_client()
                if supabase is None or not user_id:
                    save_message = translate_text("flash.login_failed", locale=locale)
                    flash(save_message, "error")
                else:
                    try:
                        supabase.table("profiles").upsert(
                            {
                                "id": user_id,
                                "display_name": form_values["display_name"],
                                "email": form_values["email"],
                                "about": form_values["about"],
                            }
                        ).execute()
                        session[SESSION_SB_USER_EMAIL] = form_values["email"].strip().lower()
                        session[SESSION_SB_DISPLAY_NAME] = form_values["display_name"].strip()
                        save_message = translate_text("flash.profile_saved", locale=locale)
                        flash(save_message, "success")
                    except Exception:
                        save_message = translate_text("flash.validation_error", locale=locale)
                        flash(save_message, "error")
            else:
                runtime_key = _runtime_store_key()
                RUNTIME_USER_PROFILES[runtime_key] = dict(form_values)
                save_message = translate_text("flash.profile_saved", locale=locale)
                flash(save_message, "success")

    return render_template(
        "user.html",
        title=translate_text("meta.user", locale=locale),
        active_page="user",
        errors=errors,
        form_values=form_values,
        save_message=save_message,
    )


@app.route("/boards")
def boards():
    locale = get_locale()

    search_query = request.args.get("q", "").strip()
    member_filter = request.args.get("member", "all")
    sort_option = request.args.get("sort", "name_asc")

    if member_filter not in {"all", "small", "medium", "large"}:
        member_filter = "all"

    if sort_option not in {"name_asc", "name_desc", "members_desc", "members_asc"}:
        sort_option = "name_asc"

    visible_boards = board_collection(search_query, member_filter, sort_option)
    filters_open = bool(search_query or member_filter != "all" or sort_option != "name_asc")

    status_message = translate_text(
        "boards.status",
        locale=locale,
        count=len(visible_boards),
        sort_label=translate_text(f"boards.sort.{sort_option}", locale=locale),
    )

    return render_template(
        "boards.html",
        title=translate_text("meta.boards", locale=locale),
        active_page="boards",
        boards=visible_boards,
        search_query=search_query,
        member_filter=member_filter,
        sort_option=sort_option,
        status_message=status_message,
        filters_open=filters_open,
    )


@app.route("/board")
def board_alias():
    return board("product-roadmap")


@app.route("/boards/<slug>")
def board(slug: str):
    locale = get_locale()
    board_data = enrich_board(slug)
    if board_data is None:
        abort(404)

    return render_template(
        "board.html",
        title=f"{board_data['name']} | Trellar",
        active_page="boards",
        board=board_data,
        board_slug=slug,
    )


@app.route("/settings", methods=["GET", "POST"])
def settings():
    locale = get_locale()
    form_values = default_settings_values()
    errors: dict[str, str] = {}
    save_message = ""

    if request.method == "POST":
        form_values = {
            "workspace_name": request.form.get("workspace_name", ""),
            "default_visibility": request.form.get("default_visibility", ""),
            "digest_frequency": request.form.get("digest_frequency", ""),
            "channel": request.form.get("channel", ""),
            "card_template": request.form.get("card_template", ""),
        }
        errors = validate_settings_form(form_values, locale)

        if errors:
            save_message = translate_text("flash.validation_error", locale=locale)
            flash(save_message, "error")
        else:
            if SUPABASE_ENABLED:
                supabase, user_id = get_authenticated_supabase_client()
                if supabase is None or not user_id:
                    save_message = translate_text("flash.login_failed", locale=locale)
                    flash(save_message, "error")
                else:
                    try:
                        supabase.table("user_settings").upsert(
                            {
                                "user_id": user_id,
                                **form_values,
                            }
                        ).execute()
                        save_message = translate_text("flash.settings_saved", locale=locale)
                        flash(save_message, "success")
                    except Exception:
                        save_message = translate_text("flash.validation_error", locale=locale)
                        flash(save_message, "error")
            else:
                runtime_key = _runtime_store_key()
                RUNTIME_SETTINGS[runtime_key] = dict(form_values)
                save_message = translate_text("flash.settings_saved", locale=locale)
                flash(save_message, "success")

    return render_template(
        "settings.html",
        title=translate_text("meta.settings", locale=locale),
        active_page="settings",
        errors=errors,
        form_values=form_values,
        save_message=save_message,
    )


@app.route("/activity")
def activity():
    locale = get_locale()
    page_raw = request.args.get("page", "1")

    try:
        page = max(int(page_raw), 1)
    except ValueError:
        page = 1

    per_page = 3
    activity_store = get_runtime_activity()
    total = len(activity_store)
    visible_count = min(page * per_page, total)

    visible_items: list[dict[str, str]] = []
    for index, item in enumerate(activity_store[:visible_count], start=1):
        enriched = dict(item)
        enriched["display_time"] = format_relative_time(str(item["time_iso"]), locale)
        enriched["index"] = str(index)
        visible_items.append(enriched)

    has_more = visible_count < total
    next_page = page + 1

    loaded_message = ""
    loaded_param = request.args.get("loaded")
    if loaded_param:
        loaded_message = translate_text("activity.loaded", locale=locale, count=visible_count)

    return render_template(
        "activity.html",
        title=translate_text("meta.activity", locale=locale),
        active_page="activity",
        activity_items=visible_items,
        has_more=has_more,
        next_page=next_page,
        loaded_message=loaded_message,
    )


@app.route("/activity/export.csv")
def export_activity_csv():
    activity_store = get_runtime_activity()
    output = StringIO()
    writer = csv.DictWriter(output, fieldnames=["timestamp", "board", "title"])
    writer.writeheader()

    for item in activity_store:
        writer.writerow(
            {
                "timestamp": item.get("time_iso", ""),
                "board": item.get("board", ""),
                "title": item.get("title", ""),
            }
        )

    response = make_response(output.getvalue())
    response.headers["Content-Type"] = "text/csv; charset=utf-8"
    response.headers["Content-Disposition"] = "attachment; filename=trellar-activity.csv"
    return response


@app.route("/api/boards/create", methods=["POST"])
def api_create_board():
    payload = request.get_json(silent=True) or {}
    name = str(payload.get("name", "")).strip()
    description = str(payload.get("description", "")).strip()

    if not name:
        return jsonify({"ok": False, "error": "missing_name"}), 400

    if len(name) > 80:
        return jsonify({"ok": False, "error": "name_too_long"}), 400

    if len(description) > 220:
        return jsonify({"ok": False, "error": "description_too_long"}), 400

    if SUPABASE_ENABLED:
        supabase, user_id = get_authenticated_supabase_client()
        if supabase is None or not user_id:
            return jsonify({"ok": False, "error": "unauthorized"}), 401

        board_state = get_runtime_boards()
        slug = create_board_slug(name, set(board_state.keys()))
        board_description = description or "New board"

        try:
            board_response = supabase.table("boards").insert(
                {
                    "owner_id": user_id,
                    "slug": slug,
                    "name": name,
                    "description": board_description,
                    "members": 1,
                }
            ).execute()
            board_row = _first_response_row(board_response)
            board_id = str((board_row or {}).get("id", "")).strip()
            if not board_id:
                return jsonify({"ok": False, "error": "create_failed"}), 500

            lane_payload = [
                {"board_id": board_id, "name": "Backlog", "position": 0},
                {"board_id": board_id, "name": "In Progress", "position": 1},
                {"board_id": board_id, "name": "Done", "position": 2},
            ]
            supabase.table("lanes").insert(lane_payload).execute()
            add_activity_entry(f'Created board "{name}"', name)
        except Exception:
            return jsonify({"ok": False, "error": "create_failed"}), 500

        return (
            jsonify(
                {
                    "ok": True,
                    "slug": slug,
                    "name": name,
                    "description": board_description,
                }
            ),
            201,
        )

    board_store = get_runtime_boards()
    board_catalog = get_runtime_board_catalog()
    slug = create_board_slug(name, set(board_store.keys()))
    board_description = description or "New board"

    board_store[slug] = {
        "name": name,
        "description": board_description,
        "lanes": default_new_board_lanes(),
    }

    board_catalog.append(
        {
            "slug": slug,
            "name": name,
            "description": board_description,
            "members": 1,
            "created_order": next_created_order(board_catalog),
        }
    )

    add_activity_entry(f'Created board "{name}"', name)

    return (
        jsonify(
            {
                "ok": True,
                "slug": slug,
                "name": name,
                "description": board_description,
            }
        ),
        201,
    )


@app.route("/api/boards/<slug>/cards/create", methods=["POST"])
def api_create_card(slug: str):
    payload = request.get_json(silent=True) or {}
    title = str(payload.get("title", "")).strip()
    meta = str(payload.get("meta", "")).strip()
    status = str(payload.get("status", "")).strip() or "New"

    if not title:
        return jsonify({"ok": False, "error": "missing_title"}), 400

    if len(title) > 120:
        return jsonify({"ok": False, "error": "title_too_long"}), 400

    if len(meta) > 160:
        return jsonify({"ok": False, "error": "meta_too_long"}), 400

    if len(status) > 60:
        return jsonify({"ok": False, "error": "status_too_long"}), 400

    lane_index_raw = payload.get("lane_index", 0)
    try:
        lane_index = int(lane_index_raw)
    except (TypeError, ValueError):
        return jsonify({"ok": False, "error": "invalid_lane"}), 400

    if SUPABASE_ENABLED:
        supabase, user_id = get_authenticated_supabase_client()
        if supabase is None or not user_id:
            return jsonify({"ok": False, "error": "unauthorized"}), 401

        board_row = _supabase_board_by_slug(supabase, user_id, slug)
        if board_row is None:
            return jsonify({"ok": False, "error": "board_not_found"}), 404

        board_id = str(board_row.get("id", "")).strip()
        lanes = _supabase_lanes_for_board(supabase, board_id)
        if lane_index < 0 or lane_index >= len(lanes):
            return jsonify({"ok": False, "error": "invalid_lane"}), 400

        target_lane = lanes[lane_index]
        lane_id = str(target_lane.get("id", "")).strip()
        lane_name = str(target_lane.get("name", "Lane"))
        card_payload = {
            "board_id": board_id,
            "lane_id": lane_id,
            "title": title,
            "meta": meta or "No details",
            "status": status,
            "position": _supabase_next_card_position(supabase, lane_id),
            "archived": False,
        }
        try:
            created = _first_response_row(supabase.table("cards").insert(card_payload).execute())
        except Exception:
            return jsonify({"ok": False, "error": "create_failed"}), 500

        if not created:
            return jsonify({"ok": False, "error": "create_failed"}), 500

        card = {
            "id": str(created.get("id", "")),
            "title": str(created.get("title", title)),
            "meta": str(created.get("meta", meta or "No details")),
            "status": str(created.get("status", status)),
        }
        board_name = str(board_row.get("name", "Board"))
        add_activity_entry(f'Added card "{title}"', board_name)
        return (
            jsonify(
                {
                    "ok": True,
                    "card": card,
                    "lane_index": lane_index,
                    "lane_name": lane_name,
                }
            ),
            201,
        )

    board_data = get_runtime_boards().get(slug)
    if board_data is None:
        return jsonify({"ok": False, "error": "board_not_found"}), 404

    lanes = board_data.get("lanes", [])
    if lane_index < 0 or lane_index >= len(lanes):
        return jsonify({"ok": False, "error": "invalid_lane"}), 400

    card = {
        "id": create_card_id(slug),
        "title": title,
        "meta": meta or "No details",
        "status": status,
    }
    lanes[lane_index].get("cards", []).append(card)

    lane_name = str(lanes[lane_index].get("name", "Lane"))
    board_name = str(board_data.get("name", "Board"))
    add_activity_entry(f'Added card "{title}"', board_name)

    return (
        jsonify(
            {
                "ok": True,
                "card": card,
                "lane_index": lane_index,
                "lane_name": lane_name,
            }
        ),
        201,
    )


@app.route("/api/boards/<slug>/cards/move", methods=["POST"])
def api_move_card(slug: str):
    payload = request.get_json(silent=True) or {}
    card_id = str(payload.get("card_id", "")).strip()
    direction = str(payload.get("direction", "")).strip().lower()

    if not card_id:
        return jsonify({"ok": False, "error": "missing_card_id"}), 400

    if direction not in {"left", "right"}:
        return jsonify({"ok": False, "error": "invalid_direction"}), 400

    if SUPABASE_ENABLED:
        supabase, user_id = get_authenticated_supabase_client()
        if supabase is None or not user_id:
            return jsonify({"ok": False, "error": "unauthorized"}), 401

        board_row = _supabase_board_by_slug(supabase, user_id, slug)
        if board_row is None:
            return jsonify({"ok": False, "error": "board_not_found"}), 404

        board_id = str(board_row.get("id", "")).strip()
        lanes = _supabase_lanes_for_board(supabase, board_id)
        card_row = _first_response_row(
            supabase.table("cards")
            .select("id,title,lane_id")
            .eq("board_id", board_id)
            .eq("id", card_id)
            .eq("archived", False)
            .limit(1)
            .execute()
        )
        if not card_row:
            return jsonify({"ok": False, "error": "card_not_found"}), 404

        current_lane_id = str(card_row.get("lane_id", ""))
        lane_index = _supabase_lane_index(lanes, current_lane_id)
        if lane_index < 0:
            return jsonify({"ok": False, "error": "invalid_lane"}), 400

        target_lane_index = lane_index - 1 if direction == "left" else lane_index + 1
        if target_lane_index < 0 or target_lane_index >= len(lanes):
            return jsonify({"ok": False, "error": "cannot_move"}), 400

        target_lane = lanes[target_lane_index]
        target_lane_id = str(target_lane.get("id", ""))
        target_lane_name = str(target_lane.get("name", "Lane"))
        try:
            supabase.table("cards").update(
                {
                    "lane_id": target_lane_id,
                    "position": _supabase_next_card_position(supabase, target_lane_id),
                }
            ).eq("id", card_id).execute()
        except Exception:
            return jsonify({"ok": False, "error": "cannot_move"}), 400

        card_title = str(card_row.get("title", "Card"))
        board_name = str(board_row.get("name", "Board"))
        add_activity_entry(f'Moved "{card_title}" to {target_lane_name}', board_name)

        return jsonify(
            {
                "ok": True,
                "card_id": card_id,
                "from_lane_index": lane_index,
                "to_lane_index": target_lane_index,
                "card_title": card_title,
                "target_lane_name": target_lane_name,
            }
        )

    board_data = get_runtime_boards().get(slug)
    if board_data is None:
        return jsonify({"ok": False, "error": "board_not_found"}), 404

    location = find_card_location(board_data, card_id)
    if location is None:
        return jsonify({"ok": False, "error": "card_not_found"}), 404

    lane_index, card_index = location
    lanes = board_data.get("lanes", [])
    target_lane_index = lane_index - 1 if direction == "left" else lane_index + 1

    if target_lane_index < 0 or target_lane_index >= len(lanes):
        return jsonify({"ok": False, "error": "cannot_move"}), 400

    source_cards = lanes[lane_index].get("cards", [])
    target_cards = lanes[target_lane_index].get("cards", [])
    moved_card = source_cards.pop(card_index)
    target_cards.append(moved_card)

    card_title = str(moved_card.get("title", "Card"))
    target_lane_name = str(lanes[target_lane_index].get("name", "Lane"))
    board_name = str(board_data.get("name", "Board"))
    add_activity_entry(f'Moved "{card_title}" to {target_lane_name}', board_name)

    return jsonify(
        {
            "ok": True,
            "card_id": card_id,
            "from_lane_index": lane_index,
            "to_lane_index": target_lane_index,
            "card_title": card_title,
            "target_lane_name": target_lane_name,
        }
    )


@app.route("/api/boards/<slug>/cards/archive", methods=["POST"])
def api_archive_card(slug: str):
    payload = request.get_json(silent=True) or {}
    card_id = str(payload.get("card_id", "")).strip()
    if not card_id:
        return jsonify({"ok": False, "error": "missing_card_id"}), 400

    if SUPABASE_ENABLED:
        supabase, user_id = get_authenticated_supabase_client()
        if supabase is None or not user_id:
            return jsonify({"ok": False, "error": "unauthorized"}), 401

        board_row = _supabase_board_by_slug(supabase, user_id, slug)
        if board_row is None:
            return jsonify({"ok": False, "error": "board_not_found"}), 404

        board_id = str(board_row.get("id", "")).strip()
        card_row = _first_response_row(
            supabase.table("cards")
            .select("id,title,lane_id,position,meta,status")
            .eq("board_id", board_id)
            .eq("id", card_id)
            .eq("archived", False)
            .limit(1)
            .execute()
        )
        if not card_row:
            return jsonify({"ok": False, "error": "card_not_found"}), 404

        try:
            supabase.table("cards").update({"archived": True}).eq("id", card_id).execute()
        except Exception:
            return jsonify({"ok": False, "error": "archive_failed"}), 400

        lanes = _supabase_lanes_for_board(supabase, board_id)
        lane_id = str(card_row.get("lane_id", ""))
        lane_index = _supabase_lane_index(lanes, lane_id)

        archive_buffer = get_runtime_archive_buffer()
        archive_buffer[card_id] = {
            "slug": slug,
            "lane_id": lane_id,
            "card_position": _safe_int(card_row.get("position"), default=0),
            "card": {
                "id": card_id,
                "title": str(card_row.get("title", "Card")),
                "meta": str(card_row.get("meta", "")),
                "status": str(card_row.get("status", "New")),
            },
        }

        card_title = str(card_row.get("title", "Card"))
        board_name = str(board_row.get("name", "Board"))
        add_activity_entry(f'Archived "{card_title}"', board_name)

        return jsonify(
            {
                "ok": True,
                "card_id": card_id,
                "card_title": card_title,
                "lane_index": lane_index,
            }
        )

    board_data = get_runtime_boards().get(slug)
    if board_data is None:
        return jsonify({"ok": False, "error": "board_not_found"}), 404

    location = find_card_location(board_data, card_id)
    if location is None:
        return jsonify({"ok": False, "error": "card_not_found"}), 404

    lane_index, card_index = location
    lanes = board_data.get("lanes", [])
    cards = lanes[lane_index].get("cards", [])
    archived_card = cards.pop(card_index)

    archive_buffer = get_runtime_archive_buffer()
    archive_buffer[card_id] = {
        "slug": slug,
        "lane_index": lane_index,
        "card_index": card_index,
        "card": archived_card,
    }

    card_title = str(archived_card.get("title", "Card"))
    board_name = str(board_data.get("name", "Board"))
    add_activity_entry(f'Archived "{card_title}"', board_name)

    return jsonify(
        {
            "ok": True,
            "card_id": card_id,
            "card_title": card_title,
            "lane_index": lane_index,
        }
    )


@app.route("/api/boards/<slug>/cards/restore", methods=["POST"])
def api_restore_card(slug: str):
    payload = request.get_json(silent=True) or {}
    card_id = str(payload.get("card_id", "")).strip()
    if not card_id:
        return jsonify({"ok": False, "error": "missing_card_id"}), 400

    if SUPABASE_ENABLED:
        supabase, user_id = get_authenticated_supabase_client()
        if supabase is None or not user_id:
            return jsonify({"ok": False, "error": "unauthorized"}), 401

        board_row = _supabase_board_by_slug(supabase, user_id, slug)
        if board_row is None:
            return jsonify({"ok": False, "error": "board_not_found"}), 404

        archive_buffer = get_runtime_archive_buffer()
        archived = archive_buffer.get(card_id)
        if not archived or archived.get("slug") != slug:
            return jsonify({"ok": False, "error": "archived_card_not_found"}), 404

        board_id = str(board_row.get("id", "")).strip()
        lanes = _supabase_lanes_for_board(supabase, board_id)
        lane_id = str(archived.get("lane_id", ""))
        lane_index = _supabase_lane_index(lanes, lane_id)
        if lane_index < 0:
            return jsonify({"ok": False, "error": "invalid_lane"}), 400

        try:
            supabase.table("cards").update(
                {
                    "archived": False,
                    "lane_id": lane_id,
                    "position": _supabase_next_card_position(supabase, lane_id),
                }
            ).eq("id", card_id).execute()
        except Exception:
            return jsonify({"ok": False, "error": "restore_failed"}), 400

        archived_card = _to_dict(archived.get("card"))
        card_title = str(archived_card.get("title", "Card"))
        board_name = str(board_row.get("name", "Board"))
        archive_buffer.pop(card_id, None)
        add_activity_entry(f'Restored "{card_title}"', board_name)

        return jsonify(
            {
                "ok": True,
                "card_id": card_id,
                "card_title": card_title,
                "lane_index": lane_index,
                "card_index": _safe_int(archived.get("card_position"), default=0),
            }
        )

    board_data = get_runtime_boards().get(slug)
    if board_data is None:
        return jsonify({"ok": False, "error": "board_not_found"}), 404

    archive_buffer = get_runtime_archive_buffer()
    archived = archive_buffer.get(card_id)
    if not archived or archived.get("slug") != slug:
        return jsonify({"ok": False, "error": "archived_card_not_found"}), 404

    lanes = board_data.get("lanes", [])
    lane_index = int(archived.get("lane_index", 0))
    card_index = int(archived.get("card_index", 0))
    if lane_index < 0 or lane_index >= len(lanes):
        return jsonify({"ok": False, "error": "invalid_lane"}), 400

    lane_cards = lanes[lane_index].get("cards", [])
    insert_index = min(max(card_index, 0), len(lane_cards))
    restored_card = archived.get("card", {})
    lane_cards.insert(insert_index, restored_card)
    archive_buffer.pop(card_id, None)

    card_title = str(restored_card.get("title", "Card"))
    board_name = str(board_data.get("name", "Board"))
    add_activity_entry(f'Restored "{card_title}"', board_name)

    return jsonify(
        {
            "ok": True,
            "card_id": card_id,
            "card_title": card_title,
            "lane_index": lane_index,
            "card_index": insert_index,
        }
    )


@app.route("/help")
def help_page():
    locale = get_locale()
    return render_template(
        "help.html",
        title=translate_text("meta.help", locale=locale),
        active_page="help",
    )


@app.route("/docs/<path:filename>")
def docs_file(filename: str):
    return send_from_directory(os.path.join(app.root_path, "docs"), filename)


@app.errorhandler(404)
def not_found(_error):
    locale = get_locale()
    return (
        render_template(
            "404.html",
            title=translate_text("meta.not_found", locale=locale),
            active_page="",
        ),
        404,
    )


@app.errorhandler(500)
def server_error(_error):
    locale = get_locale()
    return (
        render_template(
            "500.html",
            title=translate_text("meta.server_error", locale=locale),
            active_page="",
        ),
        500,
    )


if __name__ == "__main__":
    app.run(debug=True)
