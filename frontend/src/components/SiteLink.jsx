import { useCallback } from 'react';

export function Link({ to, className, children, ...props }) {
  const handleClick = useCallback((event) => {
    if (event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    event.preventDefault();
    window.history.pushState({}, '', to);
    window.dispatchEvent(new PopStateEvent('popstate'));
    if (to === '/') window.scrollTo({ top: 0, behavior: 'smooth' });
  }, [to]);

  return <a href={to} className={className} onClick={handleClick} {...props}>{children}</a>;
}
