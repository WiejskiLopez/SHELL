### platform/utils/class_slots.md
```
﻿# class_slots

| class_name | slot_name |
|---|---|
| AgentProperties | _app |
| AgentProperties | _model |
| AgentProperties | _retries |
| AgentProperties | _retry_delay |
| AgentProperties | _timeout |
| App | _app_configuration |
| App | _app_node |
| App | _app_properties |
| App | _app_trace |
| App | _app_utils |
| App | _result |
| App | _runner |
| AppNode | _app |
| AppNode | _lock |
| AppNode | _node |
| AppProperties | _autopilot |
| AppProperties | _command |
| AppProperties | _log_level |
| AppProperties | _max_step |
| AppProperties | _mode |
| AppProperties | _model |
| AppProperties | _name |
| AppProperties | _no_ask_user |
| AppProperties | _retries |
| AppProperties | _role |
| AppProperties | _timeout |
| AppProperties | _type |
| AppUtils | _placeholders |
| Cli | _app |
| Cli | _cli_properties |
| CliProperties | _add_dirs |
| CliProperties | _allow_all_paths |
| CliProperties | _allow_all_tools |
| CliProperties | _autopilot |
| CliProperties | _clean |
| CliProperties | _clean_out |
| CliProperties | _prompt |
| CliProperties | _dry_run |
| CliProperties | _help |
| CliProperties | _log_level |
| CliProperties | _max_step |
| CliProperties | _mode |
| CliProperties | _model |
| CliProperties | _no_ask_user |
| CliProperties | _node_dir |
| CliProperties | _output_format |
| CliProperties | _parent_node_dir |
| CliProperties | _parent_thread_id |
| CliProperties | _prompt_dir |
| CliProperties | _role |
| CliProperties | _runner_root_dir |
| CliProperties | _source_dir |
| CliProperties | _step_number |
| CliProperties | _task_dir |
| CliProperties | _task_name |
| CliProperties | _thread_id |
| CliProperties | _timeout |
| CliProperties | _type |
| CliProperties | _version |
| CliProperties | _work_dir |
| Command | _command |
| Config | _app |
| Config | _config_dict |
| Config | _config_path |
| Event | _event_type |
| Event | _log_level_code |
| Event | _message |
| Event | _returncode |
| Event | _source |
| Event | _stderr |
| Event | _stdout |
| Event | _timestamp |
| File | _file_body |
| File | _file_path |
| FilePrompt | _file_body |
| FilePrompt | _file_name |
| FilePrompt | _prompt_type |
| Locker | _app |
| Locker | _lock_path |
| Logger | _app |
| Logger | _cached_logger |
| Logger | _log_level |
| Node | _app |
| Node | _node_archive |
| Node | _node_config |
| Node | _node_dir |
| Node | _node_input |
| Node | _node_logs |
| Node | _node_name |
| Node | _node_output |
| Node | _node_prompt |
| Node | _node_properties |
| Node | _node_scripts |
| Node | _node_stage |
| Node | _node_status |
| Node | _node_task |
| Node | _node_temp |
| NodeArchive | _app |
| NodeArchive | _module_status |
| NodeConfig | _app |
| NodeConfig | _module_status |
| NodeConfig | _node_config_file_body |
| NodeConfig | _node_properties |
| NodeLogs | _app |
| NodeLogs | _logs_dir |
| NodeLogs | _module_status |
| NodeOutput | _app |
| NodeOutput | _module_status |
| NodeOutput | _output_dir |
| NodeOutput | _output_files_map |
| NodePrompt | _app |
| NodePrompt | _module_status |
| NodePrompt | _prompt |
| NodePrompt | _prompt_dir |
| NodeScripts | _app |
| NodeScripts | _module_status |
| NodeScripts | _scripts_dir |
| NodeStage | _app |
| NodeStage | _module_status |
| NodeStage | _stage |
| NodeStage | _stage_dir |
| NodeStatus | _app |
| NodeStatus | _status |
| NodeTask | _app |
| NodeTask | _module_status |
| NodeTask | _task_md_file_body |
| NodeTask | _task_name |
| NodeTask | _task_yaml_file_body |
| NodeTemp | _app |
| NodeTemp | _module_status |
| NodeTemp | _temp_dir |
| Graph | _app |
| Graph | _status |
| Graph | _sub_nodes |
| Placeholders | _placeholder_list |
| Process | _process_command |
| Process | _returncode |
| Process | _runner |
| Process | _stderr |
| Process | _stdout |
| ProcessCommand | _command |
| Prompt | _app |
| Prompt | _file_prompts |
| Prompt | _prompt_cli |
| Prompt | _prompt_dir |
| Prompt | _prompt_input |
| Prompt | _prompt_role |
| Prompt | _prompt_skill |
| Prompt | _prompt_system |
| Prompt | _prompt_task |
| PromptCli | _app |
| PromptCli | _file_prompt |
| PromptInput | _app |
| PromptInput | _file_prompts |
| PromptRole | _app |
| PromptRole | _file_prompts |
| PromptSkill | _app |
| PromptSkill | _file_prompts |
| PromptSystem | _app |
| PromptSystem | _file_prompts |
| PromptTask | _app |
| PromptTask | _file_prompts |
| Result | _app |
| Result | _returncode |
| Result | _status |
| Result | _stderr |
| Result | _stdout |
| RouterBase | _app |
| RouterBase | _graph |
| RouterBase | _role_to_node_map |
| RouterStage | _app |
| RunnerProperties | _add_dirs |
| Stage | _app |
| Stage | _module_status |
| Stage | _stage_active |
| Stage | _stage_dead |
| Stage | _stage_dir |
| Stage | _stage_done |
| Stage | _stage_history |
| Stage | _stage_ignored |
| Stage | _stage_pending |
| StageActive | _active_dir |
| StageActive | _app |
| StageActive | _module_status |
| StageDead | _app |
| StageDead | _dead_dir |
| StageDead | _module_status |
| StageDone | _app |
| StageDone | _done_dir |
| StageDone | _module_status |
| StageHistory | _app |
| StageHistory | _history_dir |
| StageHistory | _module_status |
| StageIgnored | _app |
| StageIgnored | _ignored_dir |
| StageIgnored | _module_status |
| StagePending | _app |
| StagePending | _module_status |
| StagePending | _pending_dir |
| SubNode | _app |
| SubNode | _is_new |
| SubNode | _node_status |
| SubNode | _sub_node_command |
| SubNode | _sub_node_config_dict |
| SubNode | _sub_node_configuration |
| SubNode | _sub_node_properties |
| SubNodeCommand | _app |
| SubNodeCommand | _command |
| SubNodeConfiguration | _app |
| SubNodeConfiguration | _config |
| SubNodeConfiguration | _mode |
| SubNodeConfiguration | _model |
| SubNodeConfiguration | _node_archive |
| SubNodeConfiguration | _node_config |
| SubNodeConfiguration | _node_input |
| SubNodeConfiguration | _node_output |
| SubNodeConfiguration | _node_prompt |
| SubNodeConfiguration | _node_properties |
| SubNodeConfiguration | _node_stage |
| SubNodeConfiguration | _node_task |
| SubNodeConfiguration | _role |
| SubNodeConfiguration | _runner_root_dir |
| SubNodeConfiguration | _source_dir |
| SubNodeConfiguration | _sub_node |
| SubNodeConfiguration | _sub_node_dir |
| SubNodeConfiguration | _sub_node_name |
| SubNodeConfiguration | _task_name |
| SubNodeConfiguration | _timeout |
| SubNodeConfiguration | _type |
| SubNodeConfiguration | _work_dir |
| SubNodeProperties | _autopilot |
| SubNodeProperties | _command |
| SubNodeProperties | _log_level |
| SubNodeProperties | _max_step |
| SubNodeProperties | _mode |
| SubNodeProperties | _model |
| SubNodeProperties | _name |
| SubNodeProperties | _no_ask_user |
| SubNodeProperties | _retries |
| SubNodeProperties | _role |
| SubNodeProperties | _timeout |
| SubNodeProperties | _type |
| Tasker | _app |
| Tasker | _graph |
| Tasker | _session_id |
| Tool | _app |
| Tool | _tool_properties |
| ToolProperties | _app |
| Worker | _app |
| Worker | _script_file_body |
| Worker | _worker_properties |
| WorkerProperties | _app |
```

