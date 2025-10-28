const STORAGE_KEYS = {
  FACULTIES: 'schedulo_faculties',
  LABS: 'schedulo_labs',
  CLASS_STRUCTURE: 'schedulo_class_structure',
  SUBJECTS: 'schedulo_subjects',
  DEPARTMENT_TIMINGS: 'schedulo_department_timings',
  FACULTY_ASSIGNMENTS: 'schedulo_faculty_assignments',
  TIMETABLES: 'schedulo_timetables',
};

const generateId = () => {
  return `${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
};

const getFromStorage = (key) => {
  try {
    const data = localStorage.getItem(key);
    return data ? JSON.parse(data) : [];
  } catch (error) {
    console.error('Error reading from localStorage:', error);
    return [];
  }
};

const saveToStorage = (key, data) => {
  try {
    localStorage.setItem(key, JSON.stringify(data));
  } catch (error) {
    console.error('Error saving to localStorage:', error);
  }
};

export const storage = {
  faculties: {
    getAll: () => getFromStorage(STORAGE_KEYS.FACULTIES),

    insert: (faculty) => {
      const faculties = getFromStorage(STORAGE_KEYS.FACULTIES);
      const newFaculty = {
        ...faculty,
        id: generateId(),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      faculties.push(newFaculty);
      saveToStorage(STORAGE_KEYS.FACULTIES, faculties);
      return newFaculty;
    },

    update: (id, updates) => {
      const faculties = getFromStorage(STORAGE_KEYS.FACULTIES);
      const index = faculties.findIndex(f => f.id === id);
      if (index !== -1) {
        faculties[index] = {
          ...faculties[index],
          ...updates,
          updated_at: new Date().toISOString(),
        };
        saveToStorage(STORAGE_KEYS.FACULTIES, faculties);
        return faculties[index];
      }
      return null;
    },

    delete: (id) => {
      const faculties = getFromStorage(STORAGE_KEYS.FACULTIES);
      const filtered = faculties.filter(f => f.id !== id);
      saveToStorage(STORAGE_KEYS.FACULTIES, filtered);
      return true;
    },
  },

  labs: {
    getAll: () => getFromStorage(STORAGE_KEYS.LABS),

    insert: (lab) => {
      const labs = getFromStorage(STORAGE_KEYS.LABS);
      const newLab = {
        ...lab,
        id: generateId(),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      labs.push(newLab);
      saveToStorage(STORAGE_KEYS.LABS, labs);
      return newLab;
    },

    update: (id, updates) => {
      const labs = getFromStorage(STORAGE_KEYS.LABS);
      const index = labs.findIndex(l => l.id === id);
      if (index !== -1) {
        labs[index] = {
          ...labs[index],
          ...updates,
          updated_at: new Date().toISOString(),
        };
        saveToStorage(STORAGE_KEYS.LABS, labs);
        return labs[index];
      }
      return null;
    },

    delete: (id) => {
      const labs = getFromStorage(STORAGE_KEYS.LABS);
      const filtered = labs.filter(l => l.id !== id);
      saveToStorage(STORAGE_KEYS.LABS, filtered);
      return true;
    },
  },

  classStructure: {
    getAll: () => getFromStorage(STORAGE_KEYS.CLASS_STRUCTURE),

    getByYear: (year) => {
      const structures = getFromStorage(STORAGE_KEYS.CLASS_STRUCTURE);
      return structures.find(s => s.year === year);
    },

    upsert: (year, data) => {
      const structures = getFromStorage(STORAGE_KEYS.CLASS_STRUCTURE);
      const index = structures.findIndex(s => s.year === year);

      if (index !== -1) {
        structures[index] = {
          ...structures[index],
          ...data,
          updated_at: new Date().toISOString(),
        };
      } else {
        structures.push({
          ...data,
          year,
          id: generateId(),
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        });
      }

      saveToStorage(STORAGE_KEYS.CLASS_STRUCTURE, structures);
      return structures.find(s => s.year === year);
    },
  },

  subjects: {
    getAll: () => getFromStorage(STORAGE_KEYS.SUBJECTS),

    getByYear: (year) => {
      const subjects = getFromStorage(STORAGE_KEYS.SUBJECTS);
      return subjects.filter(s => s.year === year);
    },

    getByYearAndType: (year, types) => {
      const subjects = getFromStorage(STORAGE_KEYS.SUBJECTS);
      return subjects.filter(s => s.year === year && types.includes(s.class_type));
    },

    insert: (subject) => {
      const subjects = getFromStorage(STORAGE_KEYS.SUBJECTS);
      const newSubject = {
        ...subject,
        id: generateId(),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      subjects.push(newSubject);
      saveToStorage(STORAGE_KEYS.SUBJECTS, subjects);
      return newSubject;
    },

    update: (id, updates) => {
      const subjects = getFromStorage(STORAGE_KEYS.SUBJECTS);
      const index = subjects.findIndex(s => s.id === id);
      if (index !== -1) {
        subjects[index] = {
          ...subjects[index],
          ...updates,
          updated_at: new Date().toISOString(),
        };
        saveToStorage(STORAGE_KEYS.SUBJECTS, subjects);
        return subjects[index];
      }
      return null;
    },

    delete: (id) => {
      const subjects = getFromStorage(STORAGE_KEYS.SUBJECTS);
      const filtered = subjects.filter(s => s.id !== id);
      saveToStorage(STORAGE_KEYS.SUBJECTS, filtered);
      return true;
    },
  },

  departmentTimings: {
    get: () => {
      const timings = getFromStorage(STORAGE_KEYS.DEPARTMENT_TIMINGS);
      return timings[0] || null;
    },

    upsert: (data) => {
      const timings = getFromStorage(STORAGE_KEYS.DEPARTMENT_TIMINGS);

      if (timings.length > 0) {
        timings[0] = {
          ...timings[0],
          ...data,
          updated_at: new Date().toISOString(),
        };
      } else {
        timings.push({
          ...data,
          id: generateId(),
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        });
      }

      saveToStorage(STORAGE_KEYS.DEPARTMENT_TIMINGS, timings);
      return timings[0];
    },
  },

  facultyAssignments: {
    getAll: () => getFromStorage(STORAGE_KEYS.FACULTY_ASSIGNMENTS),

    getByYearAndType: (year, type) => {
      const assignments = getFromStorage(STORAGE_KEYS.FACULTY_ASSIGNMENTS);
      const faculties = getFromStorage(STORAGE_KEYS.FACULTIES);
      const subjects = getFromStorage(STORAGE_KEYS.SUBJECTS);

      return assignments
        .filter(a => a.year === year && a.assignment_type === type)
        .map(assignment => ({
          ...assignment,
          faculties: faculties.find(f => f.id === assignment.faculty_id),
          subjects: subjects.find(s => s.id === assignment.subject_id),
        }));
    },

    insert: (assignment) => {
      const assignments = getFromStorage(STORAGE_KEYS.FACULTY_ASSIGNMENTS);
      const newAssignment = {
        ...assignment,
        id: generateId(),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      assignments.push(newAssignment);
      saveToStorage(STORAGE_KEYS.FACULTY_ASSIGNMENTS, assignments);
      return newAssignment;
    },

    update: (id, updates) => {
      const assignments = getFromStorage(STORAGE_KEYS.FACULTY_ASSIGNMENTS);
      const index = assignments.findIndex(a => a.id === id);
      if (index !== -1) {
        assignments[index] = {
          ...assignments[index],
          ...updates,
          updated_at: new Date().toISOString(),
        };
        saveToStorage(STORAGE_KEYS.FACULTY_ASSIGNMENTS, assignments);
        return assignments[index];
      }
      return null;
    },

    delete: (id) => {
      const assignments = getFromStorage(STORAGE_KEYS.FACULTY_ASSIGNMENTS);
      const filtered = assignments.filter(a => a.id !== id);
      saveToStorage(STORAGE_KEYS.FACULTY_ASSIGNMENTS, filtered);
      return true;
    },
  },

  timetables: {
    getAll: () => getFromStorage(STORAGE_KEYS.TIMETABLES),

    getByYearAndSemester: (academicYear, semester) => {
      const timetables = getFromStorage(STORAGE_KEYS.TIMETABLES);
      return timetables.filter(
        t => t.academic_year === academicYear && t.semester === semester
      );
    },

    insert: (timetable) => {
      const timetables = getFromStorage(STORAGE_KEYS.TIMETABLES);
      const newTimetable = {
        ...timetable,
        id: generateId(),
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      };
      timetables.push(newTimetable);
      saveToStorage(STORAGE_KEYS.TIMETABLES, timetables);
      return newTimetable;
    },
  },
};
