import api from "../lib/api";

const LOCAL_STORAGE_KEY = "lab_sessions";
const DEFAULT_SESSIONS = [
  { id: 1, startTime: "10:30", endTime: "12:30" },
  { id: 2, startTime: "14:15", endTime: "16:15" },
  { id: 3, startTime: "16:30", endTime: "18:30" },
];

const loadLocalSessions = () => {
  const saved = localStorage.getItem(LOCAL_STORAGE_KEY);
  if (saved) {
    try {
      return JSON.parse(saved);
    } catch (e) {
      console.error("Error parsing lab sessions from localStorage", e);
    }
  }
  return DEFAULT_SESSIONS;
};

const saveLocalSessions = (sessions) => {
  localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(sessions));
};

export const getLabSessions = async () => {
  try {
    const res = await api.get("/settings/lab-timings");
    const sessions = res.data.sessions || [];
    if (sessions.length === 0) {
      return loadLocalSessions();
    }
    return sessions.map((session, index) => ({
      id: session.id || index + 1,
      startTime: session.startTime,
      endTime: session.endTime,
    }));
  } catch (error) {
    return loadLocalSessions();
  }
};

export const saveLabSessions = async (sessions) => {
  saveLocalSessions(sessions);
  try {
    await api.post("/settings/lab-timings", { sessions });
  } catch (error) {
    console.error("Error saving lab sessions to backend:", error);
  }
};

export const getSessionTimes = () => {
  const sessions = loadLocalSessions();
  return sessions
    .sort((a, b) => a.startTime.localeCompare(b.startTime))
    .map((s) => s.startTime);
};
