from random import choice, randint

all_chars = [" U", " U'", " U2", " D", " D'", " D2", " B", " B'", " B2", " R", " R'", " R2", " L"," L'", " L2", " F", " F'", " F2",]
scramble = []

def generate_scramble():
    scramble.clear()  # Clear previous scramble if any
    
    for i in range(randint(15, 20)):
        x = choice(all_chars)
        
        while len(scramble) > 0:
            last_move_base = scramble[-1].strip()[0]  # Get the base move (face) of the last move
            new_move_base = x.strip()[0]  # Get the base move (face) of the new move
            
            # Check if the new move conflicts with the last move (e.g., U, U', or U2)
            if new_move_base == last_move_base:
                x = choice(all_chars)  # Re-select the move
            else:
                break
        
        scramble.append(x)
    
    scramble_str = ''.join(scramble)
    return scramble_str 