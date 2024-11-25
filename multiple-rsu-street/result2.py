import json
import os
import re

def process_log_file(file_path):
    events = []
    current_event = []

    with open(file_path, 'r') as file:
        for line in file:
            if line.strip():  # Check if the line is not empty
                current_event.append(line.strip())
            else:
                if current_event:
                    events.append(current_event)
                    current_event = []

        # Append the last event if it doesn't end with an empty line
        if current_event:
            events.append(current_event)

    return events


def extract_event_id(event):
    first_item = event[0]  # Get the first item from the list
    if "E #" in first_item:
        parts = first_item.split()
        for i, part in enumerate(parts):
            if part == "E":  # Check for the "E" token
                if i + 2 < len(parts):  # Ensure there's a number after "E #"
                    return parts[i + 2]  # Return the number following "E #"
    return None  # Return None if "E #" pattern is not found


def filter_events_by_strings(events):

    search_strings = ["KF"]

    filtered_events = [event for event in events if any(any(substring in line for substring in search_strings) for line in event)]
    return filtered_events

def extract_following_events_based_on_occurrences(events, search_string):
    results = {}
    for i, event in enumerate(events[:]):
        # Count occurrences of the search string in the current event
        count = sum(search_string in line for line in event)
        
        if count > 0:
            results[extract_event_id(event)] = {}
            results[extract_event_id(event)]["event"] = event
    
    return results

def extract_parameter_from_event(event):
    transmitter_id = None
    receiver_id = None
    start_time = None
    end_time = None
    transmitter_position = None
    receiver_position = None
    receiver_result = None
    reception_power = None

    for entry in event:
        # Extract transmitter_id, receiver_id, start_time, end_time
        if "DEBUG:Receiving Ieee80211ScalarTransmission" in entry:
            transmitter_id_match = re.search(r'transmitterId = (\d+)', entry)
            receiver_id_match = re.search(r'receiverId = (\d+)', entry)
            start_time_match = re.search(r'startTime = ([\d.]+)', entry)
            end_time_match = re.search(r'endTime = ([\d.]+)', entry)
            transmitter_pos_match = re.search(r'startPosition = \(([\d., -]+)\)', entry)
            receiver_pos_match = re.search(r'startPosition = \(([\d., -]+)\).*endPosition = \(([\d., -]+)\)', entry)
            reception_power_match = re.search(r'power = ([\de.-]+) W', entry)

            if transmitter_id_match:
                transmitter_id = transmitter_id_match.group(1)
            if receiver_id_match:
                receiver_id = receiver_id_match.group(1)
            if start_time_match:
                start_time = float(start_time_match.group(1))
            if end_time_match:
                end_time = float(end_time_match.group(1))
            if transmitter_pos_match:
                transmitter_position = transmitter_pos_match.group(1)
            if receiver_pos_match:
                receiver_position = receiver_pos_match.group(2)
            if reception_power_match:
                reception_power = float(reception_power_match.group(1))

        # Extract receiver result (True/False)
        if "DEBUG:Computing whether reception is possible" in entry:
            receiver_result = False if "reception is impossible" in entry else True

    return {
        "transmitter_id": transmitter_id,
        "receiver_id": receiver_id,
        "start_time": start_time,
        "end_time": end_time,
        "transmitter_position": transmitter_position,
        "receiver_position": receiver_position,
        "receiver_result": receiver_result,
        "reception_power": reception_power
    }




def extract_paramater_from_event_list(events_dict):
    for key, value in events_dict.items():
        # transmitter_id, transmitter_startTime, transmitter_endTime,transmitter_position = extract_transmitter_id_and_timestamp(value["transmitter_event"])
        events_dict[key].update(extract_parameter_from_event(value["event"]))

        # Remove the transmitter_event and receiver_events keys
        events_dict[key].pop("event")

    return events_dict


def ensure_directory_exists(file_path):
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        os.makedirs(directory)
        

def main():

    speed = 70 # km/hour
    events = process_log_file("./results/General-#0.elog")
    log_folder_path = "./results/speed" + str(speed) + "/300vehicle/"
    ensure_directory_exists(log_folder_path)
    filtered_events_file_path = log_folder_path + "filtered_events.json"
    extracted_events_file_path = log_folder_path + "/extracted_events.json"
    # print(events)

    filtered_string = "DEBUG:Computing whether reception is possible:"
    filtered_events = extract_following_events_based_on_occurrences(events, filtered_string)
  
    # # write to the json file
    # with open(filtered_events_file_path, 'w') as f:
    #     json.dump(filtered_events, f, indent=4)

    # Extract transmitterId, startTime, receiverId, and reception possibility
    extracted_events = extract_paramater_from_event_list(filtered_events)

    # write to the json file
    with open("./results/log.json", "w") as f:
        json.dump(extracted_events, f, indent=4)

    # # if transmitter_id is not 0 , then the event is deleted form the dictionary
    # for key, value in list(extracted_events.items()):
    #     if value["transmitter_id"] != "0":
    #         extracted_events.pop(key)
            
    # # write to the json file even if the file is empty
    # with open(extracted_events_file_path, 'w') as f:
    #     json.dump(extracted_events, f, indent=4)



if __name__ == "__main__":
    main()



