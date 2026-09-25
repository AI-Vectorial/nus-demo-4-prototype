"""Model calls: composing answers, and embedding text.

Callers use generate() and embed(). Nothing outside app.generate.client knows
which provider is behind them.
"""

from __future__ import annotations

from app.generate.client import ProviderError, embed, generate, health

__all__ = ["ProviderError", "embed", "generate", "health"]
