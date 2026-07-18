#!/usr/bin/env python
"""Debug signature end detection."""
c = """    @classmethod
    def create(
        cls,
        *,
        id_: SchedulerDefinitionId,
        name: SchedulerName,
        trigger_config: TriggerConfig,
        action_config: ActionConfig,
        execution_policy: ExecutionPolicy,
        now: CreatedAt,
        enabled: bool = True,
        description: SchedulerDescription | None = None,
    ) -> SchedulerDefinition:
        return cls._new("""

sig_end = c.find("):\n")
print(f"sig_end: {sig_end}")
if sig_end >= 0:
    print(f"Found: {repr(c[sig_end:sig_end+20])}")
else:
    # Try ) -> type:
    sig_end = c.find(") ->")
    if sig_end >= 0:
        print(f"Found -> at {sig_end}: {repr(c[sig_end:sig_end+30])}")
        sig_end = c.find(":\n", sig_end)
        if sig_end >= 0:
            print(f"Found :\\n at {sig_end}")
