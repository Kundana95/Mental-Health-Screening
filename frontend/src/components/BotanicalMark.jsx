export default function BotanicalMark({ small = false }) {
  return (
    <svg
      aria-hidden="true"
      className={small ? 'botanical-mark botanical-mark--small' : 'botanical-mark'}
      viewBox="0 0 40 40"
      fill="none"
    >
      <path d="M11 31c2-9 7-15 17-21" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
      <path d="M13 24c-6 1-9-2-9-7 5-1 9 2 9 7Z" fill="currentColor" opacity=".8" />
      <path d="M21 17c0-6 4-10 10-10 0 6-4 10-10 10Z" fill="currentColor" opacity=".8" />
      <path d="M20 20c5-4 10-3 13 2-4 4-9 4-13-2Z" fill="currentColor" opacity=".58" />
      <path d="M8 33h24" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}
