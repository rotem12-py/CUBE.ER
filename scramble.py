import random

# possible moves for every cube type
x3_chars = [' U', " U'", ' U2' , ' D', " D'", ' D2', ' L', " L'", ' L2' , ' R', " R", ' R2', ' F', " F'", ' F2', ' B', " B'", ' B2']

# return the scramble according to the type passed
def scramble(scr_type):
    if scr_type == "3x3":
        return x3()

def x3():
    result = []
    result_txt = ""
    for i in range(20):
        chosen_move = random.choice(x3_chars)
        if len(result) > 0:
            if result[-1][1] != chosen_move[1]:
                result.append(chosen_move)
            else:
                chosen_move = random.choice(x3_chars)
                result.append(chosen_move)
        else:
            result.append(chosen_move)
    for i in result:
        result_txt += i
    return result_txt


