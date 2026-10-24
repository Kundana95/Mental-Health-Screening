import { useRef, useState } from 'react';

const phq9Questions = [
  'Little interest or pleasure in doing things',
  'Feeling down, depressed, or hopeless',
  'Trouble falling or staying asleep, or sleeping too much',
  'Feeling tired or having little energy',
  'Poor appetite or overeating',
  'Feeling bad about yourself — or that you are a failure or have let yourself or your family down',
  'Trouble concentrating on things, such as reading the newspaper or watching television',
  'Moving or speaking so slowly that other people could have noticed? Or the opposite — being so fidgety or restless that you have been moving around a lot more than usual',
  'Thoughts that you would be better off dead, or of hurting yourself in some way',
];

const gad7Questions = [
  'Feeling nervous, anxious or on edge',
  'Not being able to stop or control worrying',
  'Worrying too much about different things',
  'Trouble relaxing',
  'Being so restless that it is hard to sit still',
  'Becoming easily annoyed or irritable',
  'Feeling afraid as if something awful might happen',
];

const scoredChoices = [
  { label: 'Not at all', score: 0 },
  { label: 'Several days', score: 1 },
  { label: 'More than half the days', score: 2 },
  { label: 'Nearly every day', score: 3 },
];

const contextQuestions = [
  { key: 'age_group', label: 'What is your age group?', choices: ['Under 18', '18–24', '25–34', '35–44', '45 and above', 'Prefer not to say'] },
  { key: 'current_status', label: 'What is your current status?', choices: ['Student', 'Employed', 'Self-employed', 'Unemployed', 'Other', 'Prefer not to say'] },
  { key: 'sleep_duration', label: 'On average, how many hours do you sleep per night?', choices: ['Less than 5 hours', '5–6 hours', '7–8 hours', 'More than 8 hours', 'My sleep schedule varies considerably'] },
  { key: 'sleep_quality', label: 'How would you describe your sleep quality?', choices: ['Very good', 'Good', 'Fair', 'Poor', 'Very poor'] },
  { key: 'stress_level', label: 'How would you rate your current stress level?', choices: ['Very low', 'Low', 'Moderate', 'High', 'Very high'] },
  { key: 'physical_activity', label: 'How often do you engage in physical activity for at least 30 minutes?', choices: ['Never', '1–2 days per week', '3–4 days per week', '5 or more days per week'] },
  { key: 'tobacco_use', label: 'Do you currently use tobacco or nicotine products?', choices: ['No', 'Occasionally', 'Daily', 'Prefer not to say'] },
  { key: 'alcohol_frequency', label: 'How often do you consume alcohol?', choices: ['Never', 'Less than once a month', '1–3 times a month', '1–2 times a week', '3 or more times a week', 'Prefer not to say'] },
  { key: 'emotional_support', label: 'How often do you feel you have someone you can turn to for emotional support?', choices: ['Always', 'Often', 'Sometimes', 'Rarely', 'Never', 'Prefer not to say'] },
];

function ScoredQuestion({ number, question, value, onChange, disabled }) {
  const groupName = `screening-answer-${number}`;
  return (
    <fieldset className="assessment-question">
      <legend>{number}. {question}</legend>
      <div className="assessment-options">
        {scoredChoices.map(({ label, score }) => (
          <label className="assessment-option" key={score}>
            <input
              type="radio"
              name={groupName}
              value={score}
              checked={value === score}
              onChange={() => onChange(score)}
              disabled={disabled}
              required
            />
            <span>{label}</span>
          </label>
        ))}
      </div>
    </fieldset>
  );
}