### router/default-router/config/config.yaml
```
name: default-router
mode: router
role: router
type: base
# Default configuration for router.
# Values here are merged with node-level overrides defined in task.yaml.
# Node-level values take priority over these defaults.
log_level: INFO  # Default log level for router
max_step: 20     # Maximum TTL step; message with step >= max_step is rejected immediately
```

### router/default-router/entrypoint.py
```
﻿import sys

from shell.app.app import App


def main() -> int:
    app = App.init_app(mode='router', runner_root_dir=__file__)
    return app.run_app()

if __name__ == "__main__":
    sys.exit(main())
```

### router/default-router/manifest.yaml
```
﻿name: default-router
mode: router
role: router
type: default
version: 0.1.0
description: "Router for routing agent structure"

exit_codes:
  0: SUCCESS
  1: ERROR
  2: TIMEOUT
  3: WARNING
  4: LOCKED
  5: QUESTION
  6: WAITING
  7: SKIP
  8: READY
  9: INITIALIZED
  99: CRITICAL

".<node_name>":  # Node name this name was from --node-dir.name cli param or task-file.yaml graph.node-name tag
  input:         #Input folder for files used by App
  output:        #Output folder for files generated by App
  archive:       #Archive folder for save state after App finish his job
  temp:          #Temporary folder place where App can generate temporary files
  log:           #Folder when loggers App can put his working logs
  config:        #Folder containing config.yaml
  scripts:       #Folder contain scripts using by App, scripts generate working logs
  tools:         #Folder contain tools using by App, tools are extra apps who not generating working logs
  router:        #Folder containing <router-name>.route.yaml file

cli_args:
  --node-dir:  #Path to the  node directory
  --task-dir:  #Path to directory containing task files (.md and .yaml); required
  --dry-run:   #Optional; validate router node-dir structure and paths without executing; default empty
  --version:   #Optional; print router version and exit; default empty
  --help:      #Optional; show manifest and exit; default empty
  --clean:     #Optional; clean output/, logs/ and tmp/, then exit; default empty
  --clean-out: #Optional; clean output/, logs/ and tmp/, then run normally; default empty
  --log-level: #Optional; log level: DEBUG, INFO, WARNING, ERROR, CRITICAL; default INFO
  --no-ask-user: #Optional; working without interaction with human; default empty
  --autopilot:  #Optional; autonomic work; default empty
  --add-dir:    #Optional; extra folders like workspaces what App can use; default empty
  --mode:      #Optional; for future multimode support; default is mode from manifest
  --role:      #Optional; for future multirole support; default is role from manifest
  --type:      #Optional; for future multi type support; default is type from manifest
  --work-dir:  #Optional; working directory for agent operations; default c:/temp
  --max-step:  #Optional; maximum TTL step for message routing; default 20
```

