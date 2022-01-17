# Reinforcement Learning on a Snake Game

## Install
`git clone https://github.com/adzai/Reinforcement-Learning.git`

`cd Reinfocement-Learning`

`pip install -r requirements.txt`


## Run

```
usage: run.py [-h] [-t] [-p] [-q Q_TABLE] [--depth] [--speed SPEED]
              [-l LEARNING_RATE] [-d DECAY_RATE]
              [--total_episodes TOTAL_EPISODES] [-o OUTPUT]
              [--env_size ENV_SIZE]

Snake Game RL

optional arguments:
  -h, --help            show this help message and exit
  -t, --train           Training mode
  -p, --play            AI playing mode
  -q Q_TABLE, --q_table Q_TABLE
                        Path to .npy Q table
  --depth               Will add information about 1 more turn to the
                        state space. DISCLAIMER: If the agent was
                        trained with --depth, it must be played with
                        --depth as well.
  --speed SPEED         Speed of updating the snake game played in
                        pygame in milliseconds. Default: 100
  -l LEARNING_RATE, --learning_rate LEARNING_RATE
                        Learning rate used for training. Default:
                        0.75
  -d DECAY_RATE, --decay_rate DECAY_RATE
                        Decay rate used for training. Default: 0.007
  --total_episodes TOTAL_EPISODES
                        Number of total episodes that should be used
                        for training. Default: 100000
  -o OUTPUT, --output OUTPUT
                        Path where .npy Q table will be saved.
                        Default: snake_q_table.npy
  --env_size ENV_SIZE   Environment size (e.g. --env_size 16 will
                        create 16x16 env).
```

Pre trained Q tables are in the Q_tables folder, corresponding plots
are in the plots folder.

## Train the agent
**Standard state space**
```
python run.py --train --env_size 3 --o "3-depth.npy" --total_episodes 500000 --decay_rate=0.01
```
**Extended state space**
```
python run.py --train --env_size 3 --o "3-depth.npy" --total_episodes 500000 --decay_rate=0.01 --depth
```

## Visualization
**Trained on standard state space**
```
python run.py --play --env_size 3 --q_table Q_tables/3.npy
```
**Trained on extended state space**
```
python run.py --play --env_size 3 --q_table Q_tables/3.npy --depth
```

You can also try a differently sized environment (up to 16x16)
```
python run.py --play --env_size 16 --q_table Q_tables/3.npy --depth
```
