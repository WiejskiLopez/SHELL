from shell.component.prompt.prompt_type.prompt_type import PromptType


def _init_prompt_cli(prompt_cli) -> None:
    cli_prompt = prompt_cli._app.cli_.cli_properties_.prompt_
    prompt_cli.prompt_file_._file_name = 'cli.prompt.md'
    prompt_cli.prompt_file_._file_body = cli_prompt
    prompt_cli.prompt_file_._prompt_type = PromptType.CLI
