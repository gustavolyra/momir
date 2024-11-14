import wifi
import adafruit_requests
import socketpool
import board
import busio
import time
import digitalio
import ssl  # For handling SSL connections
from adafruit_ssd1306 import SSD1306_I2C
import adafruit_thermal_printer
import wifi_secrets 

# Define your Wi-Fi credentials
WIFI_SSID = wifi_secrets.secrets['ssid']
WIFI_PASSWORD = wifi_secrets.secrets['password']

# Initialize I2C and OLED
i2c = busio.I2C(board.vv, board.GP0)  # SCL=GP1, SDA=GP0
oled = SSD1306_I2C(128, 64, i2c)

# Initialize buttons
up_button = digitalio.DigitalInOut(board.GP6)
up_button.direction = digitalio.Direction.INPUT
up_button.pull = digitalio.Pull.UP

down_button = digitalio.DigitalInOut(board.GP7)
down_button.direction = digitalio.Direction.INPUT
down_button.pull = digitalio.Pull.UP

enter_button = digitalio.DigitalInOut(board.GP8)
enter_button.direction = digitalio.Direction.INPUT
enter_button.pull = digitalio.Pull.UP

# Initialize the thermal printer
ThermalPrinter = adafruit_thermal_printer.get_printer_class(2.69)
RX = board.GP5
TX = board.GP4
uart = busio.UART(TX, RX, baudrate=9600)
printer = ThermalPrinter(uart, auto_warm_up=False)


# Clear the display
def clearDisplay():
    oled.fill(0)
    oled.show()

clearDisplay()
# Display a message
oled.text("Connecting to wifi, OLED!", 0, 0, 1)
oled.show()

# Connect to Wi-Fi
print("Connecting to Wi-Fi...")
max_retries = 5
retry_delay = 2 # in seconds

for attempt in range(max_retries):
    try:
        wifi.radio.connect(WIFI_SSID, WIFI_PASSWORD)
        break  # Exit the loop if the connection is successful
    except Exception as e:
        print(f"Attempt {attempt + 1} failed: {e}")
        time.sleep(retry_delay)  # Wait before retrying

# Check if connected successfully
if wifi.radio.ipv4_address:
    clearDisplay()
    oled.text("Connected to wifi: ", 0, 0, 1)
    oled.text(str(wifi.radio.ipv4_address), 3, 10, 1)
    oled.show()
    print("Connected to Wi-Fi!")
    print("IP Address:", wifi.radio.ipv4_address)
else:
    clearDisplay()
    oled.text("Failed to connect!", 0, 0, 1)
    oled.show()
    print("Failed to connect to Wi-Fi after retries.")

# List of card formats and initial selection index
formats = ["standard", "pioneer", "modern", "legacy", "vintage"]
selected_format = 0  # Index inicial

# Function to display format selection menu on OLED
def draw_format_selection():
    clearDisplay()
    oled.text("Select the format:", 0, 0, 1)
    for i, format_name in enumerate(formats):
        # Desenha o '>' na linha selecionada
        if i == selected_format:
            oled.text("> " + format_name, 0, 17 + i * 10, 1)
        else:
            oled.text("  " + format_name, 0, 17 + i * 10, 1)
    oled.show()

# Show format selection menu after Wi-Fi connection
draw_format_selection()

# Menu navigation loop
while True:
    if not up_button.value:  
        selected_format = (selected_format - 1) % len(formats)  
        draw_format_selection()
        time.sleep(0.2)  

    if not down_button.value:  
        selected_format = (selected_format + 1) % len(formats)  
        draw_format_selection()
        time.sleep(0.2)  

    if not enter_button.value:  
        format_type = formats[selected_format]
        clearDisplay()
        oled.text("Format selected:", 0, 0, 1)
        oled.text(format_type, 0, 10, 1)
        oled.show()
        time.sleep(1)  
        break


# Create a socket pool and initialize the requests module with it
socket = socketpool.SocketPool(wifi.radio)
ssl_context = ssl.create_default_context()
requests = adafruit_requests.Session(socket, ssl_context)

# Function to draw an up arrow at (x, y)
def draw_up_arrow(x, y):
    oled.line(x, y + 7, x + 6, y + 7, color=1)  # Base of the arrow
    oled.line(x + 1, y + 6, x + 3, y, color=1)  # Left side of the arrow
    oled.line(x + 5, y + 6, x + 3, y, color=1)  # Right side of the arrow

# Function to draw a down arrow at (x, y)
def draw_down_arrow(x, y):
    oled.line(x, y, x + 6, y, color=1)  # Base of the arrow
    oled.line(x + 1, y + 1, x + 3, y + 7, color=1)  # Left side of the arrow
    oled.line(x + 5, y + 1, x + 3, y + 7, color=1)  # Right side of the arrow

