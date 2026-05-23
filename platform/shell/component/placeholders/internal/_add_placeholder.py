from shell.constants.constants import DIR_OUTPUT, DIR_INPUT, DIR_ARCHIVE, DIR_TEMP

_NODE_SUBDIRS = (DIR_OUTPUT, DIR_INPUT, DIR_ARCHIVE, DIR_TEMP)


def _add_placeholder(placeholders, name: str, value: str) -> None:
    token = f'$${name}$$'
    if '_dir' in name or '_path' in name:
        value = value.replace('\\', '/')
    placeholders._placeholder_list.append((token, value))
    if name == 'node_dir':
        for subdir in _NODE_SUBDIRS:
            subdir_name = f'{subdir}_node_dir'
            subdir_value = f'{value}/.node/{subdir}'
            placeholders._placeholder_list.append((f'$${subdir_name}$$', subdir_value))
