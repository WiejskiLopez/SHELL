from __future__ import annotations


def _run_process(process: 'Process') -> None:
    pc = process.process_command_
    kwargs = {
        'capture_output': True,
        'text': True,
        'encoding': 'utf-8',
        'errors': 'replace',
        'cwd': pc.cwd_,
    }
    if pc.stdin_ is not None:
        kwargs['input'] = pc.stdin_
    if pc.timeout_ is not None:
        kwargs['timeout'] = pc.timeout_
    if pc.env_ is not None:
        kwargs['env'] = pc.env_
    completed = process._runner(pc.cmd_, **kwargs)
    process._returncode = completed.returncode
    process._stdout = completed.stdout
    process._stderr = completed.stderr