# Function to draw a character in larger size
def draw_large_text(text, x, y):
    for char in text:
        if char == ' ':
            # Move the x position for spaces
            x += 8  # Adjust based on desired spacing
            continue

        # Define a simple bitmap for characters
        bitmap = {
            '0': [0x3E, 0x41, 0x41, 0x41, 0x3E],  # 0
            '1': [0x00, 0x42, 0x7F, 0x40, 0x00],  # 1
            '2': [0x62, 0x51, 0x49, 0x49, 0x46],  # 2
            '3': [0x22, 0x41, 0x49, 0x49, 0x36],  # 3
            '4': [0x1C, 0x10, 0x10, 0x7F, 0x10],  # 4
            '5': [0x27, 0x45, 0x45, 0x45, 0x3A],  # 5
            '6': [0x3E, 0x49, 0x49, 0x49, 0x3A],  # 6
            '7': [0x01, 0x01, 0x01, 0x01, 0x7F],  # 7
            '8': [0x36, 0x49, 0x49, 0x49, 0x36],  # 8
            '9': [0x26, 0x49, 0x49, 0x49, 0x3E],  # 9
        }

        # Get the bitmap for the current character
        if char in bitmap:
            char_bitmap = bitmap[char]
            for i in range(5):  # Assuming each character is 5 pixels wide
                for j in range(7):  # Assuming character height is 7 pixels
                    if char_bitmap[i] & (1 << j):
                        # Draw a filled rectangle for the pixel
                        oled.fill_rect(x + i * 2, y + j * 2, 2, 2, 1)  # Scale by 2 for larger size

        x += 10  # Move x position for next character

# Function to clear and update OLED with formatted display
def draw_screen(cmc):
    oled.fill(0)  # Clear the display
    oled.text("Enter CMC:", 0, 0, 1)
    draw_large_text(str(cmc),(128 - len(str(cmc)) * 10) // 2, 20)
    oled.text("Btn1:", 0, 40, 1)
    draw_up_arrow(40, 40)  # Up arrow for Btn1
    oled.text("Btn2:", 60, 40, 1)
    draw_down_arrow(100, 40)  # Down arrow for Btn2
    oled.text("Btn3: ENTER", 0, 54, 1)
    oled.show()

# Initial screen update
draw_screen(0)

# Function to fetch a random card from Scryfall based on value
def get_random_card_scryfall(cmc, format_type):
    url = f"https://api.scryfall.com/cards/random?q=t:creature+is:{format_type}+mv:{cmc}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            payload = response.json()  # Parse the JSON response

            # Extract the relevant information
            name = payload.get("name", "N/A")
            mana_cost = payload.get("mana_cost", "N/A")
            type_line = payload.get("type_line", "N/A")
            oracle_text = payload.get("oracle_text", "N/A")
            power = payload.get("power", "N/A")
            toughness = payload.get("toughness", "N/A")

            stats = f"{power} / {toughness}"

            # Print details to the console (or you can update the OLED here)
            print("name:", name)
            print("cmc:", mana_cost)
            print("type_line:", type_line)
            print("oracle_text:", oracle_text)
            print("power:", power)
            print("toughness:", toughness)

            # Optionally, display on OLED
            clearDisplay()
            oled.text("Name: " + name, 0, 0, 1)
            oled.text("Cost: " + str(mana_cost), 0, 10, 1)
            oled.text("Type: " + type_line, 0, 20, 1)
            oled.text("Text: " + oracle_text[:20], 0, 30, 1)  # Limiting the length for display
            oled.show()

            printer.feed(1)
            printer.size = adafruit_thermal_printer.SIZE_MEDIUM
            
            printer.justify = adafruit_thermal_printer.JUSTIFY_CENTER
            printer.bold = True
            printer.print(name)
            printer.bold = False
            printer.justify = adafruit_thermal_printer.JUSTIFY_RIGHT
            printer.print(mana_cost)
            printer.justify = adafruit_thermal_printer.JUSTIFY_CENTER
            printer.print("=" * 32)
            printer.justify = adafruit_thermal_printer.JUSTIFY_LEFT
            printer.print(type_line)
            printer.justify = adafruit_thermal_printer.JUSTIFY_CENTER
            printer.print("-" * 32)
            printer.justify = adafruit_thermal_printer.JUSTIFY_LEFT
            oracle_lines = oracle_text.split('\n')  
            for line in oracle_lines:
                printer.print(line)
            printer.justify = adafruit_thermal_printer.JUSTIFY_RIGHT
            printer.print(f"{power}/{toughness}")
            printer.justify = adafruit_thermal_printer.JUSTIFY_CENTER
            printer.print("=" * 32)
            printer.feed(4)

        else:
            print("Failed to fetch card. Status code:", response.status_code)
    except Exception as e:
        print("Error fetching card:", e)

value = 0
# Main loop to handle button presses and update the display
while True:
    if not up_button.value:  # Up button pressed
        if value < 15:
            value += 1
            draw_screen(value)
            time.sleep(0.2)  # Debounce delay

    if not down_button.value:  # Down button pressed
        if value > 0:
            value -= 1
            draw_screen(value)
            time.sleep(0.2)  # Debounce delay

    if not enter_button.value:  # Enter button pressed
        print("Enter pressed with value:", value)
        get_random_card_scryfall(value, formats[selected_format])
        value = 0
        draw_screen(value)
        time.sleep(0.2)  # Debounce delay

    time.sleep(0.1)  # Loop delay
