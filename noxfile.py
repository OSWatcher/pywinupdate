from pathlib import Path

import nox

nox.options.sessions = ["fmt", "lint"]


@nox.session
def fmt(session):
    session.install("black")
    session.run("black", "--line-length", "120", ".")


@nox.session
def lint(session):
    session.install("flake8", "flake8-bugbear", "isort")
    session.run("flake8", "--show-source", "--statistics")
    session.run("isort", "--line-length", "120", ".")


@nox.session
def type(session):
    session.install("-r", "requirements.txt")
    session.install("mypy")
    session.run("mypy", ".")


@nox.session
def run(session):
    args = session.posargs
    session.install("-r", "requirements.txt")
    session.run("python", "-m", "winupdate", *args)


@nox.session
def run_installed(session):
    """Install the package and run it from a different directory to test data files inclusion"""
    args = session.posargs
    session.install(".")
    # chdir to home dir
    session.chdir(str(Path.home()))
    session.run("python", "-m", "winupdate", *args)
