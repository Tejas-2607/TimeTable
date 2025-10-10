// Helper to parse "HH:mm" string to total minutes from midnight
const timeToMinutes = (timeStr) => {
    if (!timeStr || !timeStr.includes(':')) return 0;
    const [hours, minutes] = timeStr.split(':').map(Number);
    return hours * 60 + minutes;
};

// Helper to convert total minutes back to "HH:mm" string
const minutesToTime = (totalMinutes) => {
    const hours = Math.floor(totalMinutes / 60).toString().padStart(2, '0');
    const minutes = (totalMinutes % 60).toString().padStart(2, '0');
    return `${hours}:${minutes}`;
};

// Main function to generate time slots for a week
export const generateTimeSlots = (startTime, endTime, lectureDuration, breakInfo) => {
    const startMinutes = timeToMinutes(startTime);
    const endMinutes = timeToMinutes(endTime);
    const breakStartMinutes = timeToMinutes(breakInfo.startTime);
    const breakEndMinutes = breakStartMinutes + parseInt(breakInfo.duration, 10);
    const lectDurationMins = parseInt(lectureDuration, 10);

    const weekDays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday'];
    const slotsByDay = {};

    weekDays.forEach(day => {
        const daySlots = [];
        let currentTime = startMinutes;

        // Morning session
        while (currentTime + lectDurationMins <= breakStartMinutes) {
            daySlots.push({ start: minutesToTime(currentTime), end: minutesToTime(currentTime + lectDurationMins), type: 'lecture' });
            currentTime += lectDurationMins;
        }

        // Add break
        daySlots.push({ start: minutesToTime(breakStartMinutes), end: minutesToTime(breakEndMinutes), type: 'break', name: breakInfo.name });

        // Afternoon session
        currentTime = breakEndMinutes;
        while (currentTime + lectDurationMins <= endMinutes) {
            daySlots.push({ start: minutesToTime(currentTime), end: minutesToTime(currentTime + lectDurationMins), type: 'lecture' });
            currentTime += lectDurationMins;
        }
        slotsByDay[day] = daySlots;
    });

    return slotsByDay;
};