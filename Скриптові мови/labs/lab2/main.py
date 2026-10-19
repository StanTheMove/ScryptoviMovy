import argparse
import sys

from labs.lab2.task1 import run_demo
from labs.lab2.task2 import main as run_analyze


def main():
    parser = argparse.ArgumentParser(description="Lab2 Main Dispatcher")
    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("demo", help="Запуск Завдання 1")
    subparsers.add_parser("analyze", help="Запуск Завдання 2")

    args, remaining = parser.parse_known_args()

    if args.command == "demo":
        run_demo()
    elif args.command == "analyze":
        sys.argv = [sys.argv[0]] + remaining
        run_analyze()


if __name__ == "__main__":
    main()
