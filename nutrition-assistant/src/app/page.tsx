"use client";
import React from 'react';

const inputClasses = "outline rounded outline-1";

//- user input: Make me a balanced <kind> meal for <meal-time>. My bodyweight in kg is <count>.
// - on submit, get meal names from chatgpt, then send each mealname to a aws function or a worker thread, which generates the recipe for each mealname
// - when the recipes come back, give them to another lambda, which does the scoring, this means I need to deploy the sqlite3 db OR I can rewrite the python script in typescript and call it from a webworker

const MealPreferenceUI = props => {
  return (
    <>
      Describe your meal preferences: <textarea className={inputClasses} onChange={e => props.setMealPreference(e.target.value)} rows={3} placeholder="I want to eat healthy, lots of fruits and veggies." />
      Meal time: <input className={inputClasses}  onChange={e => props.setMealTime(e.target.value)} placeholder="e.g breakfast, snack..." />
      My bodyweight in kg is <input className={inputClasses} min={1} type="number" onChange={e => props.setWeight(e.target.valueAsNumber)}/>
      <button onClick={props.handleSubmit} className="px-4 py-2 font-semibold text-sm bg-cyan-500 text-white rounded-full shadow-sm">
        Submit
      </button>
    </>
  )

};

export default function Home() {
  const [mealPreference, setMealPreference] = React.useState<string | undefined>();
  const [mealTime, setMealTime] = React.useState<string | undefined>();
  const [weight, setWeight] = React.useState<number | undefined>();

  const handleSubmit = () => {
    const fields = [["meal preference", mealPreference], ["meal time", mealTime], ["weight", weight]];
    const emptyFields = fields.filter(([name, value]) => !value);
    if (emptyFields.length > 0) {
        const fieldNames = emptyFields.map(f => f[0]).join(", ");
        alert(`Please fill in the ${fieldNames} field(s).`);
    } else {
      // TODO submit
    }

  };

  return (
    <main className="flex min-h-screen flex-col items-center justify-between p-24">
      <MealPreferenceUI
        setMealPreference={setMealPreference}
        setMealTime={setMealTime}
        setWeight={setWeight}
        handleSubmit={handleSubmit}
      />
    </main>
  )
}
