# Fixtures
# get_state: Callable[[], dict[str, EntityState]],
# verify_state: Callable[
#     [EvalTask, dict[str, EntityState], dict[str, EntityState]],
#     Awaitable[dict[str, Any]],
# ],
# caplog: pytest.LogCaptureFixture,

# Extract response
# regexp = re.compile(r"```yaml\s*(.*?)\s+```", re.DOTALL | re.MULTILINE)
# m = regexp.match(response)
# if not m or (match_text := m.group(1)) is None:
#     raise ValueError(f"Could not extract regexp: {m}")
# response = match_text


# prepare dump output
# yaml.SafeDumper.add_multi_representer(
#     enum.StrEnum,
#     yaml.representer.SafeRepresenter.represent_str,
# )

# Get the states of entity before the automation
# states = get_state()


# Verify state after the automation runs
# updated_states = get_state()
# unexpected_states: dict[str, Any] | str
# try:
#     unexpected_states = await verify_state(eval_task, states, updated_states)
# except ValueError as err:
#     unexpected_states = f"Error verifying state: {err}"


# Record the output with expected changes
# output = ModelOutput(
#     uuid=str(uuid.uuid4()),  # Unique based on the model evaluated
#     task_id=eval_task.task_id,
#     category=eval_task.category,
#     task={
#         "input_text": eval_task.input_text,
#         "expect_changes": {
#             k: dataclasses.asdict(v)
#             for k, v in (eval_task.expect_changes or {}).items()
#         },
#     },
#     response=response,
#     context={
#         "unexpected_states": unexpected_states,
#         "conversation_trace": conversation_trace,
#         # TODO: Would be useful to support something like --dump-states for fully examining states
#         # "state": states,
#         # "updated_states": updated_states,
#         "tries": tries,
#     },
# )
# _LOGGER.info(output)
# eval_record_writer.write(dataclasses.asdict(output))
