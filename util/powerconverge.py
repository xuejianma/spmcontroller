
def power_converge(curr_x, curr_y, target_y, learning_rate = 0.5):
    new_x = curr_x - learning_rate * (target_y - curr_y)
    return new_x
