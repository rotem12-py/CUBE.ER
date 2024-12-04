import random

# possible moves for every cube type
x2_chars = [" U", " U'", " U2", " R", " R2", " R'", " F", " F'", " F2"]
x3_chars = [' U', " U'", ' U2' , ' D', " D'", ' D2', ' L', " L'", ' L2' , ' R', " R", ' R2', ' F', " F'", ' F2', ' B', " B'", ' B2']


def scramble(scr_type):
    result = []
    result_txt = ""
    scramble_chars = []
    scr_length = 0

    # set the scramble possible characters and length depending on scr_type
    if scr_type == "3x3":
        scramble_chars = x3_chars
        scr_length = 20
    elif scr_type == "2x2":
        scramble_chars = x2_chars
        scr_length = 9

    # add a random char to the scramble from the possible characters
    for i in range(scr_length):
        chosen_move = random.choice(scramble_chars)

        # if the new movie has the same letter as the same one, replace it
        while len(result) > 0 and chosen_move[1] == result[-1][1]:
            chosen_move = random.choice(scramble_chars)

        result.append(chosen_move)

    for i in result:
        result_txt += i
    return result_txt


