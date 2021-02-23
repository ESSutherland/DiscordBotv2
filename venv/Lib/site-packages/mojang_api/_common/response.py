#!/usr/bin/env python3

class APIResponse:
    def __new__(cls, response, *args, **kwargs):
        data = None
        try:
            data = response.json()
        except ValueError:
            return {'response': response}
        else:
            if isinstance(data, dict):
                return {'response': response, 'data': dict(data)}
            elif isinstance(data, list):
                return {'response': response, 'data': list(data)}
            else:
                raise TypeError(
                    'response\'s JSON data must be of type \'dict\' or \'list\'')
