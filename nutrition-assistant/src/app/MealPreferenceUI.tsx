const inputClasses = "outline rounded outline-1";

export const defaultPreferenceValue = "I want to eat healthy, lots of fruits and veggies.";

export const MealPreferenceUI = props => {
  return (
    <>
      Describe your meal preferences: <textarea className={inputClasses} onChange={e => props.setMealPreference(e.target.value)} rows={3} defaultValue={defaultPreferenceValue} />
      Meal time: <input className={inputClasses}  onChange={e => props.setMealTime(e.target.value)} placeholder="e.g breakfast, snack..." />
      <button onClick={props.handleSubmit} className="px-4 py-2 font-semibold text-sm bg-cyan-500 text-white rounded-full shadow-sm">
        Submit
      </button>
    </>
  )

};