### tasker/default-tasker/config/config.yaml
```
name: default-tasker
mode: tasker
role: tasker
type: base
# Default configuration for tasker.
# Values here are merged with node-level overrides defined in task.yaml.
# Node-level values take priority over these defaults.
log_level: INFO  # Default log level for tasker
source_dir: c:/temp/workspace  # Default source directory
max_step: 20     # Maximum TTL step; message with step >= max_step is rejected immediately
```

### tasker/default-tasker/entrypoint.py
```
﻿"""entrypoint.py
Entry point for tasker-worker.
Contains ONLY method calls — no inline logic.

Exit codes for the external orchestrator:
    0 — success
    1 — error
    2 — timeout
    4 — locked
    5 — question
"""

import sys

from shell.app.app import App


def main() -> int:
    app = App.init_app(mode='tasker', runner_root_dir=__file__)
    return app.run_app()

if __name__ == "__main__":
    sys.exit(main())
```

### tasker/default-tasker/examples/my-task.md
```
# my-task

W katalogu c:/temp
1. Utworz prosty projekt aplikacje ktora dodaje 2 liczby i zwraca wynik
2. W jezyku python
3. Napisz do niego testy jednostkowe
4. Uruchom testy i pokaż wynik
```

### tasker/default-tasker/examples/my-task.yaml
```
﻿name: my-task

# session_id — generated by tasker on each init_task run; used by router to tag outgoing messages.
# Allows distinguishing messages from different runs when stage/done/ is checked for idempotency.
# Do not set manually — tasker overwrites this field on every run.
session_id: null

# node mode type values:
#   agent    — AI agent with LLM (e.g. cli-agent)
#   worker   — background worker with some extra logs
#   router   — router for routing between agents and workers
#   tasker    — task manager for managing tasks and graphs
#   tool     — simple tool without complex logic, e.g. for calling external API or running shell commands

# node role values (examples),usually roles are for agent mode
#   analyzer   — analyzes input and produces report
#   developer  — writes or modifies code
#   architect  — designs solution / produces blueprint
#   deployer   — deploys artifacts to environment
#   reviewer   — reviews and validates output
#   tester     — runs tests and reports results

# node status values:
#   new      — defined in yaml, not yet initialized
#   initialized — initialized, but not yet ready for execution
#   ready    — ready for execution
#   pending  — execution started but not finished
#   success  — completed successfully
#   error    — completed with error
#   question — agent stopped and is waiting for extra input
#   waiting  — waiting for external dependency

graph:

  - sub_node_dir: C:\temp\workspace\step-2
    runner_root_dir: C:\Users\palysiewicz\IdeaProjects\MICROSYSTEM\.github\copilot-knowledge\07-automation\agent\cli-agent
    mode: agent
    role: developer
    model: gpt-5-mini
    type: agent
    status: null

  - sub_node_dir: C:\temp\workspace\step-5
    runner_root_dir: C:\Users\palysiewicz\IdeaProjects\MICROSYSTEM\.github\copilot-knowledge\07-automation\agent\cli-agent
    mode: agent
    role: reviewer
    model: gpt-5-mini
    type: agent
    status: null

  - sub_node_dir: C:\temp\workspace\step-6
    runner_root_dir: C:\Users\palysiewicz\IdeaProjects\MICROSYSTEM\.github\copilot-knowledge\07-automation\agent\cli-agent
    mode: agent
    role: analyzer
    model: gpt-5-mini
    type: agent
    status: null

  - sub_node_dir: C:\temp\workspace\step-7
    runner_root_dir: C:\Users\palysiewicz\IdeaProjects\MICROSYSTEM\.github\copilot-knowledge\07-automation\router\default-router
    mode: router
    role: router
    type: router
    status: null

  # Example sub-tasker node (mode: tasker).
  # task_name refers to a subfolder / file pair in source_dir: <task_name>.yaml + <task_name>.md
  # source_dir is optional — inherited from parent CLI --source-dir when omitted.
  - sub_node_dir: C:\temp\workspace\step-8
    runner_root_dir: C:\Users\palysiewicz\IdeaProjects\MICROSYSTEM\.github\copilot-knowledge\07-automation\tasker\default-tasker
    mode: tasker
    role: tasker
    type: tasker
    task_name: my-subtask
    source_dir: null
    status: null
```

