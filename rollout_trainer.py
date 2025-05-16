def train(agent, environment, episodes=1000):
    for ep in range(episodes):
        state = environment.reset()
        done = False
        while not done:
            action = agent.act(state)
            next_state, reward, done, info = environment.step(action)
            state = next_state
        print(f"Episode {ep+1} completed.")