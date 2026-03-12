import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ChevronRight, ChevronLeft, Check, CheckCircle2, ArrowRight } from 'lucide-react';
import { regenerateMasterTimetable } from '../services/timetableGeneratorService';
import DepartmentTimings from './generate-steps/DepartmentTimings';
import SubjectsStep from './generate-steps/SubjectsStep';
import FacultyAssignment from './generate-steps/FacultyAssignment';

export default function GenerateTimetable() {
  const navigate = useNavigate();
  const [currentStep, setCurrentStep] = useState(1);
  const [isGenerating, setIsGenerating] = useState(false);
  const [showSuccess, setShowSuccess] = useState(false);
  const [formData, setFormData] = useState({
    timings: null,
    subjects: [],
    practicalAssignments: [],
    theoryAssignments: [],
  });

  const steps = [
    { number: 1, title: 'Department Timings', component: DepartmentTimings },
    { number: 2, title: 'Enter Subjects', component: SubjectsStep },
    { number: 3, title: 'Faculty Assignment', component: FacultyAssignment },
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

  const handleGenerateTimetable = async () => {
    setIsGenerating(true);

    try {
      const response = await regenerateMasterTimetable();

      // Show success popup
      setShowSuccess(true);

    } catch (error) {
      const errorMessage = error.response?.data?.error || error.message || 'Failed to generate timetable. Please try again.';

      // Show error alert
      alert(`❌ Error: ${errorMessage}`);
    } finally {
      setIsGenerating(false);
    }
  };

  return (
    <div className="p-8">
      <div className="mb-8">
        <h2 className="text-3xl font-bold text-slate-800 tracking-tight">Generate Timetable</h2>
        <p className="text-slate-500 mt-2">
          Automated multi-step process for timetable generation
        </p>
      </div>

      <div className="mb-12 mt-4">
        <div className="flex items-start justify-between w-full">
          {steps.map((step, index) => (
            <div key={step.number} className="contents">
              <div className="flex flex-col items-center w-36 relative z-10">
                <div
                  className={`w-12 h-12 rounded-full flex items-center justify-center font-bold text-lg transition-all duration-300 ${currentStep === step.number
                    ? 'bg-blue-600 text-white shadow-[0_4px_14px_0_rgba(37,99,235,0.39)]'
                    : currentStep > step.number
                      ? 'bg-emerald-500 text-white shadow-md shadow-emerald-500/20'
                      : 'bg-slate-50 text-slate-500 border border-slate-200/80 shadow-sm'
                    }`}
                >
                  {currentStep > step.number ? (
                    <Check size={24} />
                  ) : (
                    step.number
                  )}
                </div>
                <span
                  className={`text-sm mt-3 font-medium text-center transition-colors ${currentStep === step.number
                    ? 'text-blue-600 font-semibold'
                    : currentStep > step.number
                      ? 'text-emerald-600'
                      : 'text-slate-400'
                    }`}
                >
                  {step.title}
                </span>
              </div>
              {index < steps.length - 1 && (
                <div
                  className={`h-[2px] flex-1 mt-6 mx-2 transition-all duration-500 ${currentStep > step.number
                    ? 'bg-emerald-500'
                    : 'bg-slate-100'
                    }`}
                />
              )}
            </div>
          ))}
        </div>
      </div>

      <div className="bg-white rounded-3xl shadow-sm p-8 border border-slate-200/60 min-h-[500px]">
        <CurrentStepComponent
          data={formData}
          onDataChange={handleStepData}
          onNext={handleNext}
        />
      </div>

      <div className="mt-6 flex items-center justify-between">
        <button
          onClick={handlePrevious}
          disabled={currentStep === 1 || isGenerating}
          className={`flex items-center gap-2 px-6 py-3 rounded-xl transition-all font-medium ${currentStep === 1 || isGenerating
            ? 'bg-slate-50 text-slate-400 cursor-not-allowed border border-transparent'
            : 'bg-white border border-slate-200 text-slate-600 hover:bg-slate-50 hover:text-slate-800 shadow-sm'
            }`}
        >
          <ChevronLeft size={20} />
          Previous
        </button>

        <div className="text-sm font-medium text-slate-400 bg-slate-100 px-4 py-2 rounded-full">
          Step {currentStep} of {steps.length}
        </div>

        {currentStep < steps.length ? (
          <button
            onClick={handleNext}
            disabled={isGenerating}
            className="flex items-center gap-2 bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-all font-medium disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next
            <ChevronRight size={20} />
          </button>
        ) : (
          <button
            onClick={handleGenerateTimetable}
            disabled={isGenerating}
            className="flex items-center gap-2 bg-emerald-600 text-white px-6 py-3 rounded-xl hover:bg-emerald-700 transition-all font-medium shadow-md shadow-emerald-600/20 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Check size={20} />
            {isGenerating ? 'Generating...' : 'Generate Timetable'}
          </button>
        )}
      </div>
      {/* Success Modal */}
      {showSuccess && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-2xl shadow-2xl max-w-md w-full p-8 text-center">
            <div className="w-16 h-16 rounded-full bg-emerald-100 flex items-center justify-center mx-auto mb-4">
              <CheckCircle2 size={36} className="text-emerald-600" />
            </div>
            <h3 className="text-2xl font-bold text-slate-800 mb-2">Timetable Generated!</h3>
            <p className="text-slate-500 text-sm mb-6">
              Your timetable has been generated successfully. You can now view the master practical plan and class-wise timetables.
            </p>
            <button
              onClick={() => { setShowSuccess(false); navigate('/view'); }}
              className="flex items-center justify-center gap-2 w-full py-3 bg-gradient-to-r from-blue-600 to-cyan-600 text-white font-semibold rounded-xl hover:from-blue-700 hover:to-cyan-700 transition-all shadow-md shadow-blue-600/20 active:scale-[0.98]"
            >
              View Timetables
              <ArrowRight size={18} />
            </button>
          </div>
        </div>
      )}
    </div>
  );
}