### tasker/default-tasker/manifest.yaml
```
﻿name: default-tasker
mode: tasker
role: tasker
type: default
version: 0.1.0
description: "Task-level multi-node orchestrator."

exit_codes:
  0: SUCCESS
  1: ERROR
  2: TIMEOUT
  3: WARNING
  4: LOCKED
  5: QUESTION
  6: WAITING
  7: SKIP
  8: READY
  9: INITIALIZED
  99: CRITICAL

".<node_name>":  # Node name this name was from --node-dir.name cli param or task-file.yaml graph.node-name tag
  input:         #Input folder for files used by App
  output:        #Output folder for files generated by App
  archive:       #Archive folder for save state after App finish his job
  temp:          #Temporary folder place where App can generate temporary files
  log:           #Folder when loggers App can put his working logs
  config:        #Folder containing config.yaml
  scripts:       #Folder contain scripts using by App, scripts generate working logs
  tools:         #Folder contain tools using by App, tools are extra apps who not generating working logs
  task:          #Folder contain task definition files: <task_name>.yaml and <task_name>.md
  ".<node_name>": #Sub node, every node can contain none of some sub nodes

cli_args:
  --node-dir:  #Path to the  node directory
  --dry-run:   #Optional; validate tasker node-dir structure and paths without executing; default empty
  --version:   #Optional; print tasker version and exit; default empty
  --help:      #Optional; show manifest and exit; default empty
  --clean:     #Optional; clean output/, logs/ and tmp/, then exit; default empty
  --clean-out: #Optional; clean output/, logs/ and tmp/, then run normally; default empty
  --log-level: #Optional; log level: DEBUG, INFO, WARNING, ERROR, CRITICAL; default INFO
  --no-ask-user: #Optional; working without interaction with human; default empty
  --autopilot:  #Optional; autonomic work; default empty
  --add-dir:    #Optional; extra folders like workspaces what App can use; default empty
  --mode:      #Optional; for future multimode support; default is mode from manifest
  --role:      #Optional; for future multirole support; default is role from manifest
  --type:      #Optional; for future multi type support; default is type from manifest
  --source-dir: #Required; path to source directory containing task files
  --task-name: #Name of the task to execute; that was name of folder in task repository; 
  --work-dir:  #Optional; working directory for agent operations; default c:/temp
  --max-step:  #Optional; maximum TTL step for message routing; default 20
```

### tools/default-tool/config/config.yaml
```
name: default-tool
mode: tool
role: tool
type: base
# Default configuration for tool.
# Values here are merged with node-level overrides defined in task.yaml.
# Node-level values take priority over these defaults.
log_level: INFO  # Default log level for tool
```

### tools/default-tool/entrypoint.py
```
﻿import sys

from shell.app.app import App


def main() -> int:
    app = App.init_app(mode='tasker', runner_root_dir=__file__)
    return app.run_app()
if __name__ == "__main__":
    sys.exit(main())
```

