import json

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
            # Extract (count - 1) subsequent events
            count -= 1  # Adjust to extract one fewer than the count of occurrences
            buffer_log_num = 1 # tranmitterのログからすぐにreceiverのログに行かない可能性があるためバッファを設ける
            subsequent_events = events[i+1:i+1+count+buffer_log_num] if i+1+count <= len(events) else events[i+1:]

            results[extract_event_id(event)] = {}
            results[extract_event_id(event)]["transmitter_event"] = event
            results[extract_event_id(event)]["receiver_events"] = subsequent_events
    
    return results

def extract_transmitter_id_and_timestamp(log_entries):
    transmitter_id = None
    startTime = None
    endTime = None
    transmitter_position = None
    for entry in log_entries:
        if "transmitterId =" in entry:
            parts = entry.split(',')
            # Extract transmitterId and startTime
            for part in parts:
                if "transmitterId" in part:
                    transmitter_id = part.split('=')[-1].strip()
                if "startTime" in part:
                    startTime = part.split('=')[-1].strip()
                    startTime = float(startTime)
                if "endTime" in part:
                    endTime = part.split('=')[-1].strip()
                    endTime = float(endTime)
                
                
                # Attempt to extract position if available
                if "startPosition =" in entry:
                    # Correctly capture the full coordinates in the tuple format
                    transmitter_position = entry.split("startPosition =")[1].split('),')[0].strip() + ')'
    return transmitter_id, startTime, endTime, transmitter_position


# from multiple receiver logs, extract receiver_id and reception possibility
def extract_receiver_id_and_reception_possibility(log_entries_2list):
    results = {}
    receivable_id_list = []

    for log_entries in log_entries_2list:
        receiver_id = None
        position = None
        reception_status = "possible"
        startTime = None
        endTime = None

        for entry in log_entries:


            if "receiverId =" in entry:
                # Extract the receiver ID from the entry
                receiver_id = entry.split('receiverId =')[-1].split(',')[0].strip()
            # Attempt to extract position if available
            if "startPosition =" in entry:
                # Correctly capture the full coordinates in the tuple format
                position = entry.split("startPosition =")[1].split('),')[0].strip() + ')'
            # Update the reception status based on current entry details
            if "reception is impossible" in entry:
                reception_status = "impossible"


            # if "startTime" in entry:
            #     startTime = entry.split('=')[-1].strip()
            # if "endTime" in entry:
            #     endTime = entry.split('=')[-1].strip()

        if receiver_id is not None:
            results[receiver_id] = {
                "position": position,
                "reception_status": reception_status
            }

            if reception_status == "possible":
                receivable_id_list.append(int(receiver_id))
            
    # order by receiver_id
    results = dict(sorted(results.items(), key=lambda x: x[0]))
    receivable_id_list = sorted(receivable_id_list)
        
    return results, receivable_id_list


def extract_paramater_values(events_dict):
    for key, value in events_dict.items():
        transmitter_id, transmitter_startTime, transmitter_endTime,transmitter_position = extract_transmitter_id_and_timestamp(value["transmitter_event"])
        receive_results, receivable_id_list = extract_receiver_id_and_reception_possibility(value["receiver_events"])
        events_dict[key]["transmitter_id"] = transmitter_id
        events_dict[key]["startTime"] = transmitter_startTime
        events_dict[key]["endTime"] = transmitter_endTime
        events_dict[key]["transmitter_position"] = transmitter_position
        events_dict[key]["receiver_results"] = receive_results
        events_dict[key]["receivable_id_list"] = receivable_id_list
        events_dict[key]["receivable_id_count"] = len(receivable_id_list)

        # Remove the transmitter_event and receiver_events keys
        events_dict[key].pop("transmitter_event")
        events_dict[key].pop("receiver_events")
    
    return events_dict
        

def main():

    speed = 70 # km/hour
    events = process_log_file("./results/General-#0.elog")
    log_folder_path = "./results/speed" + str(speed) + "/300vehicle/"
    filtered_events_file_path = log_folder_path + "filtered_events.json"
    extracted_events_file_path = log_folder_path + "/extracted_events.json"
    # print(events)

    filtered_string = "DEBUG:Sending (inet::physicallayer::RadioFrame)GeoNet packet"
    filtered_events = extract_following_events_based_on_occurrences(events, filtered_string)
  
    # write to the json file
    with open(filtered_events_file_path, 'w') as f:
        json.dump(filtered_events, f, indent=4)

    # Extract transmitterId, startTime, receiverId, and reception possibility
    extracted_events = extract_paramater_values(filtered_events)

    # if transmitter_id is not 0 , then the event is deleted form the dictionary
    for key, value in list(extracted_events.items()):
        if value["transmitter_id"] != "0":
            extracted_events.pop(key)
            
    # write to the json file even if the file is empty
    with open(extracted_events_file_path, 'w') as f:
        json.dump(extracted_events, f, indent=4)

    

    





if __name__ == "__main__":
    main()