export default function DepressionAssessment() {
  const [phq9Responses, setPhq9Responses] = useState(() => Array(9).fill(null));
  const [gad7Responses, setGad7Responses] = useState(() => Array(7).fill(null));
  const [contextAnswers, setContextAnswers] = useState({});
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState('');
  const [submitted, setSubmitted] = useState(false);
  const [showSafetyGuidance, setShowSafetyGuidance] = useState(false);
  const requestInFlight = useRef(false);

  const isComplete =
    phq9Responses.every((answer) => Number.isInteger(answer) && answer >= 0 && answer <= 3) &&
    gad7Responses.every((answer) => Number.isInteger(answer) && answer >= 0 && answer <= 3) &&
    contextQuestions.every(({ key, choices }) => choices.includes(contextAnswers[key]));

  function updateResponse(setter, index, score) {
    setter((previous) => previous.map((answer, item) => item === index ? score : answer));
    setError('');
    setSubmitted(false);
    setShowSafetyGuidance(false);
  }

  function updateContext(key, answer) {
    setContextAnswers((previous) => ({ ...previous, [key]: answer }));
    setError('');
    setSubmitted(false);
    setShowSafetyGuidance(false);
  }

  async function handleSubmit(event) {
    event.preventDefault();
    if (!isComplete || requestInFlight.current) return;

    requestInFlight.current = true;
    setIsSubmitting(true);
    setError('');
    setSubmitted(false);
    try {
      const response = await fetch('/api/depression/submit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phq9_responses: phq9Responses, gad7_responses: gad7Responses, context_answers: contextAnswers }),
      });
      if (!response.ok) {
        setError(response.status === 422
          ? 'Some answers could not be validated. Please review the questions and try again.'
          : 'We couldn’t submit your answers. Please try again in a moment.');
        return;
      }
      setSubmitted(true);
      setShowSafetyGuidance(phq9Responses[8] > 0);
    } catch {
      setError('We couldn’t reach the assessment service. Please try again in a moment.');
    } finally {
      requestInFlight.current = false;
      setIsSubmitting(false);
    }
  }

  let questionNumber = 0;
  return (
    <main className="assessment-page container">
      <header className="assessment-heading">
        <p className="eyebrow">A THOUGHTFUL SPACE TO CHECK IN</p>
        <h1>Depression Screening</h1>
        <p>This is a screening tool, not a diagnosis.</p>
      </header>

      <form className="assessment-form" onSubmit={handleSubmit}>
        {phq9Questions.map((question, index) => {
          questionNumber += 1;
          return (
            <ScoredQuestion
              key={`item-${questionNumber}`}
              number={questionNumber}
              question={question}
              value={phq9Responses[index]}
              onChange={(score) => updateResponse(setPhq9Responses, index, score)}
              disabled={isSubmitting}
            />
          );
        })}
        {gad7Questions.map((question, index) => {
          questionNumber += 1;
          return (
            <ScoredQuestion
              key={`item-${questionNumber}`}
              number={questionNumber}
              question={question}
              value={gad7Responses[index]}
              onChange={(score) => updateResponse(setGad7Responses, index, score)}
              disabled={isSubmitting}
            />
          );
        })}

        {contextQuestions.map(({ key, label, choices }) => {
          questionNumber += 1;
          return (
            <div className="assessment-context" key={key}>
              <label htmlFor={`context-${key}`}>{questionNumber}. {label}</label>
              <select
                id={`context-${key}`}
                value={contextAnswers[key] ?? ''}
                onChange={(event) => updateContext(key, event.target.value)}
                disabled={isSubmitting}
                required
              >
                <option value="" disabled>Select an answer</option>
                {choices.map((choice) => <option key={choice} value={choice}>{choice}</option>)}
              </select>
            </div>
          );
        })}

        <div className="assessment-submit-row">
          <button className="button button--primary" type="submit" disabled={!isComplete || isSubmitting || submitted}>
            {isSubmitting ? 'Submitting…' : 'Submit assessment'}
          </button>
          <span className="assessment-submit-note">Your answers are used for this assessment only.</span>
        </div>
      </form>

      {error && <p className="assessment-message assessment-message--error" role="alert">{error}</p>}
      {submitted && <p className="assessment-message assessment-message--success" role="status">Your responses were received.</p>}
      {submitted && showSafetyGuidance && (
        <aside className="assessment-message assessment-message--safety" role="alert">
          <h2>Support is available</h2>
          <p>You do not have to manage difficult thoughts on your own. If you might act on thoughts of harming yourself or cannot stay safe, call <a href="tel:112">112 in India</a> or go to the nearest hospital now.</p>
          <p>For free, 24/7 mental-health support in India, contact Tele-MANAS at <a href="tel:14416">14416</a> or <a href="tel:18008914416">1-800-891-4416</a>. You may also reach out to someone you trust or a mental-health professional.</p>
        </aside>
      )}
    </main>
  );
}
