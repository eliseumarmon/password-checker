"""Password reuse across distinct accounts."""
from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Dict, Hashable, List, Optional, Protocol, Sequence, Set, TypeVar


class HasPassword(Protocol):
    password: str


T = TypeVar("T", bound=HasPassword)


def shared_password_groups(items: Sequence[T],
                           account_of: Callable[[T], Optional[Hashable]]) -> List[List[T]]:
    """Group items by password when more than one distinct account uses it.

    Items with an empty password, or whose account is None, are ignored.
    Groups and their members keep first-seen order.
    """
    members: Dict[str, List[T]] = defaultdict(list)
    accounts: Dict[str, Set[Any]] = defaultdict(set)
    for item in items:
        account = account_of(item)
        if not item.password or account is None:
            continue
        members[item.password].append(item)
        accounts[item.password].add(account)
    return [group for password, group in members.items() if len(accounts[password]) > 1]
