from datetime import datetime, timedelta

def add_ten_minutes(global_time):
    date_part, time_part = global_time.split(", ")
    day_number = int(date_part.split(" ")[1])
    time_format = "%H:%M"
    time_obj = datetime.strptime(time_part, time_format)
    new_time_obj = time_obj + timedelta(minutes=10)
    if new_time_obj.time() >= datetime.strptime("20:00", time_format).time():
        new_date = f"Day {day_number + 1}"
        new_time = "08:00"
    else:
        new_date = date_part
        new_time = new_time_obj.strftime(time_format)
    return f"{new_date}, {new_time}"

if __name__ == "__main__":
    global_time = "Day 1, 08:50"
    # new_time = global_time.split(", ")[1]
    new_time = add_ten_minutes(global_time)
    print(new_time)