### tools/default-tool/manifest.yaml
```
﻿name: default-tool
mode: tool
role: tool
type: default
version: 0.1.0
description: "Default tool for do something in agent structure."

exit_codes:
  0: SUCCESS
  1: ERROR
  2: TIMEOUT
  3: WARNING
  4: LOCKED
  5: QUESTION
  6: WAITING
  7: SKIP
  8: READY
  9: INITIALIZED
  99: CRITICAL

".<node_name>":  # Node name this name was from --node-dir.name cli param or task-file.yaml graph.node-name tag
  input:         #Input folder for files used by App
  output:        #Output folder for files generated by App
  archive:       #Archive folder for save state after App finish his job
  temp:          #Temporary folder place where App can generate temporary files
  log:           #Folder when loggers App can put his working logs
  config:        #Folder containing config.yaml
  scripts:       #Folder contain scripts using by App, scripts generate working logs
  tools:         #Folder contain tools using by App, tools are extra apps who not generating working logs
cli_args:
  --node-dir:  #Path to the  node directory
  --dry-run:   #Optional; validate tool node-dir structure and paths without executing; default empty
  --version:   #Optional; print tool version and exit; default empty
  --help:      #Optional; show manifest and exit; default empty
  --clean:     #Optional; clean output/, logs/ and tmp/, then exit; default empty
  --clean-out: #Optional; clean output/, logs/ and tmp/, then run normally; default empty
  --log-level: #Optional; log level: DEBUG, INFO, WARNING, ERROR, CRITICAL; default INFO
  --no-ask-user: #Optional; working without interaction with human; default empty
  --autopilot:  #Optional; autonomic work; default empty
  --add-dir:    #Optional; extra folders like workspaces what App can use; default empty
  --mode:      #Optional; for future multimode support; default is mode from manifest
  --role:      #Optional; for future multirole support; default is role from manifest
  --type:      #Optional; for future multi type support; default is type from manifest
  --work-dir:  #Optional; working directory for agent operations; default c:/temp
```

### worker/default-worker/config/config.yaml
```
# Default configuration for tasker-worker.
# Values here are merged with node-level overrides defined in task.yaml.
# Node-level values take priority over these defaults.

# Number of retries on failure (0 = no retry)
retries: 0

# If true, do not ask user for input (non-interactive mode)
no_ask_user: true

# If true, run in autopilot mode (no confirmation prompts)
autopilot: true
```

### worker/default-worker/entrypoint.py
```
﻿import sys

from shell.app.app import App

def main() -> int:
    app = App.init_app(mode='worker', runner_root_dir=__file__)
    return app.run_app()

if __name__ == "__main__":
    sys.exit(main())
```

### worker/default-worker/manifest.yaml
```
﻿name: default-worker
mode: worker
role: worker
type: default
version: 0.1.0
description: "Default worker for do something in agent structure."

exit_codes:
  0: SUCCESS
  1: ERROR
  2: TIMEOUT
  3: WARNING
  4: LOCKED
  5: QUESTION
  6: WAITING
  7: SKIP
  8: READY
  9: INITIALIZED
  99: CRITICAL

".<node_name>":  # Node name this name was from --node-dir.name cli param or task-file.yaml graph.node-name tag
  input:         #Input folder for files used by App
  output:        #Output folder for files generated by App
  archive:       #Archive folder for save state after App finish his job
  temp:          #Temporary folder place where App can generate temporary files
  log:           #Folder when loggers App can put his working logs
  config:        #Folder containing config.yaml
  scripts:       #Folder contain scripts using by App, scripts generate working logs
  tools:         #Folder contain tools using by App, tools are extra apps who not generating working logs
cli_args:
  --node-dir:  #Path to the  node directory
  --dry-run:   #Optional; validate worker node-dir structure and paths without executing; default empty
  --version:   #Optional; print worker version and exit; default empty
  --help:      #Optional; show manifest and exit; default empty
  --clean:     #Optional; clean output/, logs/ and tmp/, then exit; default empty
  --clean-out: #Optional; clean output/, logs/ and tmp/, then run normally; default empty
  --log-level: #Optional; log level: DEBUG, INFO, WARNING, ERROR, CRITICAL; default INFO
  --no-ask-user: #Optional; working without interaction with human; default empty
  --autopilot:  #Optional; autonomic work; default empty
  --add-dir:    #Optional; extra folders like workspaces what App can use; default empty
  --mode:      #Optional; for future multimode support; default is mode from manifest
  --role:      #Optional; for future multirole support; default is role from manifest
  --type:      #Optional; for future multi type support; default is type from manifest
  --work-dir:  #Optional; working directory for agent operations; default c:/temp
```
