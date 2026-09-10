#Import libraries
import pygame
import sys
import math
import json
try:
    # tkinter used only for file dialogs when uploading simulations
    import tkinter as tk
    from tkinter.filedialog import askopenfilename
    TK_AVAILABLE = True
except Exception:
    TK_AVAILABLE = False
from datetime import datetime

#Resolution and frame rate settings for the game window
WIDTH = 1280
HEIGHT = 720
FPS = 60

#Main function that, just just public static void main() in Java, serves as the entry point for the program. 
#Initializes the game, sets up the main loop, handles events & rendering for the different scenes
def main():
    #Initialized Pygame, prints as a test, creates game window, sets up clock for FPS and loads default font
    print("Hello, World!")
    pygame.init()
    screen = pygame.display.set_mode((WIDTH, HEIGHT))
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("arial", 32)

#Defines the buttons for the main menu, each with a label and a rectangle that defines its position and size on the screen.
    buttons = [
        {"label": "ARTEMIS Launch", "rect": pygame.Rect(440, 120, 400, 60)},
        {"label": "Orbital Insertion", "rect": pygame.Rect(440, 200, 400, 60)},
        {"label": "Slingshot", "rect": pygame.Rect(440, 280, 400, 60)},
        {"label": "Freeplay", "rect": pygame.Rect(440, 360, 400, 60)},
        {"label": "Upload Simulation", "rect": pygame.Rect(440, 440, 400, 60)},
    ]
    #These are all the variables that are used in the game, such as the active scene, the position and 
    # velocity of the spacecraft, the position and mass of the planet and moon, and other variables related to the game state.
    active_scene = "MAIN_MENU"
    craft_vx = 0
    craft_vy = 0
    mass = 100
    craft_x = WIDTH // 2
    craft_y = HEIGHT - HEIGHT // 4
    planet_x = WIDTH // 2
    planet_y = HEIGHT // 2
    planet_mass = 40000000
    planet_radius = 10
    moon_x = WIDTH // 2 + 300
    moon_y = HEIGHT // 2 - 100
    moon_mass = 5000000
    moon_radius = 6
    moon_orbit_radius = ((moon_x - planet_x) ** 2 + (moon_y - planet_y) ** 2) ** 0.5
    moon_angle = math.atan2(moon_y - planet_y, moon_x - planet_x)
    moon_rotation_speed = 0.6
    craft_radius = 3
    showRules = True
    duration = 0
    velocity_graph = []
    started = False
    moon_passed = False
    crashed_into_earth = False
    mission_over = False
    mission_success = False
    max_speed = 0
    fuel = 1000
    fuel_used = 0
    initial_launch_speed = 0.0
    stable_orbit_time = 0
    running = True
    out_of_bounds = False
    last_active_scene = "MAIN_MENU"
    #Initializes the main loop of the game, which continues until the user closes the window. 
    # It handles events, updates the game state, and renders the appropriate scene based on the active scene variable.
    while running:
        dt = clock.tick(FPS) / 1000.0
        for event in pygame.event.get():
            #Handles closing window and main menu button clicks
            if event.type == pygame.QUIT:
                running = False #if closed it will stop the running loop
            elif active_scene == "MAIN_MENU": #if the active scene is the main menu
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1: #on click of the left mouse button
                    for button in buttons: #for every button
                        if button["rect"].collidepoint(event.pos): #if the mouse click is within the button's rectangle
                            print(f"Selected mode: {button['label']}") #prints which mode is selected
                            # Special handling for upload
                            if button['label'] == "Upload Simulation":
                                if TK_AVAILABLE:
                                    try:
                                        root = tk.Tk()
                                        root.withdraw()
                                        file_path = askopenfilename(title='Select simulation JSON file', filetypes=[('JSON files','*.json'), ('All files','*.*')])
                                        root.destroy()
                                        if file_path:
                                            data = load_simulation(file_path)
                                            if data:
                                                # populate state from file
                                                active_scene = data.get('scene', 'Freeplay') if data.get('scene') in [b['label'] for b in buttons] else 'Freeplay'
                                                craft_x = data.get('craft_x', craft_x)
                                                craft_y = data.get('craft_y', craft_y)
                                                craft_vx = data.get('craft_vx', craft_vx)
                                                craft_vy = data.get('craft_vy', craft_vy)
                                                duration = data.get('duration', duration)
                                                velocity_graph = [(t, vx, vy) for t, vx, vy in data.get('velocity_graph', [])]
                                                fuel = data.get('fuel', fuel)
                                                fuel_used = data.get('fuel_used', fuel_used)
                                                max_speed = data.get('max_speed', max_speed)
                                                started = True
                                                showRules = False
                                    except Exception as e:
                                        print('Upload failed:', e)
                                else:
                                    print('tkinter not available; cannot open file dialog')
                            else:
                                active_scene = button['label'] #sets the active scene to the label of the clicked button
            #Allows the mode to progress to the next screen for artemis mode
            elif active_scene == "ARTEMIS Launch" and event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if not started:
                    started = True
                    showRules = False
                    mx, my = pygame.mouse.get_pos()
                    dx = mx - craft_x
                    dy = my - craft_y
                    dist = (dx * dx + dy * dy) ** 0.5
                    if dist > 0:
                        speed = dist * 0.4
                        craft_vx = (dx / dist) * speed
                        craft_vy = (dy / dist) * speed
                        initial_launch_speed = speed
                    else:
                        craft_vx = 0
                        craft_vy = 0
                        initial_launch_speed = 0.0
                elif mission_over:
                    last_active_scene = active_scene
                    active_scene = "SUCCESS_SCREEN"
                    save_mission_history("ARTEMIS Launch", "SUCCESS" if mission_success else "FAILURE", duration, max_speed, moon_passed, fuel_used)
            #Allows the mode to progress to the next screen for orbital insertion mode
            elif active_scene == "Orbital Insertion" and event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if not started:
                    started = True
                    showRules = False
                    stable_orbit_time = 0
                    mx, my = pygame.mouse.get_pos()
                    dx = mx - craft_x
                    dy = my - craft_y
                    dist = (dx * dx + dy * dy) ** 0.5
                    if dist > 0:
                        speed = dist * 0.35
                        craft_vx = (dx / dist) * speed
                        craft_vy = (dy / dist) * speed
                        initial_launch_speed = speed
                    else:
                        craft_vx = 0
                        craft_vy = 0
                        initial_launch_speed = 0.0
                elif mission_over:
                    last_active_scene = active_scene
                    active_scene = "SUCCESS_SCREEN"
                    save_mission_history("Orbital Insertion", "SUCCESS" if mission_success else "FAILURE", duration, max_speed, moon_passed, fuel_used)
            #Allows the mode to progress to the next screen for slingshot mode, and tracks whether the moon flyby was successful for the final stats screen
            elif active_scene == "Slingshot" and event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if not started:
                    started = True
                    showRules = False
                    moon_passed = False
                    mx, my = pygame.mouse.get_pos()
                    dx = mx - craft_x
                    dy = my - craft_y
                    dist = (dx * dx + dy * dy) ** 0.5
                    if dist > 0:
                        speed = dist * 0.38
                        craft_vx = (dx / dist) * speed
                        craft_vy = (dy / dist) * speed
                        initial_launch_speed = speed
                    else:
                        craft_vx = 0
                        craft_vy = 0
                        initial_launch_speed = 0.0
                elif mission_over:
                    last_active_scene = active_scene
                    active_scene = "SUCCESS_SCREEN"
                    save_mission_history("Slingshot", "SUCCESS" if mission_success else "FAILURE", duration, max_speed, moon_passed, fuel_used)
            #Allows the mode to progress to the next screen for freeplay mode
            elif active_scene == "Freeplay" and event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                if not started:
                    started = True
                    showRules = False
                    mx, my = pygame.mouse.get_pos()
                    dx = mx - craft_x
                    dy = my - craft_y
                    dist = (dx * dx + dy * dy) ** 0.5
                    if dist > 0:
                        speed = dist * 0.35
                        craft_vx = (dx / dist) * speed
                        craft_vy = (dy / dist) * speed
                        initial_launch_speed = speed
                    else:
                        craft_vx = 0
                        craft_vy = 0
                        initial_launch_speed = 0.0
                elif started:
                    last_active_scene = active_scene
                    active_scene = "SUCCESS_SCREEN"
                    save_mission_history("Freeplay", "EXPLORATION", duration, max_speed, moon_passed, fuel_used)
            #Allows player to return to main menu at the stats screen, resetting all the variables for a clean launch
            elif active_scene == "SUCCESS_SCREEN" and event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                active_scene = "MAIN_MENU"
                showRules = True
                started = False
                moon_passed = False
                crashed_into_earth = False
                mission_over = False
                mission_success = False
                duration = 0
                velocity_graph = []
                max_speed = 0
                fuel_used = 0
                fuel = 1000
                initial_launch_speed = 0.0
                stable_orbit_time = 0
                craft_vx = 0
                craft_vy = 0
                craft_x = WIDTH // 2
                craft_y = HEIGHT - HEIGHT // 4
        #Rotate the moon around Earth every frame, even before launch
        moon_angle += moon_rotation_speed * dt
        moon_x = planet_x + math.cos(moon_angle) * moon_orbit_radius
        moon_y = planet_y + math.sin(moon_angle) * moon_orbit_radius

        #Renders all the main menu buttons and text
        if(active_scene == "MAIN_MENU"): #if main menu
            screen.fill((10, 10, 30)) #color background
            title_surface = font.render("Artemis Aerospace Simulator", True, (255, 255, 255)) #renders the title text
            screen.blit(title_surface, (280, 80)) #displays the title text at the specified position
            for button in buttons: #for every button in the buttons list
                pygame.draw.rect(screen, (40, 90, 170), button["rect"], border_radius=8) #draws a rectangle for the button with the specified color and rounded corners
                label_surface = font.render(button["label"], True, (255, 255, 255)) #renders the button label text
                label_rect = label_surface.get_rect(center=button["rect"].center) #gets the rectangle of the label surface and centers it within the button's rectangle
                screen.blit(label_surface, label_rect) #displays the button label text on the screen at the calculated position

        #Renders the orbital insertion rules and background
        elif(active_scene == "Orbital Insertion"): #if the active scene is Orbital Insertion
            screen.fill((0, 0, 10)) #color background
            insertion_surface = font.render("Orbital Insertion Mode", True, (255, 255, 255))
            screen.blit(insertion_surface, (20, 20))
            if showRules:
                rules_surface = font.render("Space to launch the spacecraft! Hold UP arrow to raise orbit. Press D for stats info.", True, (255, 255, 255))
                screen.blit(rules_surface, (20, 120))

            #Draw the planet, moon, and orbit zone
            orbit_inner = planet_radius + 120
            orbit_outer = planet_radius + 180
            pygame.draw.circle(screen, (30, 30, 40), (int(planet_x), int(planet_y)), orbit_outer)
            pygame.draw.circle(screen, (0, 0, 10), (int(planet_x), int(planet_y)), orbit_inner)
            pygame.draw.circle(screen, (80, 80, 90), (int(planet_x), int(planet_y)), orbit_outer, 1)
            pygame.draw.circle(screen, (80, 80, 90), (int(planet_x), int(planet_y)), orbit_inner, 1)

            altitude = 0.0
            speed = 0.0

            #Allows user to launch the spacecraft by clicking space, and shows a line from the spacecraft to the mouse cursor indicating the direction and strength of the initial thrust.
            if not started:
                mx, my = pygame.mouse.get_pos()
                dx = mx - craft_x
                dy = my - craft_y
                dist = (dx * dx + dy * dy) ** 0.5
                predicted_speed = min(dist * 0.3, 150)
                color_intensity = int(min(predicted_speed / 50.0, 1.0) * 255)
                line_color = (color_intensity, 255 - color_intensity // 2, 0)
                pygame.draw.line(screen, line_color, (craft_x, craft_y), pygame.mouse.get_pos(), 2)
            #Once the simulation has started, it checks for out of bounds conditions
            elif not mission_over:
                if out_of_bounds:
                    if 0 < craft_x < WIDTH and 0 < craft_y < HEIGHT and not active_scene == "Slingshot":
                        out_of_bounds = False
                    restart_label = "Out of bounds! Press SPACE to return to the main menu."
                    screen.blit(font.render(restart_label, True, (255, 255, 255)), (20, HEIGHT*0.9))
                    keys_pressed = pygame.key.get_pressed()
                    #Let the user press space to reset all the variables and set the scene to Main Menu
                    if keys_pressed[pygame.K_SPACE]:
                        active_scene = "MAIN_MENU"
                        showRules = True
                        started = False
                        moon_passed = False
                        crashed_into_earth = False
                        mission_over = False
                        mission_success = False
                        duration = 0
                        velocity_graph = []
                        max_speed = 0
                        fuel_used = 0
                        fuel = 1000
                        initial_launch_speed = 0.0
                        stable_orbit_time = 0
                        craft_vx = 0
                        craft_vy = 0
                        craft_x = WIDTH // 2
                        craft_y = HEIGHT - HEIGHT // 4
                        out_of_bounds = False
                #Up arrow for thrust, consuming fuel or regenerating it
                keys_pressed = pygame.key.get_pressed()
                if keys_pressed[pygame.K_UP] and started:
                    if fuel > 4:
                        thrust_vx, thrust_vy = calculate_thrust(craft_x, craft_y, *pygame.mouse.get_pos(), 150, mass)
                        craft_vx += thrust_vx
                        craft_vy += thrust_vy
                        fuel -= 4
                        fuel_used += 4
                else:
                    fuel += 1
                    fuel = min(fuel, 1000)
                #show fuel bar
                fuel_bar_width = 200
                fuel_bar_height = 20
                fuel_ratio = fuel / 1000
                pygame.draw.rect(screen, (50, 50, 50), (20, 60, fuel_bar_width, fuel_bar_height))
                pygame.draw.rect(screen, (0, 200, 255), (20, 60, fuel_bar_width * fuel_ratio, fuel_bar_height))

                #Calculate physics for objects and update velocity and position using Euler-Cromer method
                ax1, ay1 = calculate_physics(craft_x, craft_y, planet_x, planet_y, planet_mass)
                craft_vx += ax1 * dt
                craft_vy += ay1 * dt
                craft_x += craft_vx * dt
                craft_y += craft_vy * dt

                #Update velocity graph and track maximum speed
                duration += dt
                velocity_graph.append((duration, craft_vx, craft_vy))
                speed = (craft_vx ** 2 + craft_vy ** 2) ** 0.5
                max_speed = max(max_speed, speed)

                #Check whether planet is meeting the conditions for orbit
                distance = ((craft_x - planet_x) ** 2 + (craft_y - planet_y) ** 2) ** 0.5
                altitude = distance - planet_radius
                radial_velocity = ((craft_x - planet_x) * craft_vx + (craft_y - planet_y) * craft_vy) / distance if distance > 0 else 0.0

                #Update the time spent in the orbit zone
                if 120 < altitude < 180 and abs(radial_velocity) < 30:
                    stable_orbit_time += dt*0.2
                else:
                    stable_orbit_time = max(0, stable_orbit_time - dt * 0.5)

                #Check for successful orbit condition (3 seconds in the stable orbit zone)
                if stable_orbit_time >= 3.0:
                    mission_over = True
                    mission_success = True

                #Check for moon flyby and Earth crash conditions
                if distance < planet_radius + craft_radius:
                    mission_over = True
                    mission_success = False
                if craft_y < 0 or craft_x < 0 or craft_x > WIDTH or craft_y > HEIGHT:
                    out_of_bounds = True
            else:
                pass

            #Draw the planet, moon, and spacecraft
            pygame.draw.circle(screen, (100, 150, 255), (int(planet_x), int(planet_y)), planet_radius)
            pygame.draw.circle(screen, (200, 200, 200), (int(moon_x), int(moon_y)), moon_radius)
            pygame.draw.circle(screen, (255, 255, 255), (int(craft_x), int(craft_y)), craft_radius)

            #Stats mode display the stats *which everyone should press because its cool* 
            #Displays lines for force vectors and mouse thrust, and numerical newton values for the forces when 'D' is held down
            keys_pressed = pygame.key.get_pressed()
            if keys_pressed[pygame.K_d] and started and not mission_over:
                debug_ax1, debug_ay1 = calculate_physics(craft_x, craft_y, planet_x, planet_y, planet_mass)
                debug_ax2, debug_ay2 = calculate_physics(craft_x, craft_y, moon_x, moon_y, moon_mass)
                debug_force_earth = (debug_ax1**2 + debug_ay1**2) ** 0.5
                debug_force_moon = (debug_ax2**2 + debug_ay2**2) ** 0.5
                mx, my = pygame.mouse.get_pos()
                pygame.draw.line(screen, (100, 150, 255), (int(craft_x), int(craft_y)), (int(planet_x), int(planet_y)), 2)
                earth_text = f"Earth Force: {debug_force_earth:.3f} N"
                screen.blit(font.render(earth_text, True, (100, 150, 255)), (int((craft_x + planet_x) / 2), int((craft_y + planet_y) / 2)))
                pygame.draw.line(screen, (200, 200, 200), (int(craft_x), int(craft_y)), (int(moon_x), int(moon_y)), 2)
                moon_text = f"Moon Force: {debug_force_moon:.3f} N"
                screen.blit(font.render(moon_text, True, (200, 200, 200)), (int((craft_x + moon_x) / 2), int((craft_y + moon_y) / 2)))
                pygame.draw.line(screen, (255, 255, 0), (int(craft_x), int(craft_y)), (mx, my), 2)
                mouse_label = "Mouse Direction"
                screen.blit(font.render(mouse_label, True, (255, 255, 0)), (int((craft_x + mx) / 2), int((craft_y + my) / 2)))
                if keys_pressed[pygame.K_UP] and fuel > 4:
                    thrust_vx, thrust_vy = calculate_thrust(craft_x, craft_y, mx, my, 150, mass)
                    thrust_force = (thrust_vx**2 + thrust_vy**2) ** 0.5 * mass
                    thrust_text = f"Thrust Force: {thrust_force:.3f} N"
                    screen.blit(font.render(thrust_text, True, (255, 255, 0)), (int((craft_x + mx) / 2), int((craft_y + my) / 2) + 20))
                screen.blit(font.render("STATS MODE [D]", True, (255, 0, 0)), (WIDTH - 300, 20))

            #render the text for the altitude, speed, orbit stability time, and target band for the orbit insertion mode
            screen.blit(font.render(f"Altitude: {altitude:.1f}", True, (255, 255, 255)), (20, 160))
            screen.blit(font.render(f"Speed: {speed:.1f}", True, (255, 255, 255)), (20, 200))
            screen.blit(font.render(f"Orbit stability: {stable_orbit_time:.1f}/3.0", True, (255, 255, 255)), (20, 240))
            screen.blit(font.render("Target band: 120-180 px", True, (255, 255, 255)), (20, 280))

            if mission_over:
                result_text = "Orbit achieved! Press SPACE for final stats" if mission_success else "Mission failed. Press SPACE for final stats"
                screen.blit(font.render(result_text, True, (255, 200, 50)), (20, 120))

        #Slingshot active scene
        elif(active_scene == "Slingshot"): #if the active scene is Slingshot
            screen.fill((0, 10, 20)) #color background
            slingshot_surface = font.render("Slingshot Mode", True, (255, 255, 255))
            screen.blit(slingshot_surface, (20, 20))
            if showRules:
                rules_surface = font.render("Space to launch and use moon gravity to escape. Press D for stats.", True, (255, 255, 255))
                screen.blit(rules_surface, (20, 120))

            #Draw line of thrust launch along with color for strength
            if not started:
                mx, my = pygame.mouse.get_pos()
                dx = mx - craft_x
                dy = my - craft_y
                dist = (dx * dx + dy * dy) ** 0.5
                predicted_speed = min(dist * 0.3, 150)
                color_intensity = int(min(predicted_speed / 50.0, 1.0) * 255)
                line_color = (color_intensity, 255 - color_intensity // 2, 0)
                pygame.draw.line(screen, line_color, (craft_x, craft_y), (mx, my), 2)

                #Calc the thrust force
            elif not mission_over:

                ax1, ay1 = calculate_physics(craft_x, craft_y, planet_x, planet_y, planet_mass)
                ax2, ay2 = calculate_physics(craft_x, craft_y, moon_x, moon_y, moon_mass)
                craft_vx += (ax1 + ax2) * dt
                craft_vy += (ay1 + ay2) * dt
                craft_x += craft_vx * dt
                craft_y += craft_vy * dt

                #Add to the graph array
                duration += dt
                velocity_graph.append((duration, craft_vx, craft_vy))
                speed = (craft_vx ** 2 + craft_vy ** 2) ** 0.5
                max_speed = max(max_speed, speed)
                screen.blit(font.render(f"Velocity: {speed:.1f} px/s", True, (255, 255, 255)), (20, 160))

                #Check if moon flyby
                moon_distance = ((craft_x - moon_x) ** 2 + (craft_y - moon_y) ** 2) ** 0.5
                if moon_distance < moon_radius + 50:
                    moon_passed = True

                #Check for Earth crash or out of bounds conditions
                planet_distance = ((craft_x - planet_x) ** 2 + (craft_y - planet_y) ** 2) ** 0.5
                if planet_distance < planet_radius + craft_radius:
                    mission_over = True
                    mission_success = False
                elif (craft_x > WIDTH or craft_y < 0 or craft_y > HEIGHT or craft_x < 0) and speed > initial_launch_speed:
                    mission_over = True
                    mission_success = True
                elif craft_y < 0 or craft_x < 0 or craft_y > HEIGHT or craft_x > WIDTH:
                    out_of_bounds = True
                    mission_over = True
                    mission_success = False

            #Draw the planet, moon, and spacecraft
            pygame.draw.circle(screen, (100, 150, 255), (int(planet_x), int(planet_y)), planet_radius)
            pygame.draw.circle(screen, (200, 200, 200), (int(moon_x), int(moon_y)), moon_radius)
            pygame.draw.circle(screen, (255, 255, 255), (int(craft_x), int(craft_y)), craft_radius)
            pygame.draw.circle(screen, (180, 180, 180), (int(moon_x), int(moon_y)), moon_radius + 50, 1)

            #keys pressed input
            keys_pressed = pygame.key.get_pressed()
            #Debug mode: Hold 'D' to show forces and directional lines
            if keys_pressed[pygame.K_d] and started and not mission_over:
                debug_ax1, debug_ay1 = calculate_physics(craft_x, craft_y, planet_x, planet_y, planet_mass)
                debug_ax2, debug_ay2 = calculate_physics(craft_x, craft_y, moon_x, moon_y, moon_mass)
                debug_force_earth = (debug_ax1**2 + debug_ay1**2) ** 0.5
                debug_force_moon = (debug_ax2**2 + debug_ay2**2) ** 0.5
                mx, my = pygame.mouse.get_pos()
                pygame.draw.line(screen, (100, 150, 255), (int(craft_x), int(craft_y)), (int(planet_x), int(planet_y)), 2)
                earth_text = f"Earth Force: {debug_force_earth:.3f} N"
                screen.blit(font.render(earth_text, True, (100, 150, 255)), (int((craft_x + planet_x) / 2), int((craft_y + planet_y) / 2)))
                pygame.draw.line(screen, (200, 200, 200), (int(craft_x), int(craft_y)), (int(moon_x), int(moon_y)), 2)
                moon_text = f"Moon Force: {debug_force_moon:.3f} N"
                screen.blit(font.render(moon_text, True, (200, 200, 200)), (int((craft_x + moon_x) / 2), int((craft_y + moon_y) / 2)))
                pygame.draw.line(screen, (255, 255, 0), (int(craft_x), int(craft_y)), (mx, my), 2)
                mouse_label = "Mouse Direction"
                screen.blit(font.render(mouse_label, True, (255, 255, 0)), (int((craft_x + mx) / 2), int((craft_y + my) / 2)))
                screen.blit(font.render("STATS MODE [D]", True, (255, 0, 0)), (WIDTH - 300, 20))

            #Render the text for mission end
            if mission_over:
                result_text = "Slingshot achieved! Press SPACE for final stats" if mission_success else "Mission failed. Press SPACE for final stats"
                screen.blit(font.render(result_text, True, (255, 200, 50)), (20, 120))

        #Artemis launch scene
        elif(active_scene == "ARTEMIS Launch"): #if the active scene is ARTEMIS Launch
            screen.fill((0, 0, 0)) #color background
            launch_surface = font.render("ARTEMIS Launch Mode", True, (255, 255, 255)) #renders the text for ARTEMIS Launch mode
            screen.blit(launch_surface, (20, 20)) #displays the ARTEMIS Launch mode text at the specified position
            if showRules: #if the rules should be shown
                rules_surface = font.render("Space to launch the spacecraft! Hold UP arrow to thrust. Press D for stats info.", True, (255, 255, 255)) #renders the rules text
                screen.blit(rules_surface, (20, 120)) #displays the rules text at the specified position
        
            #Allow user to pick first velocity
            if not started:
                mx, my = pygame.mouse.get_pos()
                dx = mx - craft_x
                dy = my - craft_y
                dist = (dx * dx + dy * dy) ** 0.5
                predicted_speed = min(dist * 0.3, 150)
                color_intensity = int(min(predicted_speed / 50.0, 1.0) * 255)
                line_color = (color_intensity, 255 - color_intensity // 2, 0)
                pygame.draw.line(screen, line_color, (craft_x, craft_y), pygame.mouse.get_pos(), 2)

            #Check for of out bounds and reset if user pressed space
            elif not mission_over:
                if out_of_bounds:
                    if craft_y > 0 and craft_x > 0 and craft_x < WIDTH and craft_y < HEIGHT:
                        out_of_bounds = False
                    restart_label = "Out of bounds! Press SPACE to return to the main menu."
                    screen.blit(font.render(restart_label, True, (255, 255, 255)), (20, HEIGHT*0.9))
                    keys_pressed = pygame.key.get_pressed()
                    if keys_pressed[pygame.K_SPACE]:
                        active_scene = "MAIN_MENU"
                        showRules = True
                        started = False
                        moon_passed = False
                        crashed_into_earth = False
                        mission_over = False
                        mission_success = False
                        duration = 0
                        velocity_graph = []
                        max_speed = 0
                        fuel_used = 0
                        fuel = 1000
                        initial_launch_speed = 0.0
                        stable_orbit_time = 0
                        craft_vx = 0
                        craft_vy = 0
                        craft_x = WIDTH // 2
                        craft_y = HEIGHT - HEIGHT // 4
                        out_of_bounds = False

                #Fuel and thrust mechanics, with fuel regeneration when not thrusting
                keys_pressed = pygame.key.get_pressed()
                if keys_pressed[pygame.K_UP] and started:
                    if fuel > 4:
                        thrust_vx, thrust_vy = calculate_thrust(craft_x, craft_y, *pygame.mouse.get_pos(), 150, mass)
                        craft_vx += thrust_vx
                        craft_vy += thrust_vy
                        fuel -= 4
                        fuel_used += 4
                else:
                    fuel+=1
                    fuel = min(fuel, 1000)
                #show fuel bar
                fuel_bar_width = 200
                fuel_bar_height = 20
                fuel_ratio = fuel / 1000
                pygame.draw.rect(screen, (50, 50, 50), (20, 60, fuel_bar_width, fuel_bar_height))
                pygame.draw.rect(screen, (0, 200, 255), (20, 60, fuel_bar_width * fuel_ratio, fuel_bar_height))
                ax1, ay1 = calculate_physics(craft_x, craft_y, planet_x, planet_y, planet_mass)
                ax2, ay2 = calculate_physics(craft_x, craft_y, moon_x, moon_y, moon_mass)
                craft_vx += (ax1 + ax2) * dt
                craft_vy += (ay1 + ay2) * dt
                craft_x += craft_vx * dt
                craft_y += craft_vy * dt
                duration += dt
                velocity_graph.append((duration, craft_vx, craft_vy))
                speed = (craft_vx**2 + craft_vy**2) ** 0.5
                max_speed = max(max_speed, speed)
                screen.blit(font.render(f"Velocity: {speed:.1f} px/s", True, (255, 255, 255)), (20, 160))

                #moon & earth collision
                moon_distance = ((craft_x - moon_x) ** 2 + (craft_y - moon_y) ** 2) ** 0.5
                if moon_distance < moon_radius + 40:
                    moon_passed = True

                earth_distance = ((craft_x - planet_x) ** 2 + (craft_y - planet_y) ** 2) ** 0.5
                if earth_distance < planet_radius + craft_radius:
                    mission_over = True
                    crashed_into_earth = True
                    mission_success = moon_passed
                if craft_y < 0 or craft_x < 0 or craft_x > WIDTH or craft_y > HEIGHT:
                    out_of_bounds = True
            else:
                pass

            #Draw the planet, moon, and spacecraft
            pygame.draw.circle(screen, (100, 150, 255), (int(planet_x), int(planet_y)), planet_radius)
            pygame.draw.circle(screen, (200, 200, 200), (int(moon_x), int(moon_y)), moon_radius)
            pygame.draw.circle(screen, (255, 255, 255), (int(craft_x), int(craft_y)), craft_radius)

            status_text = "Moon flyby: YES" if moon_passed else "Moon flyby: NO"
            screen.blit(font.render(status_text, True, (255, 255, 255)), (20, 80))
            
            # Debug mode: Hold 'D' to show forces and directional lines
            keys_pressed = pygame.key.get_pressed()
            if keys_pressed[pygame.K_d] and started and not mission_over:
                # Compute forces for debug display
                debug_ax1, debug_ay1 = calculate_physics(craft_x, craft_y, planet_x, planet_y, planet_mass)
                debug_ax2, debug_ay2 = calculate_physics(craft_x, craft_y, moon_x, moon_y, moon_mass)
                debug_force_earth = (debug_ax1**2 + debug_ay1**2) ** 0.5
                debug_force_moon = (debug_ax2**2 + debug_ay2**2) ** 0.5
                
                # Line to Earth (blue)
                pygame.draw.line(screen, (100, 150, 255), (int(craft_x), int(craft_y)), (int(planet_x), int(planet_y)), 2)
                earth_text = f"Earth Force: {debug_force_earth:.3f}"+"N"
                screen.blit(font.render(earth_text, True, (100, 150, 255)), (int((craft_x + planet_x) / 2), int((craft_y + planet_y) / 2)))
                
                # Line to Moon (gray)
                pygame.draw.line(screen, (200, 200, 200), (int(craft_x), int(craft_y)), (int(moon_x), int(moon_y)), 2)
                moon_text = f"Moon Force: {debug_force_moon:.3f}"+"N"
                screen.blit(font.render(moon_text, True, (200, 200, 200)), (int((craft_x + moon_x) / 2), int((craft_y + moon_y) / 2)))
                
                # Line to Mouse (yellow)
                mx, my = pygame.mouse.get_pos()
                thrust_text = ""
                if keys_pressed[pygame.K_UP] and started:
                    thrust_vx, thrust_vy = calculate_thrust(craft_x, craft_y, mx, my, 150, mass)
                    thrust_force = (thrust_vx**2 + thrust_vy**2) ** 0.5 * mass
                    thrust_text = f"Thrust Force: {thrust_force:.3f}" + "N"
                    screen.blit(font.render(thrust_text, True, (255, 255, 0)), (int((craft_x + mx) / 2), int((craft_y + my) / 2) + 20))
                pygame.draw.line(screen, (255, 255, 0), (int(craft_x), int(craft_y)), (mx, my), 2)
                mouse_label = "Mouse Direction"
                screen.blit(font.render(mouse_label, True, (255, 255, 0)), (int((craft_x + mx) / 2), int((craft_y + my) / 2)))
                
                # Debug mode indicator
                screen.blit(font.render("STATS MODE [D]", True, (255, 0, 0)), (WIDTH - 300, 20))
            
            # Display altitude and speed
            if mission_over:
                result_text = "Mission success! Press SPACE for final stats" if mission_success else "Mission failed. Press SPACE for final stats"
                screen.blit(font.render(result_text, True, (255, 200, 50)), (20, 120))

        #Freeplay mode: free exploration with Earth and Moon, no mission goals
        elif(active_scene == "Freeplay"):
            screen.fill((0, 0, 10))
            freeplay_surface = font.render("Freeplay Mode", True, (255, 255, 255))
            screen.blit(freeplay_surface, (20, 20))
            if showRules:
                rules_surface = font.render("Space to launch! Hold UP arrow to boost. Press D for velocity direction. Press SPACE again to end.", True, (255, 255, 255))
                screen.blit(rules_surface, (20, 80))
            out_of_bounds_freeplay = False
            #Allow user to pick first velocity with mouse and show line for direction and strength
            if not started:
                mx, my = pygame.mouse.get_pos()
                dx = mx - craft_x
                dy = my - craft_y
                dist = (dx * dx + dy * dy) ** 0.5
                predicted_speed = min(dist * 0.35, 150)
                color_intensity = int(min(predicted_speed / 50.0, 1.0) * 255)
                line_color = (color_intensity, 255 - color_intensity // 2, 0)
                pygame.draw.line(screen, line_color, (craft_x, craft_y), pygame.mouse.get_pos(), 2)
            elif started:
                # Fuel and thrust mechanics, with fuel regeneration when not thrusting
                keys_pressed = pygame.key.get_pressed()
                if keys_pressed[pygame.K_UP] and started:
                    if fuel > 4:
                        thrust_vx, thrust_vy = calculate_thrust(craft_x, craft_y, *pygame.mouse.get_pos(), 150, mass)
                        craft_vx += thrust_vx
                        craft_vy += thrust_vy
                        fuel -= 4
                        fuel_used += 4
                else:
                    fuel+=1
                    fuel = min(fuel, 1000)
                #show fuel bar
                fuel_bar_width = 200
                fuel_bar_height = 20
                fuel_ratio = fuel / 1000
                pygame.draw.rect(screen, (50, 50, 50), (20, 60, fuel_bar_width, fuel_bar_height))
                pygame.draw.rect(screen, (0, 200, 255), (20, 60, fuel_bar_width * fuel_ratio, fuel_bar_height))
                
                # Physics simulation
                ax1, ay1 = calculate_physics(craft_x, craft_y, planet_x, planet_y, planet_mass)
                ax2, ay2 = calculate_physics(craft_x, craft_y, moon_x, moon_y, moon_mass)
                craft_vx += (ax1 + ax2) * dt
                craft_vy += (ay1 + ay2) * dt
                craft_x += craft_vx * dt
                craft_y += craft_vy * dt
                duration += dt
                velocity_graph.append((duration, craft_vx, craft_vy))
                speed = (craft_vx**2 + craft_vy**2) ** 0.5
                max_speed = max(max_speed, speed)
                screen.blit(font.render(f"Velocity: {speed:.1f} px/s", True, (255, 255, 255)), (20, 160))
                screen.blit(font.render(f"Duration: {duration:.1f} s", True, (255, 255, 255)), (20, 200))

                # Check if out of bounds but don't reset
                if craft_y < 0 or craft_x < 0 or craft_x > WIDTH or craft_y > HEIGHT:
                    out_of_bounds_freeplay = True

            # Draw the planet and moon
            pygame.draw.circle(screen, (100, 150, 255), (int(planet_x), int(planet_y)), planet_radius)
            pygame.draw.circle(screen, (200, 200, 200), (int(moon_x), int(moon_y)), moon_radius)
            pygame.draw.circle(screen, (255, 255, 255), (int(craft_x), int(craft_y)), craft_radius)

            # Draw Moon orbit reference
            pygame.draw.circle(screen, (50, 50, 80), (int(planet_x), int(planet_y)), int(moon_orbit_radius), 1)

            # Debug mode with velocity direction arrow
            keys_pressed = pygame.key.get_pressed()
            if keys_pressed[pygame.K_d] and started:
                # Compute forces for debug display
                debug_ax1, debug_ay1 = calculate_physics(craft_x, craft_y, planet_x, planet_y, planet_mass)
                debug_ax2, debug_ay2 = calculate_physics(craft_x, craft_y, moon_x, moon_y, moon_mass)
                debug_force_earth = (debug_ax1**2 + debug_ay1**2) ** 0.5
                debug_force_moon = (debug_ax2**2 + debug_ay2**2) ** 0.5
                
                # Line to Earth (blue)
                pygame.draw.line(screen, (100, 150, 255), (int(craft_x), int(craft_y)), (int(planet_x), int(planet_y)), 2)
                earth_text = f"Earth Force: {debug_force_earth:.3f}" + "N"
                screen.blit(font.render(earth_text, True, (100, 150, 255)), (int((craft_x + planet_x) / 2), int((craft_y + planet_y) / 2)))
                
                # Line to Moon (gray)
                pygame.draw.line(screen, (200, 200, 200), (int(craft_x), int(craft_y)), (int(moon_x), int(moon_y)), 2)
                moon_text = f"Moon Force: {debug_force_moon:.3f}" + "N"
                screen.blit(font.render(moon_text, True, (200, 200, 200)), (int((craft_x + moon_x) / 2), int((craft_y + moon_y) / 2)))
                
                # Velocity direction arrow (green)
                v_mag = (craft_vx**2 + craft_vy**2) ** 0.5
                if v_mag > 0.1:
                    # Normalize velocity and scale for visibility
                    arrow_length = 80
                    arrow_x = craft_x + (craft_vx / v_mag) * arrow_length
                    arrow_y = craft_y + (craft_vy / v_mag) * arrow_length
                    
                    # Draw main arrow line (green)
                    pygame.draw.line(screen, (100, 255, 100), (int(craft_x), int(craft_y)), (int(arrow_x), int(arrow_y)), 3)
                    
                    # Draw arrowhead
                    arrow_angle = math.atan2(craft_vy, craft_vx)
                    arrowhead_length = 15
                    arrow_left_x = arrow_x - arrowhead_length * math.cos(arrow_angle - 0.4)
                    arrow_left_y = arrow_y - arrowhead_length * math.sin(arrow_angle - 0.4)
                    arrow_right_x = arrow_x - arrowhead_length * math.cos(arrow_angle + 0.4)
                    arrow_right_y = arrow_y - arrowhead_length * math.sin(arrow_angle + 0.4)
                    
                    pygame.draw.line(screen, (100, 255, 100), (int(arrow_x), int(arrow_y)), (int(arrow_left_x), int(arrow_left_y)), 3)
                    pygame.draw.line(screen, (100, 255, 100), (int(arrow_x), int(arrow_y)), (int(arrow_right_x), int(arrow_right_y)), 3)
                    
                    screen.blit(font.render(f"Velocity: {v_mag:.1f} px/s", True, (100, 255, 100)), (int(arrow_x + 10), int(arrow_y - 20)))
                
                # Debug mode indicator
                screen.blit(font.render("VELOCITY DIRECTION [D]", True, (100, 255, 100)), (WIDTH - 400, 20))

            if out_of_bounds_freeplay:
                screen.blit(font.render("Out of bounds! Press SPACE to end exploration.", True, (255, 100, 100)), (20, HEIGHT - 60))
            else:
                screen.blit(font.render("Press SPACE to end exploration", True, (200, 200, 200)), (20, HEIGHT - 60))

        #When the mission is over, it displays a summary screen with the mission results, including whether the mission was a success or failure, the duration of the flight, the maximum speed achieved, fuel used, and whether the moon flyby was successful. It also prompts the user to press SPACE to return to the main menu.
        elif active_scene == "SUCCESS_SCREEN":
            screen.fill((0, 0, 0))
            
            # Draw velocity graph on the left
            if velocity_graph:
                graph_x, graph_y = 20, 100
                graph_width, graph_height = 300, 200
                
                # Calculate velocity magnitudes
                velocities = [(t, (vx**2 + vy**2)**0.5) for t, vx, vy in velocity_graph]
                max_vel = max([v for _, v in velocities]) if velocities else 1
                max_time = max([t for t, _ in velocities]) if velocities else 1
                
                # Draw graph frame
                pygame.draw.rect(screen, (50, 50, 50), (graph_x, graph_y, graph_width, graph_height), 2)
                
                # Draw velocity points as a line
                for i in range(len(velocities) - 1):
                    t1, v1 = velocities[i]
                    t2, v2 = velocities[i + 1]
                    
                    x1 = graph_x + (t1 / max_time) * graph_width if max_time > 0 else graph_x
                    y1 = graph_y + graph_height - (v1 / max_vel) * graph_height if max_vel > 0 else graph_y + graph_height
                    x2 = graph_x + (t2 / max_time) * graph_width if max_time > 0 else graph_x
                    y2 = graph_y + graph_height - (v2 / max_vel) * graph_height if max_vel > 0 else graph_y + graph_height
                    
                    pygame.draw.line(screen, (0, 200, 255), (int(x1), int(y1)), (int(x2), int(y2)), 2)
                
                # Draw graph labels
                screen.blit(font.render("Velocity (px/s)", True, (200, 200, 200)), (graph_x, graph_y - 30))
                screen.blit(font.render(f"Max: {max_vel:.1f}", True, (100, 200, 100)), (graph_x, graph_y + graph_height + 10))
                screen.blit(font.render(f"Time: {max_time:.1f}s", True, (100, 200, 100)), (graph_x + graph_width - 100, graph_y + graph_height + 10))
            
            # Display mission summary on the right
            if last_active_scene == "Freeplay":
                title_surface = font.render("Exploration Summary", True, (255, 255, 255))
                screen.blit(title_surface, (600, 20))
                duration_y = 80
            else:
                title_surface = font.render("Mission Summary", True, (255, 255, 255))
                screen.blit(title_surface, (600, 20))
                status_surface = font.render("Status: " + ("SUCCESS" if mission_success else "FAILURE"), True, (255, 255, 255))
                screen.blit(status_surface, (600, 80))
                duration_y = 140
            
            screen.blit(font.render(f"Duration: {duration:.2f} sec", True, (255, 255, 255)), (600, duration_y))
            screen.blit(font.render(f"Top speed: {max_speed:.2f} px/s", True, (255, 255, 255)), (600, duration_y + 60))
            screen.blit(font.render(f"Fuel used: {fuel_used} / 1000", True, (255, 255, 255)), (600, duration_y + 120))
            screen.blit(font.render(f"Moon flyby: {'Yes' if moon_passed else 'No'}", True, (255, 255, 255)), (600, duration_y + 180))
            screen.blit(font.render("Press SPACE to return to the main menu", True, (200, 200, 200)), (600, duration_y + 240))
            if mission_success:
                screen.blit(font.render("Congratulations! Final stats saved.", True, (100, 255, 100)), (600, duration_y + 280))
            else:
                screen.blit(font.render("Mission data saved. Try again.", True, (255, 100, 100)), (600, duration_y + 280))

        pygame.display.flip()#new frame

    pygame.quit()
    sys.exit()
#Purpose:
# Calculates the gravitational force exerted by a specific planet on the spacecraft and updates the vehicle's velocity and position using Euler-Cromer.
#Parameters:
# craft_x, craft_y (float): Current 2D positions of the spacecraft.
# craft_vx, craft_vy (float): Current 2D velocity vectors of the spacecraft.
# planet_x, planet_y (float): Fixed 2D coordinates of the target celestial body.
# planet_mass (float): Mass of the target planet (used for G-force calculation).
#Returns:
# tuple: (force_x, force_y) updated tracking parameters.
def calculate_physics(craft_x, craft_y, planet_x, planet_y, planet_mass):
    G = 0.08
    dx = planet_x - craft_x
    dy = planet_y - craft_y
    distance_squared = dx**2 + dy**2
    if distance_squared < 100:
        return 0, 0
    distance = distance_squared ** 0.5
    force_magnitude = G * planet_mass / distance_squared
    force_x = force_magnitude * (dx / distance)
    force_y = force_magnitude * (dy / distance)
    return force_x, force_y
#Purpose:
# Accepts a file path to a JSON configuration file, parses its contents, 
# validates the dictionary structure, and normalizes the tracking velocity graph.
#Parameters:
# file_path (str): The local system path to the target simulation configuration file.
#Returns:
# dict: A validated state dictionary containing craft configuration, or None if the load fails.
def load_simulation(file_path):
    """Load simulation state from a JSON file.
    Expected keys: scene, craft_x, craft_y, craft_vx, craft_vy, duration, velocity_graph (list of [t,vx,vy]), fuel, fuel_used, max_speed
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        # Basic validation
        if not isinstance(data, dict):
            print('Invalid simulation format: root must be object')
            return None
        # Normalize velocity_graph
        vg = data.get('velocity_graph', [])
        new_vg = []
        for item in vg:
            if isinstance(item, (list, tuple)) and len(item) >= 3:
                t, vx, vy = item[0], item[1], item[2]
                new_vg.append((float(t), float(vx), float(vy)))
        data['velocity_graph'] = new_vg
        return data
    except Exception as e:
        print('Failed to load simulation:', e)
        return None
#Purpose: 
# Accepts mission performance variables, formats them into a single standardized string, and appends the record to an external text log file
#Pre/Parameters:
# file_path (str): The destination file name (e.g., "mission_history.txt")
# mode_name (str): The name of the completed simulation mode.
# duration (float): Total flight time elapsed in seconds.
# peak_speed (float): The highest velocity magnitude recorded during flight.
# final_speed (float): The velocity magnitude at the moment of termination.
# success_status (str): Outcome label (e.g., "SUCCESS" or "CRASHED") 
#Returns: 
# bool: True if the file write operation was successful, False otherwise. 
def save_mission_history(mode, status, duration, max_speed, moon_passed, fuel_used):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"{timestamp}, {mode}, {status}, duration={duration:.2f}, max_speed={max_speed:.2f}, fuel_used={fuel_used}, moon_flyby={moon_passed}\n"
    with open("mission_history.txt", "a", encoding="utf-8") as file:
        file.write(line)
#Purpose: 
# Checks keyboard listeners for booster activation (spacebar) and splits engine 
# thrust into accurate X and Y acceleration vectors using trigonometry.
#Parameters:
# craft_vx, craft_vy (float): Pre-existing velocity component vectors.
# mouse_x, mouse_y (float): Current mouse position to calculate direction.
# thrust_power (float): Total engine strength capacity in Newtons.
# mass (float): Current structural weight profile of the vehicle.
#Returns:
# tuple: (updated_vx, updated_vy) new components after active throttle modification.
def calculate_thrust(craft_x, craft_y, mouse_x, mouse_y, thrust_power, mass):
    dx = mouse_x - craft_x
    dy = mouse_y - craft_y
    dist = (dx * dx + dy * dy) ** 0.5
    if dist > 0:
        thrust_vx = (dx / dist) * thrust_power / mass
        thrust_vy = (dy / dist) * thrust_power / mass
        return thrust_vx, thrust_vy
    return 0, 0

if __name__ == "__main__":
    main()