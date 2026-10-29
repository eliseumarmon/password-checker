"""Password reuse across distinct accounts."""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Dict, Hashable, List, Optional, Sequence, Set, TypeVar

T = TypeVar("T")


def shared_password_groups(items: Sequence[T],
                           account_of: Callable[[T], Optional[Hashable]]) -> List[List[T]]:
    """Group items by password when more than one distinct account uses it.

    Items with an empty password, or whose account is None, are ignored.
    Groups and their members keep first-seen order.
    """
    members: Dict[str, List[T]] = defaultdict(list)
    accounts: Dict[str, Set[Any]] = defaultdict(set)
    for item in items:
        password = item.password  # type: ignore[attr-defined]
        account = account_of(item)
        if not password or account is None:
            continue
        members[password].append(item)
        accounts[password].add(account)
    return [group for password, group in members.items() if len(accounts[password]) > 1]
