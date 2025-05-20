# Contributing to trame

1. Clone the repository using `git clone`
2. Install pre-commit via `pip install pre-commit`
3. Run `pre-commit install` to set up pre-commit hooks
4. Run `pre-commit install --hook-type commit-msg` to register commit-msg hook
5. Make changes to the code, and commit your changes to a separate branch using
   [conventionalcommits](https://www.conventionalcommits.org/en/v1.0.0/) for our
   semantic release CI.
6. Create a fork of the repository on GitHub
7. Push your branch to your fork, and open a pull request

## Tips

1. When first creating a new project, it is helpful to run
   `pre-commit run --all-files` to ensure all files pass the pre-commit checks.
2. A quick way to fix `ruff` issues is by installing ruff (`pip install ruff`)
   and running the `ruff check --fix .` or `ruff format` command at the root of
   your repository.
3. A quick way to fix `codespell` issues is by installing codespell
   (`pip install codespell`) and running the `codespell -w` command at the root
   of your directory.
4. The
   [.codespellrc file](https://github.com/codespell-project/codespell#using-a-config-file)
   can be used fix any other codespell issues, such as ignoring certain files,
   directories, words, or regular expressions.
