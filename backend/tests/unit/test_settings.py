"""
Unit tests for the settings fields whose type is the validation.

`COOKIE_SAMESITE` is typed `Literal["lax", "strict", "none"]` rather than `str`
because Starlette's `Response.set_cookie` accepts only those three values. Typing
it moves the check to application startup: a misconfigured environment fails loudly
instead of producing a cookie header the browser silently discards, which is the
kind of fault that only shows up as "login works locally but not on staging".

Values are injected as environment variables rather than constructor keywords —
that is the path a real deployment uses, and `BaseSettings.__init__` reserves its
own underscore-prefixed keywords, so a `**overrides` splat does not type check.
`_env_file=None` keeps the developer's real `backend/.env` out of the assertions.
"""

import pytest
from pydantic import ValidationError

from src.config.settings import Settings

SAMESITE_ENV = "COOKIE_SAMESITE"


def _load(monkeypatch: pytest.MonkeyPatch, value: str | None) -> Settings:
    """Build Settings with COOKIE_SAMESITE set to `value` (or unset if None)."""
    if value is None:
        monkeypatch.delenv(SAMESITE_ENV, raising=False)
    else:
        monkeypatch.setenv(SAMESITE_ENV, value)
    return Settings(_env_file=None)


class TestCookieSameSite:
    def test_defaults_to_lax_when_unset(self, monkeypatch: pytest.MonkeyPatch) -> None:
        loaded: str = _load(monkeypatch, None).COOKIE_SAMESITE

        assert loaded == "lax"

    @pytest.mark.parametrize("value", ["lax", "strict", "none"])
    def test_accepts_each_value_starlette_supports(
        self, monkeypatch: pytest.MonkeyPatch, value: str
    ) -> None:
        # Bound to a lower-case local because ruff's SIM300 reads the ALL-CAPS
        # attribute as a constant and flags `....COOKIE_SAMESITE == value` as a
        # Yoda condition.
        loaded: str = _load(monkeypatch, value).COOKIE_SAMESITE

        assert loaded == value

    @pytest.mark.parametrize(
        "value",
        [
            "Lax",  # capitalised: a plausible typo, and not what set_cookie wants
            "none ",  # trailing space off an .env line
            "",  # present but empty
            "sameorigin",  # confused with the X-Frame-Options vocabulary
        ],
    )
    def test_rejects_anything_else_at_construction(
        self, monkeypatch: pytest.MonkeyPatch, value: str
    ) -> None:
        with pytest.raises(ValidationError):
            _load(monkeypatch, value)
