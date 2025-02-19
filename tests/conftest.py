"""Test setup defaults."""
# Copyright 2017 Kenneth Reitz, 2019 Matthew Peveler, 2025 EMJ

from __future__ import annotations

from hypothesis import settings

settings.register_profile("no_deadline", max_examples=2000, deadline=None)
settings.register_profile("quick", max_examples=500)
settings.register_profile("dev", max_examples=50)
