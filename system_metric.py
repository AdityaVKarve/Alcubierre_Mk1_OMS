import time
import psutil
import csv
import matplotlib.pyplot as plt

# Initialize empty lists to store the metrics
timestamps = []
cpu_percentages = []
memory_percentages = []

print(timestamps)

# Function to collect and store metrics
def collect_metrics():
    print("Collecting metrics...")
    timestamp = time.strftime('%H:%M:%S')

    # Get all running processes
    processes = psutil.process_iter(['pid', 'name', 'cpu_percent', 'memory_percent'])
    
    # Filter processes based on name
    python_processes = [p for p in processes if p.info['name'] == 'python3']
    uvicorn_processes = [p for p in processes if p.info['name'] == 'uvicorn']

    # Calculate the total CPU and memory percentages for Python processes
    python_cpu_percentage = sum([p.info['cpu_percent'] for p in python_processes])
    python_memory_percentage = sum([p.info['memory_percent'] for p in python_processes])

    # Calculate the total CPU and memory percentages for Uvicorn processes
    uvicorn_cpu_percentage = sum([p.info['cpu_percent'] for p in uvicorn_processes])
    uvicorn_memory_percentage = sum([p.info['memory_percent'] for p in uvicorn_processes])

    # Append the metrics to the lists
    timestamps.append(timestamp)
    cpu_percentages.append((python_cpu_percentage, uvicorn_cpu_percentage))
    memory_percentages.append((python_memory_percentage, uvicorn_memory_percentage))

    # print(timestamps)

# Function to save data as CSV
def save_as_csv(filename):
    print("Saving data as CSV...")
    data = zip(timestamps, cpu_percentages, memory_percentages)
    with open(filename, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(['Timestamp', 'Python CPU Percentage', 'Uvicorn CPU Percentage',
                         'Python Memory Percentage', 'Uvicorn Memory Percentage'])
        writer.writerows(data)
    print(f"Data saved as {filename}")

# Function to plot the graph
def plot_graph():
    python_cpu_percentages, uvicorn_cpu_percentages = zip(*cpu_percentages)
    python_memory_percentages, uvicorn_memory_percentages = zip(*memory_percentages)
    
    plt.plot(timestamps, python_cpu_percentages, label='Python CPU %')
    plt.plot(timestamps, uvicorn_cpu_percentages, label='Uvicorn CPU %')
    plt.plot(timestamps, python_memory_percentages, label='Python Memory %')
    plt.plot(timestamps, uvicorn_memory_percentages, label='Uvicorn Memory %')
    
    plt.xlabel('Time')
    plt.ylabel('Percentage')
    plt.title('Process Metrics')
    plt.legend()
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()

# Main execution
try:
    while True:
        collect_metrics()
        time.sleep(1)
except KeyboardInterrupt:
    filename = 'process_metrics.csv'
    save_as_csv(filename)
    plot_graph()
