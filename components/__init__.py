"""
Sentio Training App - UI Components

Production-grade UI components with distinctive aesthetics.
"""

from .theme import apply_theme, get_theme_css
from .tooltips import TOOLTIPS, get_tooltip, get_how_it_works
from .data_flow import render_data_flow_header, render_file_location, render_activity_log
from .i18n import (
    t,
    init_language,
    get_current_language,
    set_language,
    render_language_toggle,
    get_translated_tooltip,
    get_translated_how_it_works,
    TRANSLATIONS,
    LANGUAGES,
)

__all__ = [
    'apply_theme',
    'get_theme_css',
    'TOOLTIPS',
    'get_tooltip',
    'get_how_it_works',
    'render_data_flow_header',
    'render_file_location',
    'render_activity_log',
    # i18n exports
    't',
    'init_language',
    'get_current_language',
    'set_language',
    'render_language_toggle',
    'get_translated_tooltip',
    'get_translated_how_it_works',
    'TRANSLATIONS',
    'LANGUAGES',
]
