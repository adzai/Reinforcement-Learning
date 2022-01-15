import argparse
import sys

parser = argparse.ArgumentParser(description="Snake Game RL")
parser.add_argument("-t", "--train", action="store_true", help="Training mode")
parser.add_argument("-p", "--play", action="store_true", help="AI playing mode")
parser.add_argument("-q", "--q_table", type=str, help="Path to .npy Q table")
parser.add_argument(
    "--depth",
    action="store_true",
    help="Will add information about 1 more turn to the state space. DISCLAIMER: If the agent was trained with --depth, it must be played with --depth as well.",
)
parser.add_argument(
    "--speed",
    type=int,
    default=100,
    help="Speed of updating the snake game played in pygame in milliseconds. Default: 100",
)
parser.add_argument(
    "-l",
    "--learning_rate",
    type=float,
    default=0.75,
    help="Learning rate used for training. Default: 0.75",
)
parser.add_argument(
    "-d",
    "--decay_rate",
    type=float,
    default=0.0004,
    help="Decay rate used for training. Default: 0.0004",
)
parser.add_argument(
    "--total_episodes",
    type=int,
    default=100_000,
    help="Number of total episodes that should be used for training. Default: 100000",
)
parser.add_argument(
    "-o",
    "--output",
    type=str,
    default="snake_q_table.npy",
    help="Path where .npy Q table will be saved. Default: snake_q_table.npy",
)
parser.add_argument(
    "--env_size",
    default=3,
    type=int,
    help="Environment size (e.g. --env_size 16 will create 16x16 env).",
)
args = parser.parse_args()


if not args.train and not args.play:
    print("Must specify mode: Use either --play or --train")
    sys.exit(1)


if args.play:
    from GUI import ai_play

    ai_play(args)
else:
    from q_learning import train

    train(args)
