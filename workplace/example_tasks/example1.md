cd platform
python ..\utils\init_count_files_task.py

cd ..\tasker\default-tasker
python entrypoint.py --task-name count-files --source-dir C:\temp\count-files --work-dir C:\temp\count-files