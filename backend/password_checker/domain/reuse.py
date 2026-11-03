"""Password reuse across distinct accounts."""
from __future__ import annotations

from collections import defaultdict
from collections.abc import Callable, Hashable, Sequence
from typing import Any, Protocol

from .accounts import origin_account


class HasPassword(Protocol):
    password: str


def shared_password_groups[T: HasPassword](items: Sequence[T],
                                           account_of: Callable[[T], Hashable | None]) -> list[list[T]]:
    """Group items by password when more than one distinct account uses it.

    Items with an empty password, or whose account is None, are ignored.
    Groups and their members keep first-seen order.
    """
    members: dict[str, list[T]] = defaultdict(list)
    accounts: dict[str, set[Any]] = defaultdict(set)
    for item in items:
        account = account_of(item)
        if not item.password or account is None:
            continue
        members[item.password].append(item)
        accounts[item.password].add(account)
    return [group for password, group in members.items() if len(accounts[password]) > 1]


def reused_password_groups[T: HasPassword](items: Sequence[T]) -> list[list[T]]:
    """The reuse rule used by the workspace audit."""
    return shared_password_groups(items, origin_account)
