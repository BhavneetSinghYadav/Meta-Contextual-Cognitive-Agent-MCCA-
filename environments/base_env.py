class BaseEnvironment:
    def reset(self):
        raise NotImplementedError

    def step(self, action):
        raise NotImplementedError

    def get_state(self):
        raise NotImplementedError

    def render(self):
        pass