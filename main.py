#----------------
# Created by Leo Xie 
# Visual tool for localization tracking and pure pursuit using python 
# Features moveToPoint performance varient
# Press anywhere in the window for regular moveToPoint
# Hold shift and press anywhere to enter in pure pursuit points
#   then press enter to run pure pursuit
# Stop any movements by pressing reset trajectories anytime
#----------------

import pygame
import math

# Initialize Pygame
pygame.init()

# Set up display
WIDTH, HEIGHT = 1000, 800  # Window dimensions
slider_area_height = 150  # Define the area for sliders at the bottom
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Localization and Pure Pursuit Visualization Tool")

# Define colors
WHITE = (255, 255, 255)
RED = (255, 0, 0)
BLUE = (0, 0, 255)
GREEN = (0, 255, 0)
BLACK = (0, 0, 0)
GRAY = (150, 150, 150)

# Robot properties
robot_size = 20
robot_pos = [WIDTH // 2, (HEIGHT - slider_area_height) // 2]  # Start position
robot_speed = 2  # Default speed of the robot
default_turn_speed = 0.05  # Default turning speed for regular movements
robot_angle = 0  # Initial robot heading (in radians)
lookahead_distance = 50  # Distance for Pure Pursuit lookahead
final_point_tolerance = 5  # Tolerance for stopping at the final point

# PID Control parameters (simulated)
turn_threshold = math.radians(10)  # If the robot is within 10 degrees of the target, stop turning
target_radius = 20  # If the robot is within this radius, ignore turning and move straight

# Tracking variables
target_pos = None
is_moving = False
initial_pos = robot_pos.copy()  # Save the initial position for trajectory
initial_angle = robot_angle     # Save the initial heading
trajectories = []  # List to store all trajectories
current_path = []  # List to store the robot's path during movement

# Pure pursuit points
pure_pursuit_points = []
is_pure_pursuit_mode = False
pure_pursuit_active = False  # Active state for Pure Pursuit running

# Button class for reset functionality
class Button:
    def __init__(self, x, y, w, h, text):
        self.rect = pygame.Rect(x, y, w, h)
        self.text = text
        self.font = pygame.font.Font(None, 24)
        self.color = (200, 200, 200)

    def draw(self, screen):
        pygame.draw.rect(screen, self.color, self.rect)
        text_surface = self.font.render(self.text, True, BLACK)
        screen.blit(text_surface, (self.rect.x + 10, self.rect.y + 5))

    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and self.rect.collidepoint(event.pos):
            return True
        return False

# Slider class to manage movement and turn speed controls
class Slider:
    def __init__(self, x, y, w, min_val, max_val, default_val, label):
        self.x = x
        self.y = y
        self.w = w
        self.h = 20
        self.min_val = min_val
        self.max_val = max_val
        self.value = default_val
        self.label = label
        self.slider_rect = pygame.Rect(self.x, self.y, self.w, self.h)
        self.handle_rect = pygame.Rect(self.x + (self.value - self.min_val) / (self.max_val - self.min_val) * self.w - 5, self.y - 5, 10, 30)
        self.handle_dragging = False

    def draw(self, screen):
        pygame.draw.rect(screen, GRAY, self.slider_rect)
        pygame.draw.rect(screen, BLACK, self.handle_rect)
        font = pygame.font.Font(None, 24)
        label_surface = font.render(f"{self.label}: {self.value:.2f}", True, BLACK)
        screen.blit(label_surface, (self.x + self.w + 20, self.y))

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.handle_rect.collidepoint(event.pos):
                self.handle_dragging = True
        elif event.type == pygame.MOUSEBUTTONUP:
            self.handle_dragging = False
        elif event.type == pygame.MOUSEMOTION:
            if self.handle_dragging:
                self.handle_rect.x = max(self.x, min(event.pos[0] - 5, self.x + self.w - 10))
                self.value = self.min_val + (self.handle_rect.x - self.x) / self.w * (self.max_val - self.min_val)

# Initialize sliders
speed_slider = Slider(50, HEIGHT - 130, 300, 1, 5, 2, "Movement Speed")  # Positioned higher
turn_slider = Slider(50, HEIGHT - 80, 300, 0.01, 0.1, default_turn_speed, "Turn Speed")  # Positioned lower

# Initialize reset button
reset_button = Button(700, HEIGHT - 100, 150, 40, "Reset Trajectories")

# Function to draw the robot as a square
def draw_robot(position, angle):
    robot_rect = pygame.Rect(0, 0, robot_size, robot_size)
    robot_rect.center = position
    pygame.draw.rect(screen, BLUE, robot_rect)
    # Draw a line indicating robot's forward direction
    end_pos = (
        position[0] + robot_size * math.cos(angle),
        position[1] + robot_size * math.sin(angle)
    )
    pygame.draw.line(screen, GREEN, position, end_pos, 2)

# Function to move the robot with two PID controllers (simulated)
def move_robot_with_pid(robot_pos, target_pos, angle, speed, turn_speed):
    dx = target_pos[0] - robot_pos[0]
    dy = target_pos[1] - robot_pos[1]
    distance = math.sqrt(dx ** 2 + dy ** 2)
    target_angle = math.atan2(dy, dx)
    angle_diff = target_angle - angle

    # Normalize the angle difference to the range [-pi, pi]
    angle_diff = (angle_diff + math.pi) % (2 * math.pi) - math.pi

    # Simulated PID control for turning
    turn_delta = turn_speed * angle_diff / abs(angle_diff) if abs(angle_diff) > turn_threshold else 0

    # Combined turn and forward movement
    if distance > target_radius:
        forward_speed = speed * max(0.1, 1 - abs(angle_diff) / math.pi)  # More forward speed when aligned
        robot_pos[0] += forward_speed * math.cos(angle)
        robot_pos[1] += forward_speed * math.sin(angle)
        angle += turn_delta  # Apply turning
    else:
        return True, angle  # Reached the target

    return False, angle

# Pure Pursuit algorithm to follow a list of waypoints
def pure_pursuit(robot_pos, waypoints, lookahead_distance, robot_angle):
    if not waypoints:
        return robot_pos, robot_angle, False

    # Find the lookahead point
    lookahead_point = waypoints[0]
    dx = lookahead_point[0] - robot_pos[0]
    dy = lookahead_point[1] - robot_pos[1]
    distance = math.sqrt(dx**2 + dy**2)

    if distance < lookahead_distance and len(waypoints) > 1:
        waypoints.pop(0)  # Move to the next point

    # Calculate angle to lookahead point
    angle_to_point = math.atan2(dy, dx)
    angle_diff = angle_to_point - robot_angle

    # Normalize the angle difference
    angle_diff = (angle_diff + math.pi) % (2 * math.pi) - math.pi

    # Dynamically adjust turn speed based on the required angle change
    dynamic_turn_speed = min(0.1, max(0.01, abs(angle_diff) * 0.1))

    # Move towards lookahead point
    forward_speed = robot_speed
    robot_angle += dynamic_turn_speed * angle_diff / abs(angle_diff) if abs(angle_diff) > turn_threshold else 0
    robot_pos[0] += forward_speed * math.cos(robot_angle)
    robot_pos[1] += forward_speed * math.sin(robot_angle)

    return robot_pos, robot_angle, True

# Function to display text on the screen
def display_text(text, pos, color=BLACK):
    font = pygame.font.Font(None, 24)
    text_surface = font.render(text, True, color)
    screen.blit(text_surface, pos)

# Main loop
running = True
while running:
    screen.fill(WHITE)  # Clear screen
    
    # Draw all saved trajectories (persistent)
    for traj in trajectories:
        if len(traj) > 1:
            pygame.draw.lines(screen, BLACK, False, traj, 1)  # Draw the path of each trajectory
    
    # Draw the current path the robot follows
    if len(current_path) > 1:
        pygame.draw.lines(screen, BLACK, False, current_path, 1)  # Draw the path the robot is currently following

    # Draw pure pursuit points and paths
    if len(pure_pursuit_points) > 1:
        for i in range(len(pure_pursuit_points) - 1):
            pygame.draw.line(screen, RED, pure_pursuit_points[i], pure_pursuit_points[i+1], 2)

    # Draw initial position and heading line
    if target_pos:
        pygame.draw.circle(screen, BLACK, initial_pos, 5)
        initial_end_pos = (
            initial_pos[0] + 30 * math.cos(initial_angle),
            initial_pos[1] + 30 * math.sin(initial_angle)
        )
        pygame.draw.line(screen, BLACK, initial_pos, initial_end_pos, 2)
    
    # Draw robot and its direction
    draw_robot(robot_pos, robot_angle)
    
    # Draw the target point
    if target_pos:
        pygame.draw.circle(screen, RED, target_pos, 5)
    
    # Display coordinates of the robot, target, and mouse cursor
    display_text(f"Robot: {robot_pos[0]:.1f}, {robot_pos[1]:.1f}", (10, 10))
    if target_pos:
        display_text(f"Target: {target_pos[0]:.1f}, {target_pos[1]:.1f}", (10, 40))

    # Get the current mouse position (cursor)
    mouse_pos = pygame.mouse.get_pos()
    display_text(f"Cursor: {mouse_pos[0]:.1f}, {mouse_pos[1]:.1f}", (10, 70))
    
    # Display instructions at the bottom of the screen
    display_text("Hold shift and click to enter pure pursuit points, press enter to run", (10, HEIGHT - 40))

    # Event handling
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if pygame.key.get_mods() & pygame.KMOD_SHIFT:  # Check if Shift is held
                pure_pursuit_points.append(pygame.mouse.get_pos())  # Add waypoint for Pure Pursuit
            else:
                if mouse_pos[1] < HEIGHT - slider_area_height:  # Check if the click is outside the slider area
                    if target_pos:
                        trajectories.append(current_path.copy())  # Save the path when the robot reaches the target
                    target_pos = pygame.mouse.get_pos()
                    is_moving = True
                    initial_pos = robot_pos.copy()
                    initial_angle = robot_angle
                    current_path = []  # Reset the path for the new target
        
        # Check for reset button click
        if reset_button.is_clicked(event):
            # Reset all necessary state variables
            trajectories.clear()  # Clear all trajectories
            pure_pursuit_points.clear()  # Clear all waypoints
            current_path.clear()  # Clear the current path
            target_pos = None  # Reset target position
            is_moving = False  # Stop any movement
            pure_pursuit_active = False  # Disable pure pursuit

        # Pass events to the sliders
        speed_slider.handle_event(event)
        turn_slider.handle_event(event)

        # Start Pure Pursuit after Enter key is pressed
        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            if pure_pursuit_points:
                pure_pursuit_active = True
    
    # Move robot using Pure Pursuit if waypoints are set and active
    if pure_pursuit_active and pure_pursuit_points:
        robot_pos, robot_angle, is_moving = pure_pursuit(robot_pos, pure_pursuit_points, lookahead_distance, robot_angle)
        if len(pure_pursuit_points) == 1 and math.sqrt((robot_pos[0] - pure_pursuit_points[0][0])**2 + (robot_pos[1] - pure_pursuit_points[0][1])**2) < final_point_tolerance:
            # Stop Pure Pursuit when the final point is reached
            pure_pursuit_active = False
            pure_pursuit_points.clear()  # Clear the Pure Pursuit points
            target_pos = None  # Clear regular target position to prevent returning
            current_path.clear()  # Clear the current path

    # Move robot towards the target using PID logic if not in Pure Pursuit mode
    if not pure_pursuit_active and is_moving and target_pos:
        reached_target, robot_angle = move_robot_with_pid(robot_pos, target_pos, robot_angle, speed_slider.value, turn_slider.value)
        current_path.append(robot_pos.copy())  # Append current position to path
        if reached_target:
            is_moving = False  # Stop moving when target is reached

    # Draw sliders
    speed_slider.draw(screen)
    turn_slider.draw(screen)

    # Draw reset button
    reset_button.draw(screen)

    # Update the display
    pygame.display.flip()
    
    # Frame rate
    pygame.time.Clock().tick(60)

# Quit Pygame
pygame.quit()
