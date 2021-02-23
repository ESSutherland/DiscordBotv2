#!/usr/bin/env python3

from functools import wraps

from ..user.player import Player
from ..utils.uuid import is_valid_uuid


def accept_player():
    def decorator(func):
        @wraps(func)
        def with_player_acceptance(*args, **kwargs):
            args = list(args)
            for arg_pos in range(len(args)):
                player = args[arg_pos]
                if isinstance(player, Player):
                    pass
                elif isinstance(player, str):
                    if is_valid_uuid(player):
                        args[arg_pos]=Player(uuid=player)
                    else:
                        args[arg_pos]=Player(username=player)
                else:
                    raise TypeError(
                        'player must be a valid Player, username, or UUID')

            return func(*args, **kwargs)

        return with_player_acceptance

    return decorator
