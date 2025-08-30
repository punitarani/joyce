import pathlib

from dotenv import load_dotenv

# Path of the server app
server_dir = pathlib.Path(__file__).parents[1].resolve()
project_dir = server_dir.parents[1].resolve()

env_path = project_dir.joinpath(".env")

print(f"Loading environment from {env_path}")
load_dotenv(env_path, verbose=True)
