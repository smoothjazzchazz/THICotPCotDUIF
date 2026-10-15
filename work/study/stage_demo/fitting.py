"""Offline prototype fitting using the exact same runner as online inference."""

from work.model.controller import MappingController
from work.model.system_simple_model import run_simulation


def fit_prototypes(examples, make_receiver):
    grouped = {}
    for class_id, levels in examples:
        trace = run_simulation(levels, receiver=make_receiver(),
                               controller=MappingController({}))
        observations = []
        for row in trace:
            observation = row["receiver_state"]
            run = observation.temporal.completed_run
            if run is not None and run.level == 1:
                observations.append(observation.memory)
        if len(observations) != 1:
            raise ValueError("each training example must contain one measured high run")
        grouped.setdefault(class_id, []).append(observations[0])

    prototypes = {}
    for class_id, states in grouped.items():
        average = []
        for index in range(len(states[0])):
            average.append(sum(state[index] for state in states) / len(states))
        prototypes[class_id] = tuple(average)

    # A deliberately small development-only rule, frozen before the demo runs.
    # It is not a calibrated confidence or a general unknown-rejection guarantee.
    classes = sorted(prototypes)
    separations = []
    for index, first in enumerate(classes):
        for second in classes[index + 1:]:
            separations.append(sum((a - b) ** 2 for a, b in
                                   zip(prototypes[first], prototypes[second]))
                               / len(prototypes[first]))
    if not separations or min(separations) <= 0:
        raise ValueError("training needs at least two distinct class prototypes")
    separation = min(separations)
    return prototypes, -separation / 16, separation / 8
