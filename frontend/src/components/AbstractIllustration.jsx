export default function AbstractIllustration({ tone = 'hero', compact = false }) {
  return (
    <div className={`abstract-art abstract-art--${tone}${compact ? ' abstract-art--compact' : ''}`} aria-hidden="true">
      <svg viewBox="0 0 360 300" role="presentation">
        <circle className="art-ring" cx="214" cy="120" r="76" />
        <circle className="art-ring art-ring--inner" cx="214" cy="120" r="54" />
        <rect className="art-stroke" x="123" y="111" width="83" height="132" rx="42" transform="rotate(25 123 111)" />
        <circle className="art-dot" cx="265" cy="57" r="10" />
        <circle className="art-orbit" cx="92" cy="207" r="31" />
      </svg>
      {!compact && <span className="art-caption">A moment for you. A little more clarity.</span>}
    </div>
  );
}
