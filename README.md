# Reinforcement-Learning

```
usage: snake.py [-h] [-t] [-p] [-q Q_TABLE] [-l LEARNING_RATE] [-d DECAY_RATE] [--total_episodes TOTAL_EPISODES] [-o OUTPUT]
                [--env_size ENV_SIZE]

Snake Game RL

optional arguments:
  -h, --help            show this help message and exit
  -t, --train           Training mode
  -p, --play            AI playing mode
  -q Q_TABLE, --q_table Q_TABLE
                        Path to .npy Q table
  -l LEARNING_RATE, --learning_rate LEARNING_RATE
                        Learning rate used for training
  -d DECAY_RATE, --decay_rate DECAY_RATE
                        Decay rate used for training
  --total_episodes TOTAL_EPISODES
                        Number of total episodes that should be used for training
  -o OUTPUT, --output OUTPUT
                        Path where .npy Q table will be saved
  --env_size ENV_SIZE   Environment size (e.g. --env_size 16 will create 16x16 env). When --play is supplied, only 16x16 is used
```
