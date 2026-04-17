const DEFAULT_SESSIONS = [
  { id: 1, startTime: '10:30', endTime: '12:30' },
  { id: 2, startTime: '14:15', endTime: '16:15' },
  { id: 3, startTime: '16:30', endTime: '18:30' },
];

export const getLabSessions = () => {
  const saved = localStorage.getItem('lab_sessions');
  if (saved) {
    try {
      return JSON.parse(saved);
    } catch (e) {
      console.error('Error parsing lab sessions from localStorage', e);
    }
  }
  return DEFAULT_SESSIONS;
};

export const saveLabSessions = (sessions) => {
  localStorage.setItem('lab_sessions', JSON.stringify(sessions));
};

export const getSessionTimes = () => {
  const sessions = getLabSessions();
  // Sort by start time to keep them in order
  return sessions
    .sort((a, b) => a.startTime.localeCompare(b.startTime))
    .map(s => s.startTime);
};
