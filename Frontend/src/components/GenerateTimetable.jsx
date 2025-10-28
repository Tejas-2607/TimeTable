import { useState } from 'react';
import { ChevronRight, ChevronLeft, Check } from 'lucide-react';
import DepartmentTimings from './generate-steps/DepartmentTimings';
import SubjectsStep from './generate-steps/SubjectsStep';
import PracticalAssignment from './generate-steps/PracticalAssignment';
import TheoryAssignment from './generate-steps/TheoryAssignment';

export default function GenerateTimetable() {
  const [currentStep, setCurrentStep] = useState(1);
  const [formData, setFormData] = useState({
    timings: null,
    subjects: [],
    practicalAssignments: [],
    theoryAssignments: [],
  });

  const steps = [
    { number: 1, title: 'Department Timings', component: DepartmentTimings },
    { number: 2, title: 'Enter Subjects', component: SubjectsStep },
    { number: 3, title: 'Practical Assignment', component: PracticalAssignment },
    { number: 4, title: 'Theory Assignment', component: TheoryAssignment },
  ];

  const CurrentStepComponent = steps[currentStep - 1].component;

  const handleNext = () => {
    if (currentStep < steps.length) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handlePrevious = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleStepData = (stepName, data) => {
    setFormData((prev) => ({
      ...prev,
      [stepName]: data,
    }));
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-slate-800">
          Generate Timetable
        </h2>
        <p className="text-slate-600 mt-1">
          Multi-step process to generate automated timetable
        </p>
      </div>

      <div className="mb-8">
        <div className="flex items-center justify-between">
          {steps.map((step, index) => (
            <div key={step.number} className="flex items-center flex-1">
              <div className="flex flex-col items-center flex-1">
                <div
                  className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg transition-all ${
                    currentStep === step.number
                      ? 'bg-blue-600 text-white shadow-lg'
                      : currentStep > step.number
                      ? 'bg-green-500 text-white'
                      : 'bg-slate-200 text-slate-500'
                  }`}
                >
                  {currentStep > step.number ? (
                    <Check size={24} />
                  ) : (
                    step.number
                  )}
                </div>
                <span
                  className={`text-sm mt-2 font-medium text-center ${
                    currentStep === step.number
                      ? 'text-blue-600'
                      : currentStep > step.number
                      ? 'text-green-600'
                      : 'text-slate-500'
                  }`}
                >
                  {step.title}
                </span>
              </div>
              {index < steps.length - 1 && (
                <div
                  className={`h-1 flex-1 mx-4 transition-all ${
                    currentStep > step.number
                      ? 'bg-green-500'
                      : 'bg-slate-200'
                  }`}
                />
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-xl shadow-lg p-8 border border-slate-200 min-h-[500px]">
        <CurrentStepComponent
          data={formData}
          onDataChange={handleStepData}
          onNext={handleNext}
        />
      </div>

      <div className="mt-6 flex items-center justify-between">
        <button
          onClick={handlePrevious}
          disabled={currentStep === 1}
          className={`flex items-center gap-2 px-6 py-3 rounded-lg transition-all ${
            currentStep === 1
              ? 'bg-slate-100 text-slate-400 cursor-not-allowed'
              : 'bg-slate-200 text-slate-700 hover:bg-slate-300'
          }`}
        >
          <ChevronLeft size={20} />
          Previous
        </button>

        <div className="text-sm text-slate-600">
          Step {currentStep} of {steps.length}
        </div>

        {currentStep < steps.length ? (
          <button
            onClick={handleNext}
            className="flex items-center gap-2 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors"
          >
            Next
            <ChevronRight size={20} />
          </button>
        ) : (
          <button className="flex items-center gap-2 bg-green-600 text-white px-6 py-3 rounded-lg hover:bg-green-700 transition-colors">
            <Check size={20} />
            Generate Timetable
          </button>
        )}
      </div>
    </div>
  );
}
