import random

# Function to print the board with better visuals
def print_board(board):
    for i, row in enumerate(board):
        print(" | ".join(row))
        if i < 2:
            print("---|---|---")
    print()

# Function to check for a win
def check_win(board, player):
    for row in board:
        if all([cell == player for cell in row]):
            return True
    for col in range(3):
        if all([board[row][col] == player for row in range(3)]):
            return True
    if all([board[i][i] == player for i in range(3)]) or all([board[i][2 - i] == player for i in range(3)]):
        return True
    return False

# Function to check for a tie
def check_tie(board):
    return all([cell != ' ' for row in board for cell in row])

# Easy level: Computer's move (random)
def computer_move_easy(board):
    while True:
        row, col = random.randint(0, 2), random.randint(0, 2)
        if board[row][col] == ' ':
            board[row][col] = 'O'
            break

# Medium level: Computer's move (block player)
def computer_move_medium(board):
    for row in range(3):
        for col in range(3):
            if board[row][col] == ' ':
                board[row][col] = 'O'
                if check_win(board, 'O'):
                    return
                board[row][col] = ' '
    
    computer_move_easy(board)

# Hard level: Computer's move (Minimax algorithm)
def minimax(board, depth, is_maximizing):
    if check_win(board, 'O'):
        return 1
    if check_win(board, 'X'):
        return -1
    if check_tie(board):
        return 0
    
    if is_maximizing:
        best_score = float('-inf')
        for row in range(3):
            for col in range(3):
                if board[row][col] == ' ':
                    board[row][col] = 'O'
                    score = minimax(board, depth + 1, False)
                    board[row][col] = ' '
                    best_score = max(score, best_score)
        return best_score
    else:
        best_score = float('inf')
        for row in range(3):
            for col in range(3):
                if board[row][col] == ' ':
                    board[row][col] = 'X'
                    score = minimax(board, depth + 1, True)
                    board[row][col] = ' '
                    best_score = min(score, best_score)
        return best_score

def computer_move_hard(board):
    best_score = float('-inf')
    best_move = None
    for row in range(3):
        for col in range(3):
            if board[row][col] == ' ':
                board[row][col] = 'O'
                score = minimax(board, 0, False)
                board[row][col] = ' '
                if score > best_score:
                    best_score = score
                    best_move = (row, col)
    
    if best_move:
        board[best_move[0]][best_move[1]] = 'O'

# Main function to play the game with difficulty levels
def play_game():
    board = [[' ' for _ in range(3)] for _ in range(3)]
    print("Welcome to Tic-Tac-Toe!")
    print("You are 'X' and the computer is 'O'.")
    print("Select difficulty level: 1. Easy 2. Medium 3. Hard")
    difficulty = int(input("Enter your choice (1, 2, or 3): "))
    print_board(board)
    
    while True:
        # Player's move
        while True:
            row = int(input("Enter the row (0, 1, or 2): "))
            col = int(input("Enter the column (0, 1, or 2): "))
            if board[row][col] == ' ':
                board[row][col] = 'X'
                break
            else:
                print("Cell already taken. Try again.")
        print_board(board)
        if check_win(board, 'X'):
            print("Congratulations! You win!")
            break
        if check_tie(board):
            print("It's a tie!")
            break
        
        # Computer's move
        print("Computer's move:")
        if difficulty == 1:
            computer_move_easy(board)
        elif difficulty == 2:
            computer_move_medium(board)
        elif difficulty == 3:
            computer_move_hard(board)
        print_board(board)
        if check_win(board, 'O'):
            print("Computer wins! Better luck next time.")
            break
        if check_tie(board):
            print("It's a tie!")
            break

play_game()