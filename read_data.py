from flask import Flask, render_template, jsonify
import threading
from datetime import datetime
import gc 
import serial
import requests
import time

app = Flask(__name__)

data_history = {
    'labels': [],
    'x': [],
    'y': [],
    'z': [],
    'total': [],
    'temperature': []
}

url = "http://localhost:3000/api/update-iot-data" 
ser = serial.Serial('COM4', 115200)  # Adjust the port and baud rate 

def read_serial_data():
    while True:
        try:
            if ser.in_waiting > 0:
                # Reading a line from the serial port
                line = ser.readline().decode('utf-8').strip()
                # Spliting line by commas to extract values
                values = line.split(',')
                if len(values) == 6:  # Ensure the data has the correct number of elements
                    incoming_timestamp = values[0]
                    x = float(values[1])
                    y = float(values[2])
                    z = float(values[3])
                    total = float(values[4])
                    temperature = float(values[5])
                    dt_object = datetime.utcfromtimestamp(incoming_timestamp)
                    formatted_timestamp = dt_object.strftime('%Y-%m-%dT%I:%M:%S %p')


                    data_history['labels'].append(formatted_timestamp)
                    data_history['x'].append(x)
                    data_history['y'].append(y)
                    data_history['z'].append(z)
                    data_history['total'].append(total)
                    data_history['temperature'].append(temperature)

                    # Prepare the data to send to the Flask server
                    data = {
                        'timestamp': formatted_timestamp,
                        'x': x,
                        'y': y,
                        'z': z,
                        'total': total,
                        'temperature': temperature
                    }
                    
                    # Send the data to the Flask server
                    response = requests.post(url, json=data)
                    print(f"Data sent: {data}, Response: {response.status_code}")
                    
            time.sleep(1)  # Delay 

        except serial.SerialException as e:
            print(f"Serial Error: {e}")
            time.sleep(5)  # Wait before retrying
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)  # Wait before retrying

# Start the random data generation in a separate thread
threading.Thread(target=read_serial_data, daemon=True).start()

@app.route('/')
def index():
    gc.collect()
    return render_template('graph1.html')

@app.route('/api/get-graph-data', methods=['GET'])
def get_graph_data():
    return jsonify({
        "labels": data_history['labels'],
        "x": data_history['x'],
        "y": data_history['y'],
        "z": data_history['z'],
        "total": data_history['total'],
        "temperature": data_history['temperature']
    })

if __name__ == "__main__":
    app.run(port=3000, debug=True)
