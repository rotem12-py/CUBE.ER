def get_best_solve(session):
    # If there are no solves in the session, return None
    if not session.solves:
        return None

    # Find the best solve by iterating over all solves and checking their time
    best_solve = session.solves[0]  # Start with the first solve as the best
    for solve in session.solves:
        if solve.time < best_solve.time:
            best_solve = solve  # Update if we find a faster time

    return best_solve


def calc_small_ao(solves, ao_length):
    num = 0
    ao_result = 0
    ao_list = []
    dnf_count = 0

    if len(solves) < ao_length:
        return None

    for solve in solves:
        if solve.status == "DNF":
            dnf_count += 1
            ao_list.append(float('inf'))
        else:
            ao_list.append(solve.time)

    if dnf_count > 1:
        return "DNF"


    ao_list.remove(min(ao_list))
    ao_list.remove(max(ao_list))

    for solve in ao_list:
        num += solve

    ao_result = round(num / (ao_length-2), 2)

    return ao_result


def calc_big_ao(solves, ao_length):
    num = 0
    ao_result = 0
    ao_list = []
    dnf_count = 0

    solves_to_remove = int(ao_length * 0.05)

    if len(solves) < ao_length:
        return None

    for solve in solves:
        if solve.status == 'DNF':
            ao_list.append(float('inf'))
            dnf_count += 1
        else:
            ao_list.append(solve.time)

    if dnf_count > solves_to_remove:
        return "DNF"

    for i in range(solves_to_remove):
        ao_list.remove(min(ao_list))
        ao_list.remove(max(ao_list))

    for solve in ao_list:
        num += solve

    ao_result = round(num / len(ao_list), 2)
    return ao_result

def best_ao(solves, ao_length):
    all_ao = []  # This will store the valid AO results.

    # Loop through the solves to calculate the AOs
    for i in range(len(solves) - ao_length + 1):
        if ao_length == 3:
            ao = calc_mo3(solves=solves[i:i + ao_length])
        elif 3 < ao_length < 13:
            ao = calc_small_ao(ao_length=ao_length, solves=solves[i:i + ao_length])
        elif ao_length > 12:
            ao = calc_big_ao(ao_length=ao_length, solves=solves[i:i + ao_length])

        if ao != "DNF":
            all_ao.append(ao)


    if all_ao:
        return min(all_ao)
    else:
        return "DNF"


def calc_mo3(solves):
    mo_list = []
    num = 0
    mo_result = 0
    if len(solves) < 3:
        return None

    for solve in solves:
        if solve.status == "DNF":
            return "DNF"
        mo_list.append(solve.time)

    for solve in mo_list:
        num += solve
    mo_result = round(num / 3, 2)
    return mo_result





