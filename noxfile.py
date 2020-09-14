import nox


@nox.session
def lint(session):
    session.install('flake8', 'isort')
    session.run('flake8', '--show-source', '--statistics')
    session.run('isort', '.')
