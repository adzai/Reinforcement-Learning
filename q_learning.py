import matplotlib.pyplot as plt
from environment import Environment
from constants import REWARD, SURVIVAL_REWARD
import numpy as np
import random


def train(args):
    env = Environment(args.env_size, args.depth)
    total_episodes = args.total_episodes
    learning_rate = args.learning_rate
    gamma = 0.90
    epsilon = 1.0
    max_epsilon = 1.0
    min_epsilon = 0.01
    decay_rate = args.decay_rate
    explored_states = dict()
    q_table = np.zeros((env.observation_space_len, env.action_space_len))
    rewards = []
    aggr_ep_rewards = {"ep": [], "avg": [], "max": [], "moves": [], "states": []}
    moves_per_episode = []
    for episode in range(1, total_episodes + 1):
        state = env.reset()
        done = False
        total_rewards = 0
        moves = 0
        while not done and moves != 100_000:
            exploit = random.uniform(0, 1)

            if exploit > epsilon:
                action = np.argmax(q_table[state, :])
            else:
                action = env.get_random_action()

            new_state, reward, done = env.step(action)
            moves += 1

            if not done:
                total_rewards += reward // REWARD * 10
                reward += SURVIVAL_REWARD

            explored_states[state] = 1
            q_table[state, action] = q_table[state, action] + learning_rate * (
                reward + gamma * np.max(q_table[new_state, :]) - q_table[state, action]
            )

            state = new_state

        moves_per_episode.append(moves)
        epsilon = min_epsilon + (max_epsilon - min_epsilon) * np.exp(
            -decay_rate * episode
        )
        if episode % 100 == 0:
            aggr_ep_rewards["ep"].append(episode)
            aggr_ep_rewards["avg"].append(sum(rewards) / episode)
            aggr_ep_rewards["max"].append(max(rewards))
            aggr_ep_rewards["moves"].append(sum(moves_per_episode) / episode)
            aggr_ep_rewards["states"].append(len(explored_states.keys()))
            print(
                f"{episode} ep, average score: {sum(rewards) / episode:.2f}, epsilon: {epsilon}, explored states: {len(explored_states.keys())}, max score: {max(rewards)}, average moves: {sum(moves_per_episode) / episode:.2f}"
            )
        rewards.append(total_rewards)

    print("Score over time: " + str(sum(rewards) / total_episodes))

    np.save(args.output, q_table)
    plt.plot(aggr_ep_rewards["ep"], aggr_ep_rewards["avg"], label="average rewards")
    # plt.plot(aggr_ep_rewards["ep"], aggr_ep_rewards["max"], label="max rewards")
    plt.plot(aggr_ep_rewards["ep"], aggr_ep_rewards["moves"], label="average moves")
    plt.plot(aggr_ep_rewards["ep"], aggr_ep_rewards["states"], label="explored states")
    plt.legend(loc=4)
    qtable_save_location = args.output
    print(f"Q table saved to {qtable_save_location}")
    fig_save_location = qtable_save_location.split(".npy")[0] + "_fig.png"
    plt.savefig(fig_save_location)
    print(f"Plot saved to {fig_save_location}")
