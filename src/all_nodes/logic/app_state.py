class AppState:
    _instance = None
    _state = {}

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(AppState, cls).__new__(cls, *args, **kwargs)
        return cls._instance

    def set_state_var(self, key, value):
        self._state[key] = value

    def get_state_var(self, key, default=None):
        return self._state.get(key, default)

    def remove_state_var(self, key):
        if key in self._state:
            del self._state[key]

    def clear_state(self):
        self._state.clear()


APP_STATE = AppState()
