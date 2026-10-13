"""Pure, import-inert definitions for the round-10 bounded synthetic probe.

No module-level enumeration, I/O, random source, parser, SQL, or experiment.
The evaluator accepts ORIGINAL bodies and ORIGINAL projections only.
"""

from itertools import combinations, product
import hashlib
import json

VARIABLES = ("x", "y", "z")
DOMAIN = (0, 1, 2)
KEY_CHOICES = (-1, 0, 1, 2)  # -1 means absent; lexicographic product order.
EXPECTED_BODIES = 129
EXPECTED_PAIRS = 2739
EXPECTED_MODELS = 64
EXPECTED_COMPARISONS = 175296


def canonical_json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True)


def digest(value):
    return hashlib.sha256(canonical_json(value).encode("ascii")).hexdigest()


def active_variables(body):
    return tuple(sorted({variable for atom in body for variable in atom}))


def subsets(variables):
    """Cardinality first, then lexical order; empty subset is index zero."""
    return tuple(part for size in range(len(variables) + 1)
                 for part in combinations(variables, size))


def bodies():
    atoms = tuple(product(VARIABLES, repeat=2))
    for size in (1, 2, 3):
        yield from combinations(atoms, size)


def models():
    """Exactly all partial functions DOMAIN -> DOMAIN, including empty."""
    for model_index, choices in enumerate(product(KEY_CHOICES, repeat=3)):
        rows = tuple((key, value) for key, value in zip(DOMAIN, choices)
                     if value != -1)
        yield model_index, choices, rows


def pairs_for(body_index, body):
    projections = subsets(active_variables(body))
    for pair_index, (left_index, right_index) in enumerate(
            combinations(range(len(projections)), 2)):
        signature = {"body": body, "M": projections[left_index],
                     "N": projections[right_index], "head": "unit"}
        yield {
            "pair_id": f"b{body_index:03d}-p{pair_index:02d}",
            "body_index": body_index,
            "pair_index": pair_index,
            "subset_indices": (left_index, right_index),
            "signature": signature,
            "signature_sha256": digest(signature),
        }


def inventory():
    """Metadata-only enumeration; does not evaluate, chase, or cover."""
    for body_index, body in enumerate(bodies()):
        yield body_index, body, tuple(pairs_for(body_index, body))


def full_key_chase(original_body):
    """Repeated union of values with equal canonical keys, to a fixed point.

    Canonical representatives are lexically smallest variables. Every original
    body survives as an independent case even if the chased atom set coincides
    with another original case. Deduplication applies only inside the chase.
    """
    variables = active_variables(original_body)
    parent = {variable: variable for variable in variables}
    steps = []
    scans = 0

    def representative(variable):
        while parent[variable] != variable:
            variable = parent[variable]
        return variable

    while True:
        scans += 1
        changed = False
        by_key = {}
        for key, value in original_body:
            key_root, value_root = representative(key), representative(value)
            if key_root not in by_key:
                by_key[key_root] = value_root
                continue
            previous = representative(by_key[key_root])
            value_root = representative(value_root)
            if previous != value_root:
                keep, merge = sorted((previous, value_root))
                parent[merge] = keep
                steps.append({"scan": scans, "key": key_root,
                              "unified": (previous, value_root),
                              "representative": keep})
                changed = True
        if not changed:
            break
    mapping = {variable: representative(variable) for variable in variables}
    chased = tuple(sorted({(mapping[key], mapping[value])
                           for key, value in original_body}))
    return chased, mapping, {"scans": scans, "unions": len(steps), "steps": steps}


def enumerate_endomorphisms(chased_body):
    """Inspect EVERY self-map, with mapping and atom-check costs explicit."""
    variables = active_variables(chased_body)
    atom_set = set(chased_body)
    accepted = []
    attempted = 0
    atom_checks = 0
    for images in product(variables, repeat=len(variables)):
        mapping = dict(zip(variables, images))
        attempted += 1
        valid = True
        for key, value in chased_body:
            atom_checks += 1
            if (mapping[key], mapping[value]) not in atom_set:
                valid = False
            # Deliberately no short circuit: every mapped atom is inspected.
        if valid:
            accepted.append(mapping)
    return tuple(accepted), {"self_maps_attempted": attempted,
                             "mapped_atoms_checked": atom_checks,
                             "endomorphisms_accepted": len(accepted)}


def fd_closure(seed, chased_body):
    closure = set(seed)
    edge_checks = 0
    scans = 0
    while True:
        scans += 1
        before = len(closure)
        for key, value in chased_body:
            edge_checks += 1
            if key in closure:
                closure.add(value)
        if len(closure) == before:
            return closure, {"closure_scans": scans, "fd_edge_checks": edge_checks}


