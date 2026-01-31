import click
from analyzer.analyzer import analyze_repository

@click.group()
def platform():
    pass

@platform.command()
@click.argument("repo")
def repo(repo):
    result = analyze_repository(repo)
    click.echo(result)

if __name__ == "__main__":
    platform()
