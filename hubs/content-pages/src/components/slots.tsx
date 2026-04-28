import { useState } from 'react';

// --- Video Slot (CF Stream embed) ---
export function VideoSlot({ streamId, title }: { streamId: string; title: string }) {
  if (!streamId) return <EmptySlot label="Video" />;
  return (
    <div className="slot slot-video">
      <h3>{title}</h3>
      <div className="video-container">
        <iframe
          src={`https://customer-1prkz5571edaq9k9.cloudflarestream.com/${streamId}/iframe`}
          allow="accelerometer; gyroscope; autoplay; encrypted-media; picture-in-picture"
          allowFullScreen
          loading="lazy"
          referrerPolicy="strict-origin-when-cross-origin"
          style={{ border: 'none', width: '100%', aspectRatio: '16/9' }}
        />
      </div>
    </div>
  );
}

// --- Audio Slot ---
export function AudioSlot({ src, title }: { src: string; title: string }) {
  if (!src) return <EmptySlot label="Audio" />;
  return (
    <div className="slot slot-audio">
      <h3>{title}</h3>
      <audio controls preload="metadata" style={{ width: '100%' }}>
        <source src={src} type={src.endsWith('.m4a') ? 'audio/mp4' : 'audio/mpeg'} />
      </audio>
    </div>
  );
}

// --- Slides Slot ---
export function SlidesSlot({ src, title }: { src: string; title: string }) {
  if (!src) return <EmptySlot label="Slides" />;
  const isPdf = src.endsWith('.pdf');
  return (
    <div className="slot slot-slides">
      <h3>{title}</h3>
      {isPdf ? (
        <iframe src={src} loading="lazy" title={title} style={{ width: '100%', height: '500px', border: 'none' }} />
      ) : (
        <a href={src} className="download-link" download>Download Slide Deck</a>
      )}
    </div>
  );
}

// --- Report Slot (rendered HTML from markdown) ---
export function ReportSlot({ html, title }: { html: string; title: string }) {
  if (!html) return <EmptySlot label="Report" />;
  return (
    <div className="slot slot-report">
      <h3>{title}</h3>
      <div className="report-content" dangerouslySetInnerHTML={{ __html: html }} />
    </div>
  );
}

// --- Infographic Slot ---
export function InfographicSlot({ src, title }: { src: string; title: string }) {
  if (!src) return <EmptySlot label="Infographic" />;
  return (
    <div className="slot slot-infographic">
      <h3>{title}</h3>
      <img src={src} alt={title} loading="lazy" decoding="async" style={{ maxWidth: '100%', height: 'auto' }} />
    </div>
  );
}

// --- Quiz Slot ---
interface QuizQuestion {
  question: string;
  options: string[];
  correct: number;
  explanation?: string;
}

export function QuizSlot({ questions, title }: { questions: QuizQuestion[]; title: string }) {
  const [current, setCurrent] = useState(0);
  const [selected, setSelected] = useState<number | null>(null);
  const [score, setScore] = useState(0);
  const [done, setDone] = useState(false);

  if (!questions || questions.length === 0) return <EmptySlot label="Quiz" />;

  const q = questions[current];

  function handleAnswer(idx: number) {
    if (selected !== null) return;
    setSelected(idx);
    if (idx === q.correct) setScore(s => s + 1);
  }

  function next() {
    if (current + 1 >= questions.length) {
      setDone(true);
    } else {
      setCurrent(c => c + 1);
      setSelected(null);
    }
  }

  if (done) {
    return (
      <div className="slot slot-quiz">
        <h3>{title}</h3>
        <div className="quiz-result">Score: {score} / {questions.length}</div>
      </div>
    );
  }

  return (
    <div className="slot slot-quiz">
      <h3>{title}</h3>
      <div className="quiz-progress">{current + 1} of {questions.length}</div>
      <p className="quiz-question">{q.question}</p>
      <div className="quiz-options">
        {q.options.map((opt, i) => (
          <button
            key={i}
            onClick={() => handleAnswer(i)}
            className={`quiz-option ${selected === i ? (i === q.correct ? 'correct' : 'wrong') : ''} ${selected !== null && i === q.correct ? 'correct' : ''}`}
            disabled={selected !== null}
          >
            {opt}
          </button>
        ))}
      </div>
      {selected !== null && q.explanation && <p className="quiz-explanation">{q.explanation}</p>}
      {selected !== null && <button onClick={next} className="quiz-next">Next</button>}
    </div>
  );
}

// --- Flashcards Slot ---
interface Flashcard {
  front: string;
  back: string;
}

export function FlashcardsSlot({ cards, title }: { cards: Flashcard[]; title: string }) {
  const [current, setCurrent] = useState(0);
  const [flipped, setFlipped] = useState(false);

  if (!cards || cards.length === 0) return <EmptySlot label="Flashcards" />;

  return (
    <div className="slot slot-flashcards">
      <h3>{title}</h3>
      <div className="flashcard-progress">{current + 1} of {cards.length}</div>
      <div className={`flashcard ${flipped ? 'flipped' : ''}`} onClick={() => setFlipped(!flipped)}>
        <div className="flashcard-face front">{cards[current].front}</div>
        <div className="flashcard-face back">{cards[current].back}</div>
      </div>
      <div className="flashcard-nav">
        <button onClick={() => { setCurrent(c => Math.max(0, c - 1)); setFlipped(false); }} disabled={current === 0}>Prev</button>
        <button onClick={() => { setCurrent(c => Math.min(cards.length - 1, c + 1)); setFlipped(false); }} disabled={current === cards.length - 1}>Next</button>
      </div>
    </div>
  );
}

// --- Mind Map Slot ---
export function MindMapSlot({ src, title }: { src: string; title: string }) {
  if (!src) return <EmptySlot label="Mind Map" />;
  return (
    <div className="slot slot-mindmap">
      <h3>{title}</h3>
      <img src={src} alt={title} loading="lazy" decoding="async" style={{ maxWidth: '100%', height: 'auto' }} />
    </div>
  );
}

// --- Data Table Slot ---
interface TableData {
  headers: string[];
  rows: string[][];
}

export function DataTableSlot({ data, title }: { data: TableData; title: string }) {
  if (!data || !data.headers) return <EmptySlot label="Data Table" />;
  return (
    <div className="slot slot-datatable">
      <h3>{title}</h3>
      <div className="table-wrapper">
        <table>
          <thead>
            <tr>{data.headers.map((h, i) => <th key={i}>{h}</th>)}</tr>
          </thead>
          <tbody>
            {data.rows.map((row, i) => (
              <tr key={i}>{row.map((cell, j) => <td key={j}>{cell}</td>)}</tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

// --- Empty Slot (placeholder) ---
function EmptySlot({ label }: { label: string }) {
  return (
    <div className="slot slot-empty">
      <span>{label} - not yet available</span>
    </div>
  );
}