def covers(chased_body, chased_M, chased_N, endomorphisms):
    """N subset cl(alpha(M)); M subset cl(beta(N)); alpha/beta independent.

    All accepted maps are examined in both directions even after a witness.
    No identity-only substitution and no bounded count evidence enters here.
    """
    forward = None
    reverse = None
    costs = {"endomorphism_direction_checks": 0, "closure_calls": 0,
             "closure_scans": 0, "fd_edge_checks": 0}
    for endomorphism_index, mapping in enumerate(endomorphisms):
        for source, target, direction in ((chased_M, chased_N, "forward"),
                                           (chased_N, chased_M, "reverse")):
            closed, closure_cost = fd_closure(
                (mapping[variable] for variable in source), chased_body)
            costs["endomorphism_direction_checks"] += 1
            costs["closure_calls"] += 1
            for key, value in closure_cost.items():
                costs[key] += value
            if set(target).issubset(closed):
                witness = {"endomorphism_index": endomorphism_index,
                           "mapping": mapping, "closure": tuple(sorted(closed))}
                if direction == "forward" and forward is None:
                    forward = witness
                if direction == "reverse" and reverse is None:
                    reverse = witness
    return {"forward": forward is not None, "reverse": reverse is not None,
            "cover_EQ": forward is not None and reverse is not None,
            "alpha_witness": forward, "beta_witness": reverse}, costs


def original_counts(original_body, original_subsets, rows):
    """Direct finite assignment evaluator; independent of chase/FD/cover.

    Empty projection has count one iff at least one assignment satisfies the
    body, otherwise zero. Tuples are sets, not bags. Both columns use DOMAIN.
    """
    variables = active_variables(original_body)
    relation = set(rows)
    projected = [set() for _ in original_subsets]
    assignments = 0
    atom_checks = 0
    satisfying = 0
    for values in product(DOMAIN, repeat=len(variables)):
        assignment = dict(zip(variables, values))
        assignments += 1
        valid = True
        for key, value in original_body:
            atom_checks += 1
            if (assignment[key], assignment[value]) not in relation:
                valid = False
        if valid:
            satisfying += 1
            for subset, bucket in zip(original_subsets, projected):
                bucket.add(tuple(assignment[variable] for variable in subset))
    return tuple(map(len, projected)), {
        "assignments_enumerated": assignments,
        "original_atoms_checked": atom_checks,
        "satisfying_assignments": satisfying,
        "projection_insert_attempts": satisfying * len(original_subsets),
    }


def classify(cover_EQ, equality_bits):
    if cover_EQ and "0" in equality_bits:
        return "SUFFICIENCY_FALSIFIED"
    if not cover_EQ and "0" not in equality_bits:
        return "BOUNDED_INCONCLUSIVE_CANDIDATE"
    if cover_EQ:
        return "COVER_EQ_BOUNDED_CONFIRMED"
    return "NONCOVER_BOUNDED_DISTINGUISHED"


def check_controls(body, projections, count_vectors, chased_body, chase_map,
                   pair_results, model_table):
    """Controls refer to cases ALREADY in the fixed denominator."""
    controls = []
    specified = (
        ("same_key_chase", (("x", "y"), ("x", "z")),
         ("y",), ("y", "z"), "all_equal"),
        ("triangle_legal_PK", (("x", "y"), ("y", "z"), ("z", "x")),
         ("x",), ("x", "y"), "all_equal"),
        ("legal_projection_distinction", (("x", "y"),),
         ("x",), ("y",), "specific_distinction"),
    )
    for name, required_body, M, N, expectation in specified:
        if body != required_body:
            continue
        left, right = projections.index(M), projections.index(N)
        selected = next(result for result in pair_results
                        if tuple(result["subset_indices"]) == (left, right))
        details = {"name": name, "pair_id": selected["pair_id"],
                   "expectation": expectation}
        if expectation == "all_equal":
            passed = (count_vectors[left] == count_vectors[right]
                      and selected["cover"]["cover_EQ"])
            if name == "same_key_chase":
                passed = passed and chase_map["y"] == chase_map["z"]
            details.update({"all_64_equal": count_vectors[left] == count_vectors[right],
                            "cover_EQ": selected["cover"]["cover_EQ"],
                            "chased_body": chased_body, "chase_map": chase_map})
        else:
            model_index = next(index for index, choices, rows in model_table
                               if rows == ((0, 0), (1, 0)))
            actual = (count_vectors[left][model_index], count_vectors[right][model_index])
            passed = actual == (2, 1) and not selected["cover"]["cover_EQ"]
            details.update({"model_index": model_index, "actual": actual,
                            "expected": (2, 1),
                            "cover_EQ": selected["cover"]["cover_EQ"]})
        controls.append({**details, "status": "PASS" if passed else "FAIL"})
    return controls
