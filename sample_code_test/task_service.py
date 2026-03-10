def create_new_db_task(db_manager, room_id_map, start_place, destination, mission_content):

    room_id = room_id_map.get(destination)

    if not start_place or not destination or not mission_content:
        print("請填寫所有欄位！")
        return None

    new_id = db_manager.add_new_task(
        start_place,
        destination,
        mission_content,
        room_id=room_id
    )

    return new